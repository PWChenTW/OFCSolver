"""
Distributed Cache Implementation for OFC Solver System.

Handles cache distribution across multiple Redis instances
for scalability and high availability.
"""

from typing import List, Dict, Optional, Any, Tuple
import hashlib
import logging
from dataclasses import dataclass
from enum import Enum
import random
from datetime import timedelta

from .redis_cache import RedisCache
from .cache_manager import CacheManager, CacheKeyBuilder

logger = logging.getLogger(__name__)


class ShardingStrategy(Enum):
    """Cache sharding strategies."""
    CONSISTENT_HASH = "consistent_hash"
    MODULO = "modulo"
    RANGE = "range"
    RANDOM = "random"


class ReplicationMode(Enum):
    """Cache replication modes."""
    NONE = "none"
    MASTER_SLAVE = "master_slave"
    MULTI_MASTER = "multi_master"


@dataclass
class CacheNode:
    """Represents a cache node in the cluster."""
    node_id: str
    host: str
    port: int
    weight: int = 1  # For weighted distribution
    is_master: bool = True
    is_healthy: bool = True
    redis_cache: Optional[RedisCache] = None


class ConsistentHash:
    """
    Consistent hashing implementation for cache distribution.
    
    Provides better distribution and minimal remapping when nodes
    are added or removed.
    """
    
    def __init__(self, nodes: List[CacheNode], virtual_nodes: int = 150):
        """Initialize consistent hash ring."""
        self.nodes = nodes
        self.virtual_nodes = virtual_nodes
        self.ring: Dict[int, CacheNode] = {}
        self.sorted_keys: List[int] = []
        self._build_ring()
    
    def _build_ring(self) -> None:
        """Build the hash ring with virtual nodes."""
        self.ring.clear()
        
        for node in self.nodes:
            if not node.is_healthy:
                continue
                
            # Create virtual nodes based on weight
            num_virtual = self.virtual_nodes * node.weight
            
            for i in range(num_virtual):
                virtual_key = f"{node.node_id}:{i}"
                hash_value = self._hash(virtual_key)
                self.ring[hash_value] = node
        
        self.sorted_keys = sorted(self.ring.keys())
    
    def _hash(self, key: str) -> int:
        """Generate hash value for a key."""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
    
    def get_node(self, key: str) -> Optional[CacheNode]:
        """Get the node responsible for a key."""
        if not self.sorted_keys:
            return None
        
        hash_value = self._hash(key)
        
        # Find the first node with hash >= key hash
        for node_hash in self.sorted_keys:
            if hash_value <= node_hash:
                return self.ring[node_hash]
        
        # Wrap around to first node
        return self.ring[self.sorted_keys[0]]
    
    def add_node(self, node: CacheNode) -> None:
        """Add a node to the ring."""
        self.nodes.append(node)
        self._build_ring()
    
    def remove_node(self, node_id: str) -> None:
        """Remove a node from the ring."""
        self.nodes = [n for n in self.nodes if n.node_id != node_id]
        self._build_ring()
    
    def mark_unhealthy(self, node_id: str) -> None:
        """Mark a node as unhealthy."""
        for node in self.nodes:
            if node.node_id == node_id:
                node.is_healthy = False
                break
        self._build_ring()


class DistributedCacheManager:
    """
    Manages distributed caching across multiple Redis nodes.
    
    Features:
    - Multiple sharding strategies
    - Replication support
    - Automatic failover
    - Load balancing
    """
    
    def __init__(
        self,
        nodes: List[Dict[str, Any]],
        sharding_strategy: ShardingStrategy = ShardingStrategy.CONSISTENT_HASH,
        replication_mode: ReplicationMode = ReplicationMode.NONE,
        read_preference: str = "primary"  # primary, primary_preferred, nearest
    ):
        """Initialize distributed cache manager."""
        self.sharding_strategy = sharding_strategy
        self.replication_mode = replication_mode
        self.read_preference = read_preference
        
        # Initialize nodes
        self.nodes: List[CacheNode] = []
        self._init_nodes(nodes)
        
        # Initialize sharding
        if sharding_strategy == ShardingStrategy.CONSISTENT_HASH:
            self.hasher = ConsistentHash(self.nodes)
        
        # Statistics
        self.stats = {
            "reads": {},
            "writes": {},
            "failures": {}
        }
        
        # Initialize key builder
        self.key_builder = CacheKeyBuilder()
    
    def _init_nodes(self, node_configs: List[Dict[str, Any]]) -> None:
        """Initialize cache nodes from configuration."""
        for config in node_configs:
            node = CacheNode(
                node_id=config["id"],
                host=config["host"],
                port=config["port"],
                weight=config.get("weight", 1),
                is_master=config.get("is_master", True)
            )
            
            # Create Redis connection
            try:
                node.redis_cache = RedisCache(
                    host=node.host,
                    port=node.port,
                    max_connections=config.get("max_connections", 50)
                )
                # Test connection
                if node.redis_cache.ping():
                    node.is_healthy = True
                else:
                    node.is_healthy = False
                    logger.warning(f"Node {node.node_id} is not responding")
            except Exception as e:
                logger.error(f"Failed to connect to node {node.node_id}: {e}")
                node.is_healthy = False
            
            self.nodes.append(node)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from distributed cache.
        
        Handles node selection based on sharding strategy
        and read preferences.
        """
        node = self._select_read_node(key)
        if not node or not node.redis_cache:
            return None
        
        try:
            value = node.redis_cache.get(key)
            self._record_operation("reads", node.node_id, True)
            return value
        except Exception as e:
            logger.error(f"Failed to get key {key} from node {node.node_id}: {e}")
            self._record_operation("reads", node.node_id, False)
            self._handle_node_failure(node)
            
            # Try failover
            return self._failover_get(key, exclude_node=node)
    
    def set(
        self,
        key: str,
        value: Any,
        expire: Optional[timedelta] = None,
        replicate: bool = True
    ) -> bool:
        """
        Set value in distributed cache.
        
        Handles replication based on configured mode.
        """
        primary_node = self._select_write_node(key)
        if not primary_node or not primary_node.redis_cache:
            return False
        
        try:
            # Write to primary
            result = primary_node.redis_cache.set(key, value, expire=expire)
            self._record_operation("writes", primary_node.node_id, True)
            
            # Handle replication
            if replicate and self.replication_mode != ReplicationMode.NONE:
                self._replicate_write(key, value, expire, primary_node)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to set key {key} on node {primary_node.node_id}: {e}")
            self._record_operation("writes", primary_node.node_id, False)
            self._handle_node_failure(primary_node)
            return False
    
    def delete(self, *keys: str) -> int:
        """Delete keys from distributed cache."""
        if not keys:
            return 0
        
        # Group keys by node
        keys_by_node: Dict[CacheNode, List[str]] = {}
        for key in keys:
            node = self._select_write_node(key)
            if node and node.redis_cache:
                if node not in keys_by_node:
                    keys_by_node[node] = []
                keys_by_node[node].append(key)
        
        # Delete from each node
        total_deleted = 0
        for node, node_keys in keys_by_node.items():
            try:
                deleted = node.redis_cache.delete(*node_keys)
                total_deleted += deleted
                
                # Replicate deletes
                if self.replication_mode != ReplicationMode.NONE:
                    self._replicate_delete(node_keys, node)
                    
            except Exception as e:
                logger.error(f"Failed to delete keys from node {node.node_id}: {e}")
                self._handle_node_failure(node)
        
        return total_deleted
    
    def _select_read_node(self, key: str) -> Optional[CacheNode]:
        """Select node for read operation based on strategy and preference."""
        if self.sharding_strategy == ShardingStrategy.CONSISTENT_HASH:
            primary = self.hasher.get_node(key)
            
            if self.read_preference == "primary":
                return primary
            elif self.read_preference == "nearest":
                # In production, would consider network latency
                # For now, just return a random healthy node
                healthy_nodes = [n for n in self.nodes if n.is_healthy]
                return random.choice(healthy_nodes) if healthy_nodes else None
            else:  # primary_preferred
                if primary and primary.is_healthy:
                    return primary
                else:
                    # Fallback to any healthy node
                    healthy_nodes = [n for n in self.nodes if n.is_healthy]
                    return random.choice(healthy_nodes) if healthy_nodes else None
                    
        elif self.sharding_strategy == ShardingStrategy.MODULO:
            # Simple modulo sharding
            hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
            healthy_nodes = [n for n in self.nodes if n.is_healthy]
            if not healthy_nodes:
                return None
            index = hash_value % len(healthy_nodes)
            return healthy_nodes[index]
            
        elif self.sharding_strategy == ShardingStrategy.RANDOM:
            healthy_nodes = [n for n in self.nodes if n.is_healthy]
            return random.choice(healthy_nodes) if healthy_nodes else None
            
        return None
    
    def _select_write_node(self, key: str) -> Optional[CacheNode]:
        """Select node for write operation."""
        if self.sharding_strategy == ShardingStrategy.CONSISTENT_HASH:
            return self.hasher.get_node(key)
        else:
            # For other strategies, use same logic as read
            return self._select_read_node(key)
    
    def _replicate_write(
        self,
        key: str,
        value: Any,
        expire: Optional[timedelta],
        primary_node: CacheNode
    ) -> None:
        """Replicate write to secondary nodes."""
        if self.replication_mode == ReplicationMode.MASTER_SLAVE:
            # Replicate to all slaves
            slaves = [n for n in self.nodes 
                     if n != primary_node and not n.is_master and n.is_healthy]
            
            for slave in slaves:
                try:
                    if slave.redis_cache:
                        slave.redis_cache.set(key, value, expire=expire)
                except Exception as e:
                    logger.error(f"Failed to replicate to slave {slave.node_id}: {e}")
                    
        elif self.replication_mode == ReplicationMode.MULTI_MASTER:
            # Replicate to all other masters
            other_masters = [n for n in self.nodes 
                           if n != primary_node and n.is_master and n.is_healthy]
            
            for master in other_masters[:2]:  # Limit replication factor
                try:
                    if master.redis_cache:
                        master.redis_cache.set(key, value, expire=expire)
                except Exception as e:
                    logger.error(f"Failed to replicate to master {master.node_id}: {e}")
    
    def _replicate_delete(self, keys: List[str], primary_node: CacheNode) -> None:
        """Replicate delete operations."""
        replica_nodes = []
        
        if self.replication_mode == ReplicationMode.MASTER_SLAVE:
            replica_nodes = [n for n in self.nodes 
                           if n != primary_node and not n.is_master and n.is_healthy]
        elif self.replication_mode == ReplicationMode.MULTI_MASTER:
            replica_nodes = [n for n in self.nodes 
                           if n != primary_node and n.is_master and n.is_healthy]
        
        for node in replica_nodes:
            try:
                if node.redis_cache:
                    node.redis_cache.delete(*keys)
            except Exception as e:
                logger.error(f"Failed to replicate delete to {node.node_id}: {e}")
    
    def _failover_get(self, key: str, exclude_node: CacheNode) -> Optional[Any]:
        """Try to get value from failover nodes."""
        # Try other nodes based on replication mode
        if self.replication_mode == ReplicationMode.NONE:
            return None
        
        # Get potential failover nodes
        failover_nodes = [n for n in self.nodes 
                         if n != exclude_node and n.is_healthy]
        
        for node in failover_nodes:
            try:
                if node.redis_cache:
                    value = node.redis_cache.get(key)
                    if value is not None:
                        logger.info(f"Failover read succeeded from node {node.node_id}")
                        return value
            except Exception as e:
                logger.error(f"Failover read failed from node {node.node_id}: {e}")
                continue
        
        return None
    
    def _handle_node_failure(self, node: CacheNode) -> None:
        """Handle node failure."""
        logger.warning(f"Node {node.node_id} marked as unhealthy")
        node.is_healthy = False
        
        if self.sharding_strategy == ShardingStrategy.CONSISTENT_HASH:
            self.hasher.mark_unhealthy(node.node_id)
        
        # Record failure
        if node.node_id not in self.stats["failures"]:
            self.stats["failures"][node.node_id] = 0
        self.stats["failures"][node.node_id] += 1
    
    def _record_operation(self, op_type: str, node_id: str, success: bool) -> None:
        """Record operation statistics."""
        if node_id not in self.stats[op_type]:
            self.stats[op_type][node_id] = {"success": 0, "failure": 0}
        
        if success:
            self.stats[op_type][node_id]["success"] += 1
        else:
            self.stats[op_type][node_id]["failure"] += 1
    
    def rebalance(self) -> Dict[str, Any]:
        """
        Rebalance cache distribution (placeholder).
        
        In production, would migrate keys between nodes
        to achieve better distribution.
        """
        return {
            "status": "rebalancing_not_implemented",
            "nodes": len(self.nodes),
            "healthy_nodes": len([n for n in self.nodes if n.is_healthy])
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of all nodes."""
        results = {
            "healthy_nodes": 0,
            "unhealthy_nodes": 0,
            "nodes": {}
        }
        
        for node in self.nodes:
            try:
                if node.redis_cache and node.redis_cache.ping():
                    node.is_healthy = True
                    results["healthy_nodes"] += 1
                    results["nodes"][node.node_id] = "healthy"
                else:
                    node.is_healthy = False
                    results["unhealthy_nodes"] += 1
                    results["nodes"][node.node_id] = "unhealthy"
            except Exception as e:
                node.is_healthy = False
                results["unhealthy_nodes"] += 1
                results["nodes"][node.node_id] = f"error: {str(e)}"
        
        # Rebuild hash ring if using consistent hashing
        if self.sharding_strategy == ShardingStrategy.CONSISTENT_HASH:
            self.hasher._build_ring()
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get distribution statistics."""
        total_reads = sum(
            stats["success"] + stats["failure"] 
            for stats in self.stats["reads"].values()
        )
        total_writes = sum(
            stats["success"] + stats["failure"] 
            for stats in self.stats["writes"].values()
        )
        
        return {
            "total_reads": total_reads,
            "total_writes": total_writes,
            "node_stats": self.stats,
            "healthy_nodes": len([n for n in self.nodes if n.is_healthy]),
            "total_nodes": len(self.nodes),
            "sharding_strategy": self.sharding_strategy.value,
            "replication_mode": self.replication_mode.value
        }
    
    def shutdown(self) -> None:
        """Shutdown all cache connections."""
        for node in self.nodes:
            if node.redis_cache:
                try:
                    node.redis_cache.close()
                except Exception as e:
                    logger.error(f"Error closing node {node.node_id}: {e}")
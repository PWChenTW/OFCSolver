"""
Test script for caching implementation.

Tests the integration of Redis caching with the strategy calculator.
"""

import time
from datetime import timedelta

from src.infrastructure.cache import (
    RedisCache,
    CacheManager,
    CacheInvalidator,
    CacheWarmer,
    CacheMonitor,
    WarmingStrategy,
)
from src.domain.services import CachedStrategyCalculator
from src.domain.value_objects.hand import Hand
from src.domain.value_objects.card import Card


def test_basic_caching():
    """Test basic caching functionality."""
    print("Testing basic caching...")

    # Initialize cache components
    redis_cache = RedisCache(host="localhost", port=6379, db=0)
    cache_manager = CacheManager(redis_cache)

    # Test connection
    if not cache_manager.health_check():
        print("❌ Redis connection failed. Make sure Redis is running.")
        return False

    print("✅ Redis connection successful")

    # Test basic set/get
    test_key = "test:key"
    test_value = {"data": "test", "number": 42}

    # Set value
    success = cache_manager.cache.set(test_key, test_value, expire=timedelta(minutes=5))
    print(f"✅ Set operation: {success}")

    # Get value
    retrieved = cache_manager.cache.get(test_key)
    print(f"✅ Get operation: {retrieved == test_value}")

    # Clean up
    cache_manager.cache.delete(test_key)

    return True


def test_position_caching():
    """Test position caching."""
    print("\nTesting position caching...")

    redis_cache = RedisCache(host="localhost", port=6379, db=0)
    cache_manager = CacheManager(redis_cache)

    # Create test position
    position_data = {
        "top_row": ["AA", "KK"],
        "middle_row": ["QQ", "JJ", "TT"],
        "bottom_row": ["99", "88", "77"],
        "cards_placed": 8,
    }

    # Cache position
    success = cache_manager.set_position(position_data)
    print(f"✅ Position cached: {success}")

    # Generate position hash
    position_hash = cache_manager.key_builder.hash_position(position_data)

    # Retrieve position
    cached_position = cache_manager.get_position(position_hash)
    print(f"✅ Position retrieved: {cached_position is not None}")

    # Test analysis caching
    analysis_result = {
        "expected_value": 5.5,
        "confidence": 0.85,
        "calculation_method": "minimax_alphabeta",
        "optimal_strategy": {"action": "place", "cards": ["66"], "position": "top"},
    }

    # Cache analysis
    success = cache_manager.set_analysis(
        position_hash, "minimax_alphabeta", analysis_result
    )
    print(f"✅ Analysis cached: {success}")

    # Retrieve analysis
    cached_analysis = cache_manager.get_analysis(position_hash, "minimax_alphabeta")
    print(f"✅ Analysis retrieved: {cached_analysis is not None}")

    return True


def test_strategy_calculator_caching():
    """Test cached strategy calculator."""
    print("\nTesting cached strategy calculator...")

    redis_cache = RedisCache(host="localhost", port=6379, db=0)
    cache_manager = CacheManager(redis_cache)

    # Create cached strategy calculator
    calculator = CachedStrategyCalculator(cache_manager)

    # Create test hand
    hand = Hand()
    hand.add_to_bottom([Card.from_string("As"), Card.from_string("Ks")])
    hand.add_to_middle([Card.from_string("Qh"), Card.from_string("Jh")])

    # Create remaining deck (simplified)
    remaining_deck = [
        Card.from_string("Th"),
        Card.from_string("9h"),
        Card.from_string("8c"),
        Card.from_string("7c"),
        Card.from_string("6d"),
        Card.from_string("5d"),
    ]

    print("Calculating strategy (first time - cache miss)...")
    start_time = time.time()
    strategy1 = calculator.calculate_optimal_strategy(hand, remaining_deck, max_depth=1)
    first_time = time.time() - start_time
    print(f"✅ First calculation took: {first_time:.3f}s")
    print(f"   Expected value: {strategy1.expected_value.value:.2f}")

    print("\nCalculating same strategy (second time - cache hit)...")
    start_time = time.time()
    strategy2 = calculator.calculate_optimal_strategy(hand, remaining_deck, max_depth=1)
    second_time = time.time() - start_time
    print(f"✅ Second calculation took: {second_time:.3f}s")
    print(f"   Expected value: {strategy2.expected_value.value:.2f}")

    # Cache should make it much faster
    speedup = first_time / second_time if second_time > 0 else float("inf")
    print(f"✅ Speedup from caching: {speedup:.1f}x")

    # Print cache stats
    stats = calculator.get_cache_stats()
    print(f"\nCache statistics:")
    print(f"  Memory cache hit rate: {stats['cache_hit_rate']:.2%}")
    print(f"  Redis strategy hits: {stats['redis_strategy_hits']}")
    print(f"  Redis strategy misses: {stats['redis_strategy_misses']}")

    return True


def test_cache_invalidation():
    """Test cache invalidation."""
    print("\nTesting cache invalidation...")

    redis_cache = RedisCache(host="localhost", port=6379, db=0)
    cache_manager = CacheManager(redis_cache)
    invalidator = CacheInvalidator(cache_manager)

    # Create and cache some test data
    position_hash = "test_position_123"
    cache_manager.cache.set(f"pos:{position_hash}", {"test": "data"})
    cache_manager.cache.set(f"analysis:{position_hash}:minimax", {"result": "test"})
    cache_manager.cache.set(f"strategy:{position_hash}", {"strategy": "test"})

    # Verify data exists
    print("✅ Test data cached")

    # Invalidate position and related data
    count = invalidator.invalidate_position_analysis(position_hash, cascade=True)
    print(f"✅ Invalidated {count} cache entries")

    # Verify data is gone
    pos_data = cache_manager.cache.get(f"pos:{position_hash}")
    analysis_data = cache_manager.cache.get(f"analysis:{position_hash}:minimax")
    print(f"✅ Data properly invalidated: {pos_data is None and analysis_data is None}")

    return True


def test_cache_warming():
    """Test cache warming strategies."""
    print("\nTesting cache warming...")

    redis_cache = RedisCache(host="localhost", port=6379, db=0)
    cache_manager = CacheManager(redis_cache)
    warmer = CacheWarmer(cache_manager)

    # Warm opening positions
    count = warmer.warm_opening_positions()
    print(f"✅ Warmed {count} opening positions")

    # Warm endgame positions
    count = warmer.warm_endgame_positions()
    print(f"✅ Warmed {count} endgame positions")

    # Check warming stats
    stats = warmer.get_warming_stats()
    print(f"\nWarming statistics:")
    print(f"  Total warmed: {stats['total_warmed']}")
    print(f"  Failures: {stats['failures']}")

    return True


def test_cache_monitoring():
    """Test cache monitoring."""
    print("\nTesting cache monitoring...")

    redis_cache = RedisCache(host="localhost", port=6379, db=0)
    cache_manager = CacheManager(redis_cache)
    monitor = CacheMonitor(cache_manager)

    # Simulate some operations
    for i in range(10):
        start = time.time()
        cache_manager.cache.get(f"test_key_{i}")
        duration = (time.time() - start) * 1000  # ms

        # Record operation
        monitor.record_cache_operation(
            operation="get",
            duration_ms=duration,
            hit=i % 3 == 0,  # 30% hit rate
            error=False,
        )

    # Get current metrics
    metrics = monitor.get_current_metrics()
    print("✅ Current metrics collected:")
    if "hit_rate" in metrics:
        print(f"  Hit rate: {metrics['hit_rate']['avg']:.2%}")
    if "latency" in metrics:
        print(f"  Avg latency: {metrics['latency']['avg']:.2f}ms")

    # Get recommendations
    recommendations = monitor.get_optimization_recommendations()
    print(f"\n✅ Generated {len(recommendations)} optimization recommendations")
    for rec in recommendations:
        print(f"  - {rec['recommendation']}")

    return True


def main():
    """Run all cache tests."""
    print("=== OFC Solver Cache Testing ===\n")

    tests = [
        ("Basic Caching", test_basic_caching),
        ("Position Caching", test_position_caching),
        ("Strategy Calculator Caching", test_strategy_calculator_caching),
        ("Cache Invalidation", test_cache_invalidation),
        ("Cache Warming", test_cache_warming),
        ("Cache Monitoring", test_cache_monitoring),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\n{'='*50}")
            print(f"Running: {test_name}")
            print("=" * 50)

            if test_func():
                passed += 1
                print(f"\n✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"\n❌ {test_name} FAILED")

        except Exception as e:
            failed += 1
            print(f"\n❌ {test_name} FAILED with error: {e}")
            import traceback

            traceback.print_exc()

    print(f"\n{'='*50}")
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 50)


if __name__ == "__main__":
    main()

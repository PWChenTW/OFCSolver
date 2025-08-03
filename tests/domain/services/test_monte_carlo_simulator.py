"""Unit tests for Monte Carlo Simulator Service."""

from unittest.mock import Mock

import pytest

from src.domain.services.hand_evaluator import HandEvaluator
from src.domain.services.monte_carlo_simulator import MCTSConfig, MonteCarloSimulator


class TestMonteCarloSimulator:
    """Test cases for Monte Carlo Tree Search simulator."""

    @pytest.fixture
    def hand_evaluator(self):
        """Create hand evaluator."""
        return HandEvaluator()

    @pytest.fixture
    def basic_config(self):
        """Create basic MCTS configuration."""
        return MCTSConfig(
            num_simulations=10,  # Very small for testing
            timeout_ms=1000,
            batch_size=2,
        )

    @pytest.fixture
    def simulator(self, hand_evaluator, basic_config):
        """Create Monte Carlo simulator."""
        return MonteCarloSimulator(hand_evaluator, basic_config)

    def test_simulator_initialization(self, hand_evaluator):
        """Test simulator can be initialized."""
        simulator = MonteCarloSimulator(hand_evaluator)
        assert simulator is not None
        assert simulator._hand_evaluator == hand_evaluator
        assert simulator._config.num_simulations == 10000  # default

    def test_custom_config(self, hand_evaluator):
        """Test simulator with custom configuration."""
        config = MCTSConfig(
            num_simulations=500,
            exploration_constant=1.0,
            timeout_ms=5000,
        )
        simulator = MonteCarloSimulator(hand_evaluator, config)
        assert simulator._config.num_simulations == 500
        assert simulator._config.exploration_constant == 1.0
        assert simulator._config.timeout_ms == 5000

    def test_ucb1_calculation(self, simulator):
        """Test UCB1 value calculation."""
        # Create mock nodes
        child_node = Mock()
        child_node.statistics = Mock()
        child_node.statistics.visit_count = 10
        child_node.statistics.average_value = 0.5

        parent_visits = 100

        ucb_value = simulator._calculate_ucb1_value(child_node, parent_visits)

        # UCB1 should be average_value + exploration_bonus
        assert ucb_value > 0.5  # Should include exploration bonus
        assert ucb_value < 2.0  # Reasonable upper bound

    def test_select_best_move(self, simulator):
        """Test best move selection."""
        # Create mock root with children
        root = Mock()
        child1 = Mock()
        child1.move_to_reach = "move1"
        child1.statistics = Mock()
        child1.statistics.visit_count = 100

        child2 = Mock()
        child2.move_to_reach = "move2"
        child2.statistics = Mock()
        child2.statistics.visit_count = 50

        root.children = [child1, child2]

        best_move = simulator._select_best_move(root)

        # Should select move with highest visit count
        assert best_move == "move1"

    def test_check_convergence(self, simulator):
        """Test convergence checking logic."""
        # Create mock root
        root = Mock()
        root.statistics = Mock()
        root.statistics.visit_count = 200

        child = Mock()
        child.statistics = Mock()
        child.statistics.visit_count = 200
        root.children = [child]

        # Should converge with enough iterations without change
        assert simulator._check_convergence(root, 500) is True

        # Should not converge with few iterations
        assert simulator._check_convergence(root, 10) is False

        # Should not converge if not enough visits
        root.statistics.visit_count = 5
        assert simulator._check_convergence(root, 500) is False

"""
Simple tests that don't require database connection.
"""

import pytest


def test_basic_math():
    """Test basic math operations."""
    assert 2 + 2 == 4
    assert 3 * 3 == 9
    assert 10 / 2 == 5


def test_string_operations():
    """Test string operations."""
    assert "hello".upper() == "HELLO"
    assert "WORLD".lower() == "world"
    assert " test ".strip() == "test"


def test_list_operations():
    """Test list operations."""
    test_list = [1, 2, 3, 4, 5]
    assert len(test_list) == 5
    assert sum(test_list) == 15
    assert max(test_list) == 5
    assert min(test_list) == 1


def test_dict_operations():
    """Test dictionary operations."""
    test_dict = {"a": 1, "b": 2, "c": 3}
    assert len(test_dict) == 3
    assert test_dict.get("a") == 1
    assert test_dict.get("d", 0) == 0
    assert list(test_dict.keys()) == ["a", "b", "c"]
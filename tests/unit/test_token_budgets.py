import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from shared.config.token_budgets import token_budget_for, TOKEN_BUDGETS, DEFAULT_TOKEN_BUDGET


def test_known_task_returns_its_specific_budget():
    assert token_budget_for("greeting") == 50
    assert token_budget_for("market_report") == 350


def test_unknown_task_returns_default_budget():
    assert token_budget_for("some_task_that_does_not_exist") == DEFAULT_TOKEN_BUDGET


def test_every_budget_is_a_positive_int():
    for name, value in TOKEN_BUDGETS.items():
        assert isinstance(value, int) and value > 0, name

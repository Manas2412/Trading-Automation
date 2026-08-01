"""Tests for typed configuration and the live-trading guard."""

import pytest

from qtrade.common.config import Settings


def _settings(**env) -> Settings:
    # Ignore any real .env during tests; pass explicit values.
    return Settings(_env_file=None, **env)


def test_defaults_are_safe():
    s = _settings()
    assert s.qtrade_env == "dev"
    assert s.live_trading_enabled is False
    assert s.live_trading_allowed is False


def test_live_requires_both_env_and_flag():
    assert _settings(qtrade_env="live", live_trading_enabled=False).live_trading_allowed is False
    assert _settings(qtrade_env="paper", live_trading_enabled=True).live_trading_allowed is False
    assert _settings(qtrade_env="live", live_trading_enabled=True).live_trading_allowed is True


def test_require_live_raises_when_not_allowed():
    with pytest.raises(RuntimeError):
        _settings(qtrade_env="paper", live_trading_enabled=True).require_live()


def test_require_live_passes_when_allowed():
    # Should not raise.
    _settings(qtrade_env="live", live_trading_enabled=True).require_live()


def test_secret_not_reprd():
    s = _settings(kite_api_secret="supersecret")
    assert "supersecret" not in repr(s)

import pytest

from scripts.seed_data import get_admin_api_key


def test_seed_api_key_only_comes_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PROMPTHUB_SEED_ADMIN_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="PROMPTHUB_SEED_ADMIN_API_KEY"):
        get_admin_api_key()

    monkeypatch.setenv("PROMPTHUB_SEED_ADMIN_API_KEY", "ph-secure-seed-key")
    assert get_admin_api_key() == "ph-secure-seed-key"

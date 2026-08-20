import pandas as pd

from akshare.index import index_option_qvix


def test_daily_cache_refreshes_after_ttl(monkeypatch):
    cache_ttl = index_option_qvix._OPTBBS_DAILY_CACHE_TTL
    now = [cache_ttl * 10 + 1]
    close_values = iter([17.0, 17.62])
    read_count = 0

    def mock_read_csv(*args, **kwargs):
        nonlocal read_count
        read_count += 1
        close = next(close_values)
        return pd.DataFrame(
            [["2026-08-19", 16.0, 18.0, 15.0, close]],
        )

    index_option_qvix.__get_optbbs_daily_cached.cache_clear()
    monkeypatch.setattr(index_option_qvix, "monotonic", lambda: now[0])
    monkeypatch.setattr(index_option_qvix.pd, "read_csv", mock_read_csv)

    first_df = index_option_qvix.index_option_50etf_qvix()
    cached_df = index_option_qvix.index_option_50etf_qvix()

    assert read_count == 1
    assert first_df.loc[0, "close"] == 17.0
    assert cached_df.loc[0, "close"] == 17.0

    now[0] += cache_ttl
    refreshed_df = index_option_qvix.index_option_50etf_qvix()

    assert read_count == 2
    assert refreshed_df.loc[0, "close"] == 17.62

    index_option_qvix.__get_optbbs_daily_cached.cache_clear()

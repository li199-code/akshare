#!/usr/bin/env python
# -*- coding:utf-8 -*-

import pandas as pd

from akshare.index import index_stock_zh


def _xq_items():
    return pd.DataFrame(
        [
            ["代码", "SH000905"],
            ["名称", "中证500"],
            ["现价", 5930.12],
            ["涨幅", 0.51],
            ["涨跌", 30.12],
            ["成交量", 123456],
            ["成交额", 123456789.0],
            ["振幅", 1.02],
            ["最高", 5960.12],
            ["最低", 5900.12],
            ["今开", 5910.12],
            ["昨收", 5900.00],
            ["时间", "2026-06-19 15:00:00"],
        ],
        columns=["item", "value"],
    )


def test_stock_zh_index_spot_tx(monkeypatch):
    class MockResponse:
        text = (
            'v_sh000905="1~中证500~000905~8673.09~8627.09~8590.50~239467579~'
            '0~0~0.00~0~0.00~0~0.00~0~0.00~0~0.00~0~0.00~0~0.00~0~0.00~'
            '0~0.00~0~0.00~0~~20260618161413~46.00~0.53~8716.34~8587.98~'
            '8673.09/239467579/667474010745~239467579~66747401~2.18~'
            '40.55~~8716.34~8587.98~1.49~171540.17~190812.50~";'
        )
        encoding = ""

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(index_stock_zh.requests, "get", mock_get)

    temp_df = index_stock_zh.stock_zh_index_spot_tx(symbol="000905")

    assert temp_df.loc[0, "代码"] == "000905"
    assert temp_df.loc[0, "名称"] == "中证500"
    assert temp_df.loc[0, "最新价"] == 8673.09
    assert temp_df.loc[0, "涨跌幅"] == 0.53
    assert temp_df.loc[0, "数据来源"] == "腾讯-实时行情"


def test_stock_zh_index_spot_xq(monkeypatch):
    def mock_stock_individual_spot_xq(*args, **kwargs):
        return _xq_items()

    monkeypatch.setattr(
        index_stock_zh, "stock_individual_spot_xq", mock_stock_individual_spot_xq
    )

    temp_df = index_stock_zh.stock_zh_index_spot_xq(symbol="000905")

    assert temp_df.loc[0, "代码"] == "000905"
    assert temp_df.loc[0, "名称"] == "中证500"
    assert temp_df.loc[0, "涨跌幅"] == 0.51
    assert temp_df.loc[0, "数据来源"] == "雪球-实时行情"


def test_stock_zh_index_spot_csindex(monkeypatch):
    class MockResponse:
        @staticmethod
        def json():
            return {
                "code": "200",
                "msg": "Success",
                "data": {
                    "intraDayHeader": {
                        "indexCode": "930955",
                        "tradeDate": "2026-06-18",
                        "tradeTime": "16:29:53",
                        "openToday": 11246.19,
                        "closePre": 11275.57,
                        "current": 11046.66,
                        "change": -228.9,
                        "changePct": -2.03,
                        "tradingVol": 6969041773.0,
                        "tradingValue": 677.98,
                    },
                    "intraDayPerfList": [
                        {
                            "indexCode": "930955",
                            "indexName": "红利低波100",
                            "tradeDate": "2026-06-18",
                            "tradeTime": "09:30:12",
                            "current": 11240.06,
                            "high": 11246.19,
                            "low": 11240.06,
                        },
                        {
                            "indexCode": "930955",
                            "indexName": "红利低波100",
                            "tradeDate": "2026-06-18",
                            "tradeTime": "14:55:12",
                            "current": 11046.66,
                            "high": 11246.19,
                            "low": 11030.00,
                        },
                    ],
                    "rangeType": "hs",
                },
                "success": True,
            }

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(index_stock_zh.requests, "get", mock_get)

    temp_df = index_stock_zh.stock_zh_index_spot_csindex(symbol="930955")

    assert temp_df.loc[0, "代码"] == "930955"
    assert temp_df.loc[0, "名称"] == "红利低波100"
    assert temp_df.loc[0, "最新价"] == 11046.66
    assert temp_df.loc[0, "涨跌幅"] == -2.03
    assert temp_df.loc[0, "成交额"] == 67798000000.0
    assert temp_df.loc[0, "数据来源"] == "中证官网-盘中行情"


def test_stock_zh_index_spot_realtime_from_tx(monkeypatch):
    def mock_stock_zh_index_spot_tx(*args, **kwargs):
        return pd.DataFrame(
            [
                {
                    "序号": 1,
                    "代码": "000905",
                    "名称": "中证500",
                    "最新价": 8673.09,
                    "涨跌幅": 0.53,
                    "涨跌额": 46.00,
                    "成交量": 239467579,
                    "成交额": 667474010745,
                    "振幅": 1.49,
                    "最高": 8716.34,
                    "最低": 8587.98,
                    "今开": 8590.50,
                    "昨收": 8627.09,
                    "量比": None,
                    "数据来源": "腾讯-实时行情",
                    "更新时间": "20260618161413",
                }
            ]
        )

    monkeypatch.setattr(
        index_stock_zh, "stock_zh_index_spot_tx", mock_stock_zh_index_spot_tx
    )

    temp_df = index_stock_zh.stock_zh_index_spot_realtime(symbol="000905")

    assert temp_df.loc[0, "代码"] == "000905"
    assert temp_df.loc[0, "涨跌幅"] == 0.53
    assert temp_df.loc[0, "数据来源"] == "腾讯-实时行情"


def test_stock_zh_index_spot_realtime_from_csindex(monkeypatch):
    def mock_stock_zh_index_spot_tx(*args, **kwargs):
        raise ConnectionError("failed")

    def mock_stock_zh_index_spot_csindex(*args, **kwargs):
        return pd.DataFrame(
            [
                {
                    "序号": 1,
                    "代码": "930955",
                    "名称": "红利低波100",
                    "最新价": 11046.66,
                    "涨跌幅": -2.03,
                    "涨跌额": -228.9,
                    "成交量": 6969041773.0,
                    "成交额": 67798000000.0,
                    "振幅": 1.92,
                    "最高": 11246.19,
                    "最低": 11030.00,
                    "今开": 11246.19,
                    "昨收": 11275.57,
                    "量比": None,
                    "数据来源": "中证官网-盘中行情",
                    "更新时间": "2026-06-18 16:29:53",
                }
            ]
        )

    monkeypatch.setattr(
        index_stock_zh, "stock_zh_index_spot_tx", mock_stock_zh_index_spot_tx
    )
    monkeypatch.setattr(
        index_stock_zh,
        "stock_zh_index_spot_csindex",
        mock_stock_zh_index_spot_csindex,
    )

    temp_df = index_stock_zh.stock_zh_index_spot_realtime(symbol="930955")

    assert temp_df.loc[0, "代码"] == "930955"
    assert temp_df.loc[0, "涨跌幅"] == -2.03
    assert temp_df.loc[0, "数据来源"] == "中证官网-盘中行情"


def test_stock_zh_index_spot_realtime_from_sina(monkeypatch):
    def mock_stock_zh_index_spot_tx(*args, **kwargs):
        raise ConnectionError("failed")

    def mock_stock_zh_index_spot_csindex(*args, **kwargs):
        raise ConnectionError("failed")

    def mock_stock_zh_index_spot_xq(*args, **kwargs):
        raise ConnectionError("failed")

    def mock_stock_zh_index_spot_sina():
        return pd.DataFrame(
            [
                {
                    "代码": "sh000905",
                    "名称": "中证500",
                    "最新价": 5930.12,
                    "涨跌额": 30.12,
                    "涨跌幅": 0.51,
                    "昨收": 5900.00,
                    "今开": 5910.12,
                    "最高": 5960.12,
                    "最低": 5900.12,
                    "成交量": 123456,
                    "成交额": 123456789.0,
                }
            ]
        )

    monkeypatch.setattr(index_stock_zh, "stock_zh_index_spot_tx", mock_stock_zh_index_spot_tx)
    monkeypatch.setattr(
        index_stock_zh,
        "stock_zh_index_spot_csindex",
        mock_stock_zh_index_spot_csindex,
    )
    monkeypatch.setattr(index_stock_zh, "stock_zh_index_spot_xq", mock_stock_zh_index_spot_xq)
    monkeypatch.setattr(
        index_stock_zh, "stock_zh_index_spot_sina", mock_stock_zh_index_spot_sina
    )

    temp_df = index_stock_zh.stock_zh_index_spot_realtime(symbol="000905")

    assert temp_df.loc[0, "代码"] == "000905"
    assert temp_df.loc[0, "名称"] == "中证500"
    assert temp_df.loc[0, "涨跌幅"] == 0.51
    assert temp_df.loc[0, "数据来源"] == "新浪-实时行情"


def test_stock_zh_index_spot_realtime_sources_failed(monkeypatch):
    def mock_stock_zh_index_spot_tx(*args, **kwargs):
        raise ConnectionError("failed")

    def mock_stock_zh_index_spot_csindex(*args, **kwargs):
        raise ConnectionError("failed")

    def mock_stock_zh_index_spot_xq(*args, **kwargs):
        raise ConnectionError("failed")

    def mock_stock_zh_index_spot_sina():
        raise ConnectionError("failed")

    monkeypatch.setattr(index_stock_zh, "stock_zh_index_spot_tx", mock_stock_zh_index_spot_tx)
    monkeypatch.setattr(
        index_stock_zh,
        "stock_zh_index_spot_csindex",
        mock_stock_zh_index_spot_csindex,
    )
    monkeypatch.setattr(index_stock_zh, "stock_zh_index_spot_xq", mock_stock_zh_index_spot_xq)
    monkeypatch.setattr(
        index_stock_zh, "stock_zh_index_spot_sina", mock_stock_zh_index_spot_sina
    )

    temp_df = index_stock_zh.stock_zh_index_spot_realtime(symbol="000905")

    assert temp_df.empty
    assert list(temp_df.columns) == index_stock_zh._ZH_INDEX_SPOT_STABLE_COLUMNS

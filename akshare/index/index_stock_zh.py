#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/5/2 16:30
Desc: 股票指数数据-新浪-东财-腾讯
所有指数-实时行情数据和历史行情数据
https://finance.sina.com.cn/realstock/company/sz399552/nc.shtml
"""

import datetime
import re

import pandas as pd
import py_mini_racer
import requests

from akshare.index.cons import (
    zh_sina_index_stock_payload,
    zh_sina_index_stock_url,
    zh_sina_index_stock_count_url,
    zh_sina_index_stock_hist_url,
)
from akshare.stock.cons import hk_js_decode
from akshare.stock.stock_xq import stock_individual_spot_xq
from akshare.utils import demjson
from akshare.utils.func import fetch_paginated_data
from akshare.utils.tqdm import get_tqdm


_ZH_INDEX_SPOT_STABLE_COLUMNS = [
    "序号",
    "代码",
    "名称",
    "最新价",
    "涨跌幅",
    "涨跌额",
    "成交量",
    "成交额",
    "振幅",
    "最高",
    "最低",
    "今开",
    "昨收",
    "量比",
    "数据来源",
    "更新时间",
]


def _replace_comma(x):
    """
    去除单元格中的 ","
    :param x: 单元格元素
    :type x: str
    :return: 处理后的值或原值
    :rtype: str
    """
    if "," in str(x):
        return str(x).replace(",", "")
    else:
        return x


def get_zh_index_page_count() -> int:
    """
    指数的总页数
    https://vip.stock.finance.sina.com.cn/mkt/#hs_s
    :return: 需要抓取的指数的总页数
    :rtype: int
    """
    res = requests.get(zh_sina_index_stock_count_url)
    page_count = int(re.findall(re.compile(r"\d+"), res.text)[0]) / 80
    if isinstance(page_count, int):
        return page_count
    else:
        return int(page_count) + 1


def stock_zh_index_spot_sina() -> pd.DataFrame:
    """
    新浪财经-行情中心首页-A股-分类-所有指数
    大量采集会被目标网站服务器封禁 IP，如果被封禁 IP，请 10 分钟后再试
    https://vip.stock.finance.sina.com.cn/mkt/#hs_s
    :return: 所有指数的实时行情数据
    :rtype: pandas.DataFrame
    """
    big_df = pd.DataFrame()
    page_count = get_zh_index_page_count()
    zh_sina_stock_payload_copy = zh_sina_index_stock_payload.copy()
    tqdm = get_tqdm()
    for page in tqdm(range(1, page_count + 1), leave=False):
        zh_sina_stock_payload_copy.update({"page": page})
        res = requests.get(zh_sina_index_stock_url, params=zh_sina_stock_payload_copy)
        data_json = demjson.decode(res.text)
        big_df = pd.concat(objs=[big_df, pd.DataFrame(data_json)], ignore_index=True)
    big_df = big_df.map(_replace_comma)
    big_df["trade"] = pd.to_numeric(big_df["trade"], errors="coerce")
    big_df["pricechange"] = pd.to_numeric(big_df["pricechange"], errors="coerce")
    big_df["changepercent"] = pd.to_numeric(big_df["changepercent"], errors="coerce")
    big_df["buy"] = pd.to_numeric(big_df["buy"], errors="coerce")
    big_df["sell"] = pd.to_numeric(big_df["sell"], errors="coerce")
    big_df["settlement"] = pd.to_numeric(big_df["settlement"], errors="coerce")
    big_df["open"] = pd.to_numeric(big_df["open"], errors="coerce")
    big_df["high"] = pd.to_numeric(big_df["high"], errors="coerce")
    big_df["low"] = pd.to_numeric(big_df["low"], errors="coerce")
    big_df.columns = [
        "代码",
        "名称",
        "最新价",
        "涨跌额",
        "涨跌幅",
        "_",
        "_",
        "昨收",
        "今开",
        "最高",
        "最低",
        "成交量",
        "成交额",
        "_",
        "_",
    ]
    big_df = big_df[
        [
            "代码",
            "名称",
            "最新价",
            "涨跌额",
            "涨跌幅",
            "昨收",
            "今开",
            "最高",
            "最低",
            "成交量",
            "成交额",
        ]
    ]
    big_df["最新价"] = pd.to_numeric(big_df["最新价"], errors="coerce")
    big_df["涨跌额"] = pd.to_numeric(big_df["涨跌额"], errors="coerce")
    big_df["涨跌幅"] = pd.to_numeric(big_df["涨跌幅"], errors="coerce")
    big_df["昨收"] = pd.to_numeric(big_df["昨收"], errors="coerce")
    big_df["今开"] = pd.to_numeric(big_df["今开"], errors="coerce")
    big_df["最高"] = pd.to_numeric(big_df["最高"], errors="coerce")
    big_df["最低"] = pd.to_numeric(big_df["最低"], errors="coerce")
    big_df["成交量"] = pd.to_numeric(big_df["成交量"], errors="coerce")
    big_df["成交额"] = pd.to_numeric(big_df["成交额"], errors="coerce")
    return big_df


def __stock_zh_main_spot_em() -> pd.DataFrame:
    """
    东方财富网-行情中心-沪深重要指数
    https://quote.eastmoney.com/center/hszs.html
    :return: 指数的实时行情数据
    :rtype: pandas.DataFrame
    """
    url = "https://33.push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": "1",
        "pz": "100",
        "po": "1",
        "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "dect": "1",
        "wbp2u": "|0|0|0|web",
        "fid": "",
        "fs": "b:MK0010",
        "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,"
        "f23,f24,f25,f26,f22,f11,f62,f128,f136,f115,f152",
    }
    r = requests.get(url, params=params)
    data_json = r.json()
    temp_df = pd.DataFrame(data_json["data"]["diff"])
    temp_df.reset_index(inplace=True)
    temp_df["index"] = temp_df["index"].astype(int) + 1
    temp_df.rename(
        columns={
            "index": "序号",
            "f2": "最新价",
            "f3": "涨跌幅",
            "f4": "涨跌额",
            "f5": "成交量",
            "f6": "成交额",
            "f7": "振幅",
            "f10": "量比",
            "f12": "代码",
            "f14": "名称",
            "f15": "最高",
            "f16": "最低",
            "f17": "今开",
            "f18": "昨收",
        },
        inplace=True,
    )
    temp_df = temp_df[
        [
            "序号",
            "代码",
            "名称",
            "最新价",
            "涨跌幅",
            "涨跌额",
            "成交量",
            "成交额",
            "振幅",
            "最高",
            "最低",
            "今开",
            "昨收",
            "量比",
        ]
    ]
    temp_df["最新价"] = pd.to_numeric(temp_df["最新价"], errors="coerce")
    temp_df["涨跌幅"] = pd.to_numeric(temp_df["涨跌幅"], errors="coerce")
    temp_df["涨跌额"] = pd.to_numeric(temp_df["涨跌额"], errors="coerce")
    temp_df["成交量"] = pd.to_numeric(temp_df["成交量"], errors="coerce")
    temp_df["成交额"] = pd.to_numeric(temp_df["成交额"], errors="coerce")
    temp_df["振幅"] = pd.to_numeric(temp_df["振幅"], errors="coerce")
    temp_df["最高"] = pd.to_numeric(temp_df["最高"], errors="coerce")
    temp_df["最低"] = pd.to_numeric(temp_df["最低"], errors="coerce")
    temp_df["今开"] = pd.to_numeric(temp_df["今开"], errors="coerce")
    temp_df["昨收"] = pd.to_numeric(temp_df["昨收"], errors="coerce")
    temp_df["量比"] = pd.to_numeric(temp_df["量比"], errors="coerce")
    return temp_df


def stock_zh_index_spot_em(symbol: str = "上证系列指数") -> pd.DataFrame:
    """
    东方财富网-行情中心-沪深京指数
    https://quote.eastmoney.com/center/gridlist.html#index_sz
    :param symbol: "上证系列指数"; choice of {"沪深重要指数", "上证系列指数", "深证系列指数", "指数成份", "中证系列指数"}
    :type symbol: str
    :return: 指数的实时行情数据
    :rtype: pandas.DataFrame
    """
    if symbol == "沪深重要指数":
        return __stock_zh_main_spot_em()

    url = "https://48.push2.eastmoney.com/api/qt/clist/get"
    symbol_map = {
        "上证系列指数": "m:1+t:1",
        "深证系列指数": "m:0 t:5",
        "指数成份": "m:1+s:3,m:0+t:5",
        "中证系列指数": "m:2",
    }
    params = {
        "pn": "1",
        "pz": "100",
        "po": "1",
        "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "wbp2u": "|0|0|0|web",
        "fid": "f12",
        "fs": symbol_map[symbol],
        "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,"
        "f26,f22,f33,f11,f62,f128,f136,f115,f152",
    }
    temp_df = fetch_paginated_data(url, params)
    temp_df.rename(
        columns={
            "index": "序号",
            "f2": "最新价",
            "f3": "涨跌幅",
            "f4": "涨跌额",
            "f5": "成交量",
            "f6": "成交额",
            "f7": "振幅",
            "f10": "量比",
            "f12": "代码",
            "f14": "名称",
            "f15": "最高",
            "f16": "最低",
            "f17": "今开",
            "f18": "昨收",
        },
        inplace=True,
    )
    temp_df = temp_df[
        [
            "序号",
            "代码",
            "名称",
            "最新价",
            "涨跌幅",
            "涨跌额",
            "成交量",
            "成交额",
            "振幅",
            "最高",
            "最低",
            "今开",
            "昨收",
            "量比",
        ]
    ]
    temp_df["最新价"] = pd.to_numeric(temp_df["最新价"], errors="coerce")
    temp_df["涨跌幅"] = pd.to_numeric(temp_df["涨跌幅"], errors="coerce")
    temp_df["涨跌额"] = pd.to_numeric(temp_df["涨跌额"], errors="coerce")
    temp_df["成交量"] = pd.to_numeric(temp_df["成交量"], errors="coerce")
    temp_df["成交额"] = pd.to_numeric(temp_df["成交额"], errors="coerce")
    temp_df["振幅"] = pd.to_numeric(temp_df["振幅"], errors="coerce")
    temp_df["最高"] = pd.to_numeric(temp_df["最高"], errors="coerce")
    temp_df["最低"] = pd.to_numeric(temp_df["最低"], errors="coerce")
    temp_df["今开"] = pd.to_numeric(temp_df["今开"], errors="coerce")
    temp_df["昨收"] = pd.to_numeric(temp_df["昨收"], errors="coerce")
    temp_df["量比"] = pd.to_numeric(temp_df["量比"], errors="coerce")
    return temp_df


def _stock_zh_index_spot_realtime_empty() -> pd.DataFrame:
    """
    股票指数-单指数实时行情-空数据结构
    :return: 空数据
    :rtype: pandas.DataFrame
    """
    return pd.DataFrame(columns=_ZH_INDEX_SPOT_STABLE_COLUMNS)


def _stock_zh_index_spot_xq_symbol(symbol: str) -> str:
    """
    雪球-指数代码
    :param symbol: 指数代码; e.g., 000905, csi000905, sh000001, sz399001
    :type symbol: str
    :return: 雪球指数代码
    :rtype: str
    """
    symbol = symbol.strip()
    lower_symbol = symbol.lower()

    if lower_symbol.startswith(("sh", "sz", "bj")):
        return lower_symbol.upper()
    if lower_symbol.startswith("csi"):
        symbol = symbol[3:]
    if symbol.startswith(("399", "980")):
        return f"SZ{symbol}"
    return f"SH{symbol}"


def _stock_zh_index_spot_tx_symbol(symbol: str) -> str:
    """
    腾讯-指数代码
    :param symbol: 指数代码; e.g., 000905, csi000905, sh000001, sz399001
    :type symbol: str
    :return: 腾讯指数代码
    :rtype: str
    """
    symbol = symbol.strip()
    lower_symbol = symbol.lower()

    if lower_symbol.startswith(("sh", "sz")):
        return lower_symbol
    if lower_symbol.startswith("csi"):
        symbol = symbol[3:]
    if symbol.startswith(("399", "980")):
        return f"sz{symbol}"
    return f"sh{symbol}"


def _stock_zh_index_spot_em_sina_symbol(symbol: str) -> str:
    """
    新浪-指数代码
    :param symbol: 指数代码; e.g., 000905, sh000001, sz399001
    :type symbol: str
    :return: 带市场前缀的新浪指数代码
    :rtype: str
    """
    symbol = symbol.strip()
    lower_symbol = symbol.lower()

    if lower_symbol.startswith(("sh", "sz")):
        return lower_symbol
    if lower_symbol.startswith("csi"):
        symbol = symbol[3:]

    if symbol.startswith(("399", "980")):
        return f"sz{symbol}"
    return f"sh{symbol}"


def _stock_zh_index_spot_csindex_symbol(symbol: str) -> str:
    """
    中证官网-指数代码
    :param symbol: 指数代码; e.g., 930955, csi930955, sh000905, sz399001
    :type symbol: str
    :return: 中证官网指数代码
    :rtype: str
    """
    symbol = symbol.strip()
    lower_symbol = symbol.lower()

    if lower_symbol.startswith(("sh", "sz")):
        return symbol[2:].upper()
    if lower_symbol.startswith("csi"):
        return symbol[3:].upper()
    return symbol.upper()


def _stock_zh_index_spot_realtime_to_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """
    中证指数-单指数实时行情-字段类型转换
    :param df: 原始数据
    :type df: pandas.DataFrame
    :return: 类型转换后的数据
    :rtype: pandas.DataFrame
    """
    numeric_columns = [
        "最新价",
        "涨跌幅",
        "涨跌额",
        "成交量",
        "成交额",
        "振幅",
        "最高",
        "最低",
        "今开",
        "昨收",
        "量比",
    ]
    for item in numeric_columns:
        df[item] = pd.to_numeric(df[item], errors="coerce")
    return df


def _stock_zh_index_spot_from_csindex_json(
    data_json: dict, symbol: str
) -> pd.DataFrame:
    """
    中证官网-指数实时行情-结果转换
    :param data_json: 中证官网实时行情 JSON
    :type data_json: dict
    :param symbol: 指数代码
    :type symbol: str
    :return: 指数实时行情
    :rtype: pandas.DataFrame
    """
    if str(data_json.get("code")) != "200":
        return _stock_zh_index_spot_realtime_empty()

    data = data_json.get("data") or {}
    header = data.get("intraDayHeader") or {}
    perf_list = data.get("intraDayPerfList") or []
    if not header:
        return _stock_zh_index_spot_realtime_empty()

    name = None
    high = None
    low = None
    if perf_list:
        name = perf_list[0].get("indexName")
        high_list = [
            pd.to_numeric(item.get("high"), errors="coerce")
            for item in perf_list
            if item.get("high") is not None
        ]
        low_list = [
            pd.to_numeric(item.get("low"), errors="coerce")
            for item in perf_list
            if item.get("low") is not None
        ]
        high_list = [item for item in high_list if pd.notna(item)]
        low_list = [item for item in low_list if pd.notna(item)]
        high = max(
            high_list,
            default=None,
        )
        low = min(
            low_list,
            default=None,
        )

    yesterday_close = pd.to_numeric(header.get("closePre"), errors="coerce")
    amplitude = (
        round((high - low) / yesterday_close * 100, 2)
        if high is not None
        and low is not None
        and yesterday_close
        and pd.notna(yesterday_close)
        else None
    )
    trading_value = pd.to_numeric(header.get("tradingValue"), errors="coerce")
    trading_value = (
        trading_value * 100000000 if pd.notna(trading_value) else trading_value
    )
    update_time = None
    if header.get("tradeDate") and header.get("tradeTime"):
        update_time = f"{header.get('tradeDate')} {header.get('tradeTime')}"

    result_df = pd.DataFrame(
        [
            {
                "序号": 1,
                "代码": header.get(
                    "indexCode",
                    _stock_zh_index_spot_csindex_symbol(symbol=symbol),
                ),
                "名称": name,
                "最新价": header.get("current"),
                "涨跌幅": header.get("changePct"),
                "涨跌额": header.get("change"),
                "成交量": header.get("tradingVol"),
                "成交额": trading_value,
                "振幅": amplitude,
                "最高": high,
                "最低": low,
                "今开": header.get("openToday"),
                "昨收": header.get("closePre"),
                "量比": None,
                "数据来源": "中证官网-盘中行情",
                "更新时间": update_time,
            }
        ],
        columns=_ZH_INDEX_SPOT_STABLE_COLUMNS,
    )
    result_df = _stock_zh_index_spot_realtime_to_numeric(result_df)
    if result_df["最新价"].isna().all() or result_df["代码"].isna().all():
        return _stock_zh_index_spot_realtime_empty()
    return result_df


def _stock_zh_index_spot_from_xq_items(
    temp_df: pd.DataFrame, symbol: str
) -> pd.DataFrame:
    """
    雪球-指数实时行情-结果转换
    :param temp_df: 雪球单证券实时行情
    :type temp_df: pandas.DataFrame
    :param symbol: 指数代码
    :type symbol: str
    :return: 指数实时行情
    :rtype: pandas.DataFrame
    """
    if temp_df.empty:
        return _stock_zh_index_spot_realtime_empty()

    item_map = dict(zip(temp_df["item"], temp_df["value"]))
    code = str(item_map.get("代码") or _stock_zh_index_spot_xq_symbol(symbol=symbol))
    code = code[2:] if code[:2].upper() in {"SH", "SZ", "BJ"} else code

    result_df = pd.DataFrame(
        [
            {
                "序号": 1,
                "代码": code,
                "名称": item_map.get("名称"),
                "最新价": item_map.get("现价"),
                "涨跌幅": item_map.get("涨幅"),
                "涨跌额": item_map.get("涨跌"),
                "成交量": item_map.get("成交量"),
                "成交额": item_map.get("成交额"),
                "振幅": item_map.get("振幅"),
                "最高": item_map.get("最高"),
                "最低": item_map.get("最低"),
                "今开": item_map.get("今开"),
                "昨收": item_map.get("昨收"),
                "量比": None,
                "数据来源": "雪球-实时行情",
                "更新时间": item_map.get("时间"),
            }
        ],
        columns=_ZH_INDEX_SPOT_STABLE_COLUMNS,
    )
    result_df = _stock_zh_index_spot_realtime_to_numeric(result_df)
    if result_df["最新价"].isna().all() or result_df["代码"].isna().all():
        return _stock_zh_index_spot_realtime_empty()
    return result_df


def _stock_zh_index_spot_from_sina(
    temp_df: pd.DataFrame, symbol: str
) -> pd.DataFrame:
    """
    新浪-指数实时行情-结果转换
    :param temp_df: 新浪所有指数实时行情
    :type temp_df: pandas.DataFrame
    :param symbol: 指数代码
    :type symbol: str
    :return: 指数实时行情
    :rtype: pandas.DataFrame
    """
    sina_symbol = _stock_zh_index_spot_em_sina_symbol(symbol=symbol)
    code = sina_symbol[2:]
    match_df = temp_df[
        (temp_df["代码"].astype(str).str.lower() == sina_symbol)
        | (temp_df["代码"].astype(str).str[-6:] == code)
    ]
    if match_df.empty:
        return _stock_zh_index_spot_realtime_empty()

    row = match_df.iloc[0]
    yesterday_close = pd.to_numeric(row["昨收"], errors="coerce")
    high = pd.to_numeric(row["最高"], errors="coerce")
    low = pd.to_numeric(row["最低"], errors="coerce")
    amplitude = (
        round((high - low) / yesterday_close * 100, 2)
        if yesterday_close and pd.notna(yesterday_close)
        else None
    )
    result_df = pd.DataFrame(
        [
            {
                "序号": 1,
                "代码": code,
                "名称": row["名称"],
                "最新价": row["最新价"],
                "涨跌幅": row["涨跌幅"],
                "涨跌额": row["涨跌额"],
                "成交量": row["成交量"],
                "成交额": row["成交额"],
                "振幅": amplitude,
                "最高": row["最高"],
                "最低": row["最低"],
                "今开": row["今开"],
                "昨收": row["昨收"],
                "量比": None,
                "数据来源": "新浪-实时行情",
                "更新时间": None,
            }
        ],
        columns=_ZH_INDEX_SPOT_STABLE_COLUMNS,
    )
    return _stock_zh_index_spot_realtime_to_numeric(result_df)


def _stock_zh_index_spot_from_tx_text(text: str) -> pd.DataFrame:
    """
    腾讯-指数实时行情-结果转换
    :param text: 腾讯实时行情文本
    :type text: str
    :return: 指数实时行情
    :rtype: pandas.DataFrame
    """
    if '="' not in text:
        return _stock_zh_index_spot_realtime_empty()

    data_text = text.split('="', 1)[1].rsplit('"', 1)[0]
    data_list = data_text.split("~")
    if len(data_list) < 35:
        return _stock_zh_index_spot_realtime_empty()

    amount = None
    if len(data_list) > 35 and "/" in data_list[35]:
        amount_list = data_list[35].split("/")
        if len(amount_list) >= 3:
            amount = amount_list[2]
    if amount is None and len(data_list) > 37:
        amount = pd.to_numeric(data_list[37], errors="coerce") * 10000

    result_df = pd.DataFrame(
        [
            {
                "序号": 1,
                "代码": data_list[2],
                "名称": data_list[1],
                "最新价": data_list[3],
                "涨跌幅": data_list[32] if len(data_list) > 32 else None,
                "涨跌额": data_list[31] if len(data_list) > 31 else None,
                "成交量": data_list[6],
                "成交额": amount,
                "振幅": data_list[43] if len(data_list) > 43 else None,
                "最高": data_list[33] if len(data_list) > 33 else None,
                "最低": data_list[34] if len(data_list) > 34 else None,
                "今开": data_list[5],
                "昨收": data_list[4],
                "量比": None,
                "数据来源": "腾讯-实时行情",
                "更新时间": data_list[30] if len(data_list) > 30 else None,
            }
        ],
        columns=_ZH_INDEX_SPOT_STABLE_COLUMNS,
    )
    result_df = _stock_zh_index_spot_realtime_to_numeric(result_df)
    if result_df["最新价"].isna().all() or result_df["代码"].isna().all():
        return _stock_zh_index_spot_realtime_empty()
    return result_df


def stock_zh_index_spot_xq(
    symbol: str = "000905", token: str = None, timeout: float = None
) -> pd.DataFrame:
    """
    雪球-股票指数-单指数实时行情
    https://xueqiu.com/S/SH000905
    :param symbol: 指数代码; e.g., 000905, csi000905, sh000001, sz399001
    :type symbol: str
    :param token: 雪球财经的 token
    :type token: str
    :param timeout: 请求超时时间
    :type timeout: float
    :return: 指数行情数据
    :rtype: pandas.DataFrame
    """
    xq_symbol = _stock_zh_index_spot_xq_symbol(symbol=symbol)
    return _stock_zh_index_spot_from_xq_items(
        temp_df=stock_individual_spot_xq(
            symbol=xq_symbol, token=token, timeout=timeout
        ),
        symbol=symbol,
    )


def stock_zh_index_spot_tx(
    symbol: str = "000905", timeout: float = None
) -> pd.DataFrame:
    """
    腾讯-股票指数-单指数实时行情
    https://gu.qq.com/sh000905/zs
    :param symbol: 指数代码; e.g., 000905, csi000905, sh000001, sz399001
    :type symbol: str
    :param timeout: 请求超时时间
    :type timeout: float
    :return: 指数行情数据
    :rtype: pandas.DataFrame
    """
    tx_symbol = _stock_zh_index_spot_tx_symbol(symbol=symbol)
    url = "https://qt.gtimg.cn/q={}".format(tx_symbol)
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://gu.qq.com/{}/zs".format(tx_symbol),
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    r.encoding = "GBK"
    return _stock_zh_index_spot_from_tx_text(r.text)


def stock_zh_index_spot_csindex(
    symbol: str = "930955", timeout: float = None
) -> pd.DataFrame:
    """
    中证官网-股票指数-单指数盘中行情
    https://www.csindex.com.cn
    :param symbol: 指数代码; e.g., 930955, csi930955, sh000905, sz399001
    :type symbol: str
    :param timeout: 请求超时时间
    :type timeout: float
    :return: 指数行情数据
    :rtype: pandas.DataFrame
    """
    csindex_symbol = _stock_zh_index_spot_csindex_symbol(symbol=symbol)
    url = "https://www.csindex.com.cn/csindex-home/perf/index-perf-oneday"
    params = {"indexCode": csindex_symbol}
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.csindex.com.cn/",
        "Accept": "application/json, text/plain, */*",
    }
    r = requests.get(url, params=params, headers=headers, timeout=timeout)
    data_json = r.json()
    return _stock_zh_index_spot_from_csindex_json(
        data_json=data_json, symbol=symbol
    )


def stock_zh_index_spot_realtime(
    symbol: str = "000905", token: str = None, timeout: float = None
) -> pd.DataFrame:
    """
    股票指数-单指数实时行情
    先使用腾讯实时行情; 若失败, 回退到中证官网盘中行情、雪球和新浪实时行情; 仍失败时返回空表, 不使用东方财富和日频数据。
    https://gu.qq.com/sh000905/zs
    :param symbol: 指数代码; e.g., 930955, 000905, csi000905, sh000001, sz399001
    :type symbol: str
    :param token: 雪球财经的 token
    :type token: str
    :param timeout: 请求超时时间
    :type timeout: float
    :return: 指数行情数据
    :rtype: pandas.DataFrame
    """
    try:
        temp_df = stock_zh_index_spot_tx(symbol=symbol, timeout=timeout)
        if not temp_df.empty:
            return temp_df
    except Exception:  # noqa: PERF203
        pass

    try:
        temp_df = stock_zh_index_spot_csindex(symbol=symbol, timeout=timeout)
        if not temp_df.empty:
            return temp_df
    except Exception:  # noqa: PERF203
        pass

    try:
        temp_df = stock_zh_index_spot_xq(
            symbol=symbol, token=token, timeout=timeout
        )
        if not temp_df.empty:
            return temp_df
    except Exception:  # noqa: PERF203
        pass

    try:
        temp_df = _stock_zh_index_spot_from_sina(
            temp_df=stock_zh_index_spot_sina(), symbol=symbol
        )
        if not temp_df.empty:
            return temp_df
    except Exception:  # noqa: PERF203
        pass

    return _stock_zh_index_spot_realtime_empty()


def stock_zh_index_daily(symbol: str = "sh000922") -> pd.DataFrame:
    """
    新浪财经-指数-历史行情数据，大量抓取容易封 IP
    https://finance.sina.com.cn/realstock/company/sh000909/nc.shtml
    :param symbol: sz399998，指定指数代码
    :type symbol: str
    :return: 历史行情数据
    :rtype: pandas.DataFrame
    """
    params = {"d": "2020_2_4"}
    res = requests.get(zh_sina_index_stock_hist_url.format(symbol), params=params)
    js_code = py_mini_racer.MiniRacer()
    js_code.eval(hk_js_decode)
    dict_list = js_code.call(
        "d", res.text.split("=")[1].split(";")[0].replace('"', "")
    )  # 执行js解密代码
    temp_df = pd.DataFrame(dict_list)
    temp_df["date"] = pd.to_datetime(temp_df["date"], errors="coerce").dt.date
    temp_df["open"] = pd.to_numeric(temp_df["open"], errors="coerce")
    temp_df["close"] = pd.to_numeric(temp_df["close"], errors="coerce")
    temp_df["high"] = pd.to_numeric(temp_df["high"], errors="coerce")
    temp_df["low"] = pd.to_numeric(temp_df["low"], errors="coerce")
    temp_df["volume"] = pd.to_numeric(temp_df["volume"], errors="coerce")
    return temp_df


def get_tx_start_year(symbol: str = "sh000919") -> str:
    """
    腾讯证券-获取所有股票数据的第一天，注意这个数据是腾讯证券的历史数据第一天
    https://gu.qq.com/sh000919/zs
    :param symbol: 带市场标识的股票代码
    :type symbol: str
    :return: 开始日期
    :rtype: str
    """
    url = "https://web.ifzq.gtimg.cn/other/klineweb/klineWeb/weekTrends"
    params = {
        "code": symbol,
        "type": "qfq",
        "_var": "trend_qfq",
        "r": "0.3506048543943414",
    }
    r = requests.get(url, params=params)
    data_text = r.text
    if not demjson.decode(data_text[data_text.find("={") + 1 :])["data"]:
        url = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
        params = {
            "_var": "kline_dayqfq",
            "param": f"{symbol},day,,,320,qfq",
            "r": "0.751892490072597",
        }
        r = requests.get(url, params=params)
        data_text = r.text
        start_date = demjson.decode(data_text[data_text.find("={") + 1 :])["data"][
            symbol
        ]["day"][0][0]
        return start_date
    start_date = demjson.decode(data_text[data_text.find("={") + 1 :])["data"][0][0]
    return start_date


def stock_zh_index_daily_tx(
    symbol: str = "sz980017",
    start_date: str = "",
    end_date: str = "",
) -> pd.DataFrame:
    """
    腾讯证券-日频-股票或者指数历史数据（支持自定义时间范围）
    作为 ak.stock_zh_index_daily() 的补充，因为在新浪中有部分指数数据缺失
    注意都是：前复权，不同网站复权方式不同，不可混用数据
    https://gu.qq.com/sh000919/zs
    :param symbol: 带市场标识的股票或者指数代码
    :type symbol: str
    :param start_date: 开始日期，格式 "YYYYMMDD"，为空则从最早日期开始
    :type start_date: str
    :param end_date: 结束日期，格式 "YYYYMMDD"，为空则到当前日期
    :type end_date: str
    :return: 前复权的股票和指数数据
    :rtype: pandas.DataFrame
    """
    if start_date:
        dt_start = datetime.datetime.strptime(start_date, "%Y%m%d")
        i_start_year = dt_start.year
    else:
        earliest_date = get_tx_start_year(symbol=symbol)
        dt_start = datetime.datetime.strptime(earliest_date, "%Y-%m-%d")
        i_start_year = dt_start.year

    if end_date:
        dt_end = datetime.datetime.strptime(end_date, "%Y%m%d")
        i_end_year = dt_end.year
    else:
        dt_end = datetime.datetime.combine(
            datetime.date.today(), datetime.datetime.min.time()
        )
        i_end_year = dt_end.year

    url = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
    temp_df = pd.DataFrame()
    tqdm = get_tqdm()
    for year in tqdm(range(i_start_year, i_end_year + 1), leave=False):
        params = {
            "_var": "kline_dayqfq",
            "param": f"{symbol},day,{year}-01-01,{year + 1}-12-31,640,qfq",
            "r": "0.8205512681390605",
        }
        res = requests.get(url, params=params)
        text = res.text
        try:
            inner_temp_df = pd.DataFrame(
                demjson.decode(text[text.find("={") + 1 :])["data"][symbol]["day"]
            )
        except:  # noqa: E722
            inner_temp_df = pd.DataFrame(
                demjson.decode(text[text.find("={") + 1 :])["data"][symbol]["qfqday"]
            )
        temp_df = pd.concat(objs=[temp_df, inner_temp_df], ignore_index=True)
    if temp_df.shape[1] == 6:
        temp_df.columns = ["date", "open", "close", "high", "low", "amount"]
    else:
        temp_df = temp_df.iloc[:, :6]
        temp_df.columns = ["date", "open", "close", "high", "low", "amount"]
    temp_df["date"] = pd.to_datetime(temp_df["date"], errors="coerce").dt.date
    temp_df["open"] = pd.to_numeric(temp_df["open"], errors="coerce")
    temp_df["close"] = pd.to_numeric(temp_df["close"], errors="coerce")
    temp_df["high"] = pd.to_numeric(temp_df["high"], errors="coerce")
    temp_df["low"] = pd.to_numeric(temp_df["low"], errors="coerce")
    temp_df["amount"] = pd.to_numeric(temp_df["amount"], errors="coerce")
    temp_df.drop_duplicates(inplace=True, ignore_index=True)
    temp_df = temp_df[temp_df["date"] >= dt_start.date()]
    temp_df = temp_df[temp_df["date"] <= dt_end.date()]
    temp_df.reset_index(drop=True, inplace=True)
    return temp_df


def stock_zh_index_daily_em(
    symbol: str = "csi931151",
    start_date: str = "19900101",
    end_date: str = "20500101",
) -> pd.DataFrame:
    """
    东方财富网-股票指数数据
    https://quote.eastmoney.com/center/hszs.html
    :param symbol: 带市场标识的指数代码；sz: 深交所，sh: 上交所，csi: 中信指数 + id(000905)
    :type symbol: str
    :param start_date: 开始时间
    :type start_date: str
    :param end_date: 结束时间
    :type end_date: str
    :return: 指数数据
    :rtype: pandas.DataFrame
    """
    market_map = {"sz": "0", "sh": "1", "csi": "2", "bj": "0"}
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    if symbol.find("sz") != -1:
        secid = "{}.{}".format(market_map["sz"], symbol.replace("sz", ""))
    elif symbol.find("bj") != -1:
        secid = "{}.{}".format(market_map["bj"], symbol.replace("bj", ""))
    elif symbol.find("sh") != -1:
        secid = "{}.{}".format(market_map["sh"], symbol.replace("sh", ""))
    elif symbol.find("csi") != -1:
        secid = "{}.{}".format(market_map["csi"], symbol.replace("csi", ""))
    else:
        return pd.DataFrame()
    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f4,f5",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
        "klt": "101",  # 日频率
        "fqt": "0",
        "beg": start_date,
        "end": end_date,
    }
    r = requests.get(url, params=params)
    data_json = r.json()
    temp_df = pd.DataFrame([item.split(",") for item in data_json["data"]["klines"]])
    if temp_df.empty:
        return pd.DataFrame()
    temp_df.columns = ["date", "open", "close", "high", "low", "volume", "amount", "_"]
    temp_df = temp_df[["date", "open", "close", "high", "low", "volume", "amount"]]
    temp_df["open"] = pd.to_numeric(temp_df["open"], errors="coerce")
    temp_df["close"] = pd.to_numeric(temp_df["close"], errors="coerce")
    temp_df["high"] = pd.to_numeric(temp_df["high"], errors="coerce")
    temp_df["low"] = pd.to_numeric(temp_df["low"], errors="coerce")
    temp_df["volume"] = pd.to_numeric(temp_df["volume"], errors="coerce")
    temp_df["amount"] = pd.to_numeric(temp_df["amount"], errors="coerce")
    return temp_df


if __name__ == "__main__":
    stock_zh_index_daily_df = stock_zh_index_daily(symbol="sh000510")
    print(stock_zh_index_daily_df)

    stock_zh_index_spot_sina_df = stock_zh_index_spot_sina()
    print(stock_zh_index_spot_sina_df)

    stock_zh_index_spot_em_df = stock_zh_index_spot_em(symbol="沪深重要指数")
    print(stock_zh_index_spot_em_df)

    stock_zh_index_spot_em_df = stock_zh_index_spot_em(symbol="上证系列指数")
    print(stock_zh_index_spot_em_df)

    stock_zh_index_spot_em_df = stock_zh_index_spot_em(symbol="深证系列指数")
    print(stock_zh_index_spot_em_df)

    stock_zh_index_spot_em_df = stock_zh_index_spot_em(symbol="指数成份")
    print(stock_zh_index_spot_em_df)

    stock_zh_index_spot_em_df = stock_zh_index_spot_em(symbol="中证系列指数")
    print(stock_zh_index_spot_em_df)

    stock_zh_index_daily_tx_df = stock_zh_index_daily_tx(
        symbol="sh000919", start_date="20260101", end_date="20260429"
    )
    print(stock_zh_index_daily_tx_df)

    stock_zh_index_daily_em_df = stock_zh_index_daily_em(symbol="bj899050")
    print(stock_zh_index_daily_em_df)

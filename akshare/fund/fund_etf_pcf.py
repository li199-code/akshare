#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/6/27 00:00
Desc: 交易所 ETF PCF 文件解析-持仓成分股权重估算
"""

from datetime import datetime, timedelta
from typing import Any
from xml.etree import ElementTree

import pandas as pd
import requests


def _to_float(value: Any) -> float:
    """
    转换为浮点数
    """
    try:
        if value is None or value == "":
            return float("nan")
        return float(str(value).replace(",", ""))
    except ValueError:
        return float("nan")


def _tag_name(tag: str) -> str:
    """
    移除 XML 命名空间
    """
    return tag.rsplit("}", 1)[-1]


def _get_child_text(node: ElementTree.Element, tag: str) -> str:
    """
    获取子节点文本
    """
    for child in node:
        if _tag_name(child.tag) == tag:
            return (child.text or "").strip()
    return ""


def _find_text(root: ElementTree.Element, tag: str) -> str:
    """
    获取首个指定标签文本
    """
    for item in root.iter():
        if _tag_name(item.tag) == tag:
            return (item.text or "").strip()
    return ""


def _findall(root: ElementTree.Element, tag: str) -> list[ElementTree.Element]:
    """
    获取所有指定标签节点
    """
    return [item for item in root.iter() if _tag_name(item.tag) == tag]


def _stock_market(symbol: str) -> int:
    """
    东方财富市场标识: 1-上海; 0-深圳/北京
    """
    if symbol.startswith(("5", "6", "7", "9")):
        return 1
    return 0


def _fetch_price_map(symbols: list[str]) -> dict[str, float]:
    """
    东方财富批量行情
    """
    if not symbols:
        return {}
    urls = [
        "https://88.push2.eastmoney.com/api/qt/ulist.np/get",
        "https://push2delay.eastmoney.com/api/qt/ulist.np/get",
    ]
    headers = {
        "Referer": "https://quote.eastmoney.com/",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
        ),
    }
    price_map: dict[str, float] = {}
    unique_symbols = sorted(set(symbols))
    for i in range(0, len(unique_symbols), 80):
        temp_symbols = unique_symbols[i : i + 80]
        secids = ",".join([f"{_stock_market(item)}.{item}" for item in temp_symbols])
        params = {
            "fltt": "2",
            "invt": "2",
            "fields": "f12,f2",
            "secids": secids,
        }
        for url in urls:
            try:
                r = requests.get(url, params=params, headers=headers, timeout=15)
                r.raise_for_status()
                data_json = r.json()
            except Exception:
                continue
            diff_list = data_json.get("data", {}).get("diff", [])
            if not diff_list:
                continue
            for item in diff_list:
                price = _to_float(item.get("f2"))
                if pd.notna(price) and price > 0:
                    price_map[item.get("f12")] = price
            break
    return price_map


def _fetch_sse_pcf(symbol: str) -> bytes:
    """
    获取上交所最新 ETF PCF XML
    """
    url = "https://query.sse.com.cn/etfDownload/downloadETF2Bulletin.do"
    params = {"fundCode": symbol}
    headers = {
        "Referer": "https://www.sse.com.cn/",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
        ),
    }
    r = requests.get(url, params=params, headers=headers, timeout=15)
    r.raise_for_status()
    return r.content


def _fetch_szse_pcf(symbol: str) -> bytes:
    """
    获取深交所最新 ETF PCF XML
    """
    url = "https://reportdocs.static.szse.cn/files/text/ETFDown/pcf_{symbol}_{date}.xml"
    headers = {
        "Referer": "https://www.szse.cn/",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
        ),
    }
    today = datetime.now().date()
    for i in range(60):
        date_str = (today - timedelta(days=i)).strftime("%Y%m%d")
        r = requests.get(
            url.format(symbol=symbol, date=date_str), headers=headers, timeout=15
        )
        if r.status_code == 200 and b"<PCFFile" in r.content:
            return r.content
    raise ValueError(f"未获取到 {symbol} 的深交所 ETF PCF 文件")


def _parse_sse_pcf(symbol: str, content: bytes) -> tuple[pd.DataFrame, float]:
    """
    解析上交所 PCF XML
    """
    root = ElementTree.fromstring(content)
    trading_day = _find_text(root, "TradingDay")
    nav_per_cu = _to_float(_find_text(root, "NAVperCU"))
    records = []
    for component in _findall(root, "Component"):
        stock_code = _get_child_text(component, "InstrumentID")
        share = _to_float(_get_child_text(component, "Quantity"))
        cash_amount = _to_float(_get_child_text(component, "SubstitutionCashAmount"))
        if pd.isna(share) or share <= 0:
            continue
        records.append(
            {
                "ETF代码": symbol,
                "交易所": "上交所",
                "交易日": trading_day,
                "股票代码": stock_code,
                "股票简称": _get_child_text(component, "InstrumentName"),
                "持仓数量": share,
                "现金替代金额": cash_amount,
                "现金替代标志": _get_child_text(component, "SubstitutionFlag"),
            }
        )
    return pd.DataFrame(records), nav_per_cu


def _parse_szse_pcf(symbol: str, content: bytes) -> tuple[pd.DataFrame, float]:
    """
    解析深交所 PCF XML
    """
    root = ElementTree.fromstring(content)
    trading_day = _find_text(root, "TradingDay")
    nav_per_cu = _to_float(_find_text(root, "NAVperCU"))
    records = []
    for component in _findall(root, "Component"):
        stock_code = _get_child_text(component, "UnderlyingSecurityID")
        share = _to_float(_get_child_text(component, "ComponentShare"))
        cash_amount = _to_float(_get_child_text(component, "CreationCashSubstitute"))
        if pd.isna(share) or share <= 0:
            continue
        records.append(
            {
                "ETF代码": symbol,
                "交易所": "深交所",
                "交易日": trading_day,
                "股票代码": stock_code,
                "股票简称": _get_child_text(component, "UnderlyingSymbol"),
                "持仓数量": share,
                "现金替代金额": cash_amount,
                "现金替代标志": _get_child_text(component, "SubstituteFlag"),
            }
        )
    return pd.DataFrame(records), nav_per_cu


def fund_etf_hold_pcf(symbol: str = "510300") -> pd.DataFrame:
    """
    交易所 ETF PCF 文件解析-持仓成分股权重估算
    上交所: https://query.sse.com.cn/etfDownload/downloadETF2Bulletin.do?fundCode=510300
    深交所: https://reportdocs.static.szse.cn/files/text/ETFDown/pcf_159026_20260626.xml
    :param symbol: ETF 代码
    :type symbol: str
    :return: ETF 持仓成分股权重估算
    :rtype: pandas.DataFrame
    """
    symbol = symbol.strip().lower().replace("sh", "").replace("sz", "")
    if symbol.startswith("5"):
        content = _fetch_sse_pcf(symbol=symbol)
        temp_df, nav_per_cu = _parse_sse_pcf(symbol=symbol, content=content)
    elif symbol.startswith("1"):
        content = _fetch_szse_pcf(symbol=symbol)
        temp_df, nav_per_cu = _parse_szse_pcf(symbol=symbol, content=content)
    else:
        raise ValueError("仅支持上交所和深交所 ETF 代码")

    if temp_df.empty:
        return temp_df

    price_map = _fetch_price_map(temp_df["股票代码"].tolist())
    temp_df["估算价格"] = temp_df["股票代码"].map(price_map)
    temp_df["估算市值"] = temp_df["持仓数量"] * temp_df["估算价格"]
    temp_df["估算来源"] = "行情"

    mask = temp_df["估算市值"].isna() & temp_df["现金替代金额"].notna()
    mask = mask & (temp_df["现金替代金额"] > 0)
    temp_df.loc[mask, "估算市值"] = temp_df.loc[mask, "现金替代金额"]
    temp_df.loc[mask, "估算价格"] = (
        temp_df.loc[mask, "现金替代金额"] / temp_df.loc[mask, "持仓数量"]
    )
    temp_df.loc[mask, "估算来源"] = "现金替代金额"

    temp_df["权重估算"] = temp_df["估算市值"] / nav_per_cu * 100
    temp_df["交易日"] = pd.to_datetime(temp_df["交易日"], format="%Y%m%d").dt.date
    temp_df = temp_df[
        [
            "ETF代码",
            "交易所",
            "交易日",
            "股票代码",
            "股票简称",
            "持仓数量",
            "估算价格",
            "估算市值",
            "权重估算",
            "估算来源",
            "现金替代金额",
            "现金替代标志",
        ]
    ]
    temp_df["持仓数量"] = pd.to_numeric(temp_df["持仓数量"], errors="coerce")
    temp_df["估算价格"] = pd.to_numeric(temp_df["估算价格"], errors="coerce")
    temp_df["估算市值"] = pd.to_numeric(temp_df["估算市值"], errors="coerce")
    temp_df["权重估算"] = pd.to_numeric(temp_df["权重估算"], errors="coerce")
    temp_df["现金替代金额"] = pd.to_numeric(temp_df["现金替代金额"], errors="coerce")
    temp_df.sort_values(by="权重估算", ascending=False, na_position="last", inplace=True)
    temp_df.reset_index(drop=True, inplace=True)
    return temp_df


if __name__ == "__main__":
    fund_etf_hold_pcf_df = fund_etf_hold_pcf(symbol="510300")
    print(fund_etf_hold_pcf_df)

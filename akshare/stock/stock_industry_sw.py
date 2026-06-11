#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2024/7/22 17:30
Desc: 申万宏源研究-行业分类
http://www.swhyresearch.com/institute_sw/allIndex/downloadCenter/industryType
"""

import io

import pandas as pd
import requests
import urllib3

from akshare.stock.stock_industry_cninfo import stock_industry_category_cninfo
from akshare.stock.stock_info import stock_info_a_code_name
from akshare.utils.cons import headers

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def stock_industry_clf_hist_sw() -> pd.DataFrame:
    """
    申万宏源研究-行业分类-全部行业分类
    https://www.swsresearch.com/swindex/pdf/SwClass2021/StockClassifyUse_stock.xls
    :return: 个股行业分类变动历史
    :rtype: pandas.DataFrame
    """
    url = "https://www.swsresearch.com/swindex/pdf/SwClass2021/StockClassifyUse_stock.xls"  # 此处为 https
    r = requests.get(url, headers=headers, verify=False)
    temp_df = pd.read_excel(
        io.BytesIO(r.content), dtype={"股票代码": "str", "行业代码": "str"}
    )
    temp_df.rename(
        columns={
            "股票代码": "symbol",
            "计入日期": "start_date",
            "行业代码": "industry_code",
            "更新日期": "update_time",
        },
        inplace=True,
    )
    temp_df["start_date"] = pd.to_datetime(
        temp_df["start_date"], errors="coerce"
    ).dt.date
    temp_df["update_time"] = pd.to_datetime(
        temp_df["update_time"], errors="coerce"
    ).dt.date
    return temp_df


def stock_industry_clf_detail_sw() -> pd.DataFrame:
    """
    申万宏源研究-行业分类-全部 A 股当前申万行业分类明细
    https://www.swsresearch.com/swindex/pdf/SwClass2021/StockClassifyUse_stock.xls
    :return: 全部 A 股当前申万行业分类明细
    :rtype: pandas.DataFrame
    """
    hist_df = stock_industry_clf_hist_sw()
    hist_df = (
        hist_df.sort_values(by=["symbol", "start_date", "update_time"])
        .groupby("symbol", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )
    hist_df["industry_code"] = "S" + hist_df["industry_code"].astype(str)

    category_df = stock_industry_category_cninfo(symbol="申银万国行业分类标准")
    category_df = category_df[["类目编码", "类目名称", "父类编码"]].copy()
    category_df.columns = ["industry_code", "industry_name", "parent_code"]
    category_df.set_index("industry_code", inplace=True)

    def _get_name_path(code: str) -> list:
        path = []
        current_code = code
        while current_code in category_df.index:
            path.append(category_df.at[current_code, "industry_name"])
            parent_code = category_df.at[current_code, "parent_code"]
            if pd.isna(parent_code) or parent_code not in category_df.index:
                break
            current_code = parent_code
        path.reverse()
        if path and path[0] == "申银万国行业分类":
            path = path[1:]
        return path

    detail_df = hist_df[["industry_code"]].drop_duplicates().copy()
    detail_df["industry_path"] = detail_df["industry_code"].map(_get_name_path)
    detail_df["industry_name_level_1"] = detail_df["industry_path"].map(
        lambda items: items[0] if len(items) >= 1 else None
    )
    detail_df["industry_name_level_2"] = detail_df["industry_path"].map(
        lambda items: items[1] if len(items) >= 2 else None
    )
    detail_df["industry_name_level_3"] = detail_df["industry_path"].map(
        lambda items: items[2] if len(items) >= 3 else None
    )
    detail_df["industry_name_level_4"] = detail_df["industry_path"].map(
        lambda items: items[3] if len(items) >= 4 else (items[-1] if items else None)
    )
    detail_df.drop(columns=["industry_path"], inplace=True)

    stock_name_df = stock_info_a_code_name().rename(columns={"code": "symbol", "name": "name"})
    big_df = pd.merge(hist_df, detail_df, on="industry_code", how="left")
    big_df = pd.merge(stock_name_df, big_df, on="symbol", how="right")
    big_df.rename(columns={"start_date": "change_date"}, inplace=True)
    big_df["standard"] = "申银万国行业分类标准"
    big_df = big_df[
        [
            "symbol",
            "name",
            "industry_code",
            "industry_name_level_1",
            "industry_name_level_2",
            "industry_name_level_3",
            "industry_name_level_4",
            "change_date",
            "standard",
        ]
    ]
    return big_df.reset_index(drop=True)


if __name__ == "__main__":
    stock_industry_clf_hist_sw_df = stock_industry_clf_hist_sw()
    print(stock_industry_clf_hist_sw_df)

    stock_industry_clf_detail_sw_df = stock_industry_clf_detail_sw()
    print(stock_industry_clf_detail_sw_df)

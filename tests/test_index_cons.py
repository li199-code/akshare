#!/usr/bin/env python
# -*- coding:utf-8 -*-

from akshare.index import index_cons


def test_get_csindex_cons_weight_url_from_relative_material(monkeypatch):
    class MockResponse:
        @staticmethod
        def json():
            return {
                "code": "200",
                "data": {
                    "样本权重": [
                        {
                            "filePath": (
                                "https://oss-ch.csindex.com.cn/static/html/csindex/"
                                "public/uploads/file/autofile/closeweightlintiao/"
                                "20260615/930955closeweight.xls"
                            )
                        }
                    ]
                },
            }

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(index_cons.requests, "get", mock_get)

    url = index_cons._get_csindex_cons_weight_url(symbol="930955")

    assert url.endswith("/closeweightlintiao/20260615/930955closeweight.xls")


def test_get_csindex_cons_weight_url_fallback(monkeypatch):
    def mock_get(*args, **kwargs):
        raise ConnectionError("failed")

    monkeypatch.setattr(index_cons.requests, "get", mock_get)

    url = index_cons._get_csindex_cons_weight_url(symbol="930955")

    assert url.endswith("/closeweight/930955closeweight.xls")

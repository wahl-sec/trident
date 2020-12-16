#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident Plugin: HTTP Library
Common HTTP network operations for Trident plugins.
Implemented using generators to allow for asynchronous plugins.
@author: Jacob Wahlman
"""

from typing import AnyStr, Dict, Tuple, Generator

try:
    import requests
except ImportError:
    from urllib.request import Request, urlopen
    from urllib.parse import urlencode


def http_request(url: AnyStr, method: AnyStr="GET", headers: Dict[AnyStr, AnyStr]=None, params: Dict[AnyStr, AnyStr]=None, data: Dict[AnyStr, AnyStr]=None, cookies: Dict[AnyStr, AnyStr]=None, auth: Tuple[AnyStr, AnyStr]=None) -> Generator:
    if not hasattr(requests, method.lower()):
        raise ValueError(f"Invalid method: '{method}'.")

    request = getattr(requests, method.lower())
    yield request(url, headers=headers, params=params, data=data, cookies=cookies, auth=auth)

def http_request_urllib(url: AnyStr, method: AnyStr="GET", headers: Dict[AnyStr, AnyStr]=dict(), data: Dict[AnyStr, AnyStr]=dict()) -> Generator:
    if data is not None:
        data = urlencode(data).encode()

    class _Request:
        def __init__(self, request):
            self.request = request

        def __iter__(self):
            return self

        def __next__(self):
            return urlopen(self.request)

    return iter(_Request(request=Request(url=url, method=method, headers=headers, data=data)))
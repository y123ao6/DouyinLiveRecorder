# -*- coding: utf-8 -*-
import gzip
import urllib.parse
import urllib.error
import requests
import ssl
import json
import urllib.request
from typing import Optional, Dict, Any

# 全局 Session 对象，复用 TCP 连接，提升性能
_session_pool: Optional[requests.Session] = None
_no_proxy_session: Optional[requests.Session] = None

def get_session(use_proxy: bool = True) -> requests.Session:
    """获取复用的 Session 对象，避免重复创建连接"""
    global _session_pool, _no_proxy_session

    if use_proxy:
        if _session_pool is None:
            _session_pool = requests.Session()
            # 配置连接池参数
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=50,
                pool_maxsize=50,
                pool_block=False,
                max_retries=2
            )
            _session_pool.mount('http://', adapter)
            _session_pool.mount('https://', adapter)
        return _session_pool
    else:
        if _no_proxy_session is None:
            _no_proxy_session = requests.Session()
            _no_proxy_session.proxies.update({'http': '', 'https': ''})
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=50,
                pool_maxsize=50,
                pool_block=False,
                max_retries=2
            )
            _no_proxy_session.mount('http://', adapter)
            _no_proxy_session.mount('https://', adapter)
        return _no_proxy_session

no_proxy_handler = urllib.request.ProxyHandler({})
opener = urllib.request.build_opener(no_proxy_handler)

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
OptionalStr = str | None
OptionalDict = dict | None


def sync_req(
        url: str,
        proxy_addr: OptionalStr = None,
        headers: OptionalDict = None,
        data: dict | bytes | None = None,
        json_data: dict | list | None = None,
        timeout: int = 20,
        redirect_url: bool = False,
        abroad: bool = False,
        content_conding: str = 'utf-8'
) -> str:
    if headers is None:
        headers = {}
    try:
        if proxy_addr:
            # 使用带代理的 Session，复用连接
            session = get_session(use_proxy=True)
            session.proxies.update({
                'http': proxy_addr,
                'https': proxy_addr
                })
            if data or json_data:
                response = session.post(
                    url, data=data, json=json_data, headers=headers, timeout=timeout
                )
            else:
                response = session.get(url, headers=headers, timeout=timeout)
            if redirect_url:
                return response.url
            resp_str = response.text
        else:
            if data and not isinstance(data, bytes):
                data = urllib.parse.urlencode(data).encode(content_conding)
            if json_data and isinstance(json_data, (dict, list)):
                data = json.dumps(json_data).encode(content_conding)

            req = urllib.request.Request(url, data=data, headers=headers)

            try:
                if abroad:
                    response = urllib.request.urlopen(req, timeout=timeout)
                else:
                    response = opener.open(req, timeout=timeout)
                if redirect_url:
                    return response.url
                content_encoding = response.info().get('Content-Encoding')
                try:
                    if content_encoding == 'gzip':
                        with gzip.open(response, 'rt', encoding=content_conding) as gzipped:
                            resp_str = gzipped.read()
                    else:
                        resp_str = response.read().decode(content_conding)
                finally:
                    response.close()

            except urllib.error.HTTPError as e:
                if e.code == 400:
                    resp_str = e.read().decode(content_conding)
                else:
                    raise
            except urllib.error.URLError as e:
                print(f"URL Error: {e}")
                raise
            except Exception as e:
                print(f"An error occurred: {e}")
                raise

    except Exception as e:
        resp_str = str(e)

    return resp_str

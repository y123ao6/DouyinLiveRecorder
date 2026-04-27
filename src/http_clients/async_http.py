# -*- coding: utf-8 -*-
import httpx
from typing import Dict, Any
from .. import utils
from ..logger import logger

OptionalStr = str | None
OptionalDict = Dict[str, Any] | None

_httpx_limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)


async def async_req(
        url: str,
        proxy_addr: OptionalStr = None,
        headers: OptionalDict = None,
        data: Any = None,
        json_data: dict | list | None = None,
        timeout: int = 20,
        redirect_url: bool = False,
        return_cookies: bool = False,
        include_cookies: bool = False,
        verify: bool = False,
        http2: bool = True
) -> str | dict[str, str] | tuple[str, dict[str, str]]:
    if headers is None:
        headers = {}
    proxy_addr = utils.handle_proxy_addr(proxy_addr)
    
    try:
        async with httpx.AsyncClient(
            proxy=proxy_addr,
            timeout=timeout,
            verify=verify,
            http2=http2,
            limits=_httpx_limits
        ) as client:
            if data or json_data:
                response = await client.post(
                    url, 
                    data=data, 
                    json=json_data, 
                    headers=headers,
                    follow_redirects=True
                )
            else:
                response = await client.get(url, headers=headers, follow_redirects=True)
            
            response.raise_for_status()

            if redirect_url:
                return str(response.url)
            elif return_cookies:
                cookies_dict = {name: value for name, value in response.cookies.items()}
                return (response.text, cookies_dict) if include_cookies else cookies_dict
            else:
                return response.text
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP status error for {url}: {e.response.status_code} - {e}")
        raise
    except httpx.RequestError as e:
        logger.error(f"Request error for {url}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error for {url}: {e}")
        raise


async def get_response_status(url: str, proxy_addr: OptionalStr = None, headers: OptionalDict = None,
                              timeout: int = 10, verify: bool = False, http2: bool = False) -> bool:

    try:
        proxy_addr = utils.handle_proxy_addr(proxy_addr)
        async with httpx.AsyncClient(
            proxy=proxy_addr,
            timeout=timeout,
            verify=verify,
            http2=http2,
            limits=_httpx_limits
        ) as client:
            response = await client.head(url, headers=headers, follow_redirects=True)
            return 200 <= response.status_code < 300
    except httpx.HTTPError as e:
        logger.debug(f"HTTP error checking {url}: {e}")
    except Exception as e:
        logger.debug(f"Error checking {url}: {e}")
    return False

# -*- encoding: utf-8 -*-
from typing import Dict, List, Optional

from .base_adapter import PlatformAdapter


class AdapterFactory:
    _adapters: List[PlatformAdapter] = []

    @classmethod
    def register(cls, adapter: PlatformAdapter) -> None:
        cls._adapters.append(adapter)

    @classmethod
    def get_adapter(cls, url: str) -> Optional[PlatformAdapter]:
        for adapter in cls._adapters:
            if adapter.supports_url(url):
                return adapter
        return None

    @classmethod
    def get_all_adapters(cls) -> List[PlatformAdapter]:
        return list(cls._adapters)

    @classmethod
    def clear(cls) -> None:
        cls._adapters.clear()

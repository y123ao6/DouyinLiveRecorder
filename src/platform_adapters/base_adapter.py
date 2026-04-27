# -*- encoding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import Dict, Optional


class PlatformAdapter(ABC):
    @abstractmethod
    def get_platform_name(self) -> str:
        pass

    @abstractmethod
    def supports_url(self, url: str) -> bool:
        pass

    @abstractmethod
    def get_stream_info(
        self,
        url: str,
        quality: str,
        proxy: Optional[str] = None,
        cookies: str = '',
        **kwargs
    ) -> Dict:
        pass

    def needs_proxy(self) -> bool:
        return False

    def get_record_headers(self, url: str) -> Optional[str]:
        return None

    def is_flv_preferred(self) -> bool:
        return False

    def is_only_flv(self) -> bool:
        return False

    def is_only_audio(self) -> bool:
        return False

    def use_http_recording(self) -> bool:
        return False

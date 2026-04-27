# -*- encoding: utf-8 -*-
import datetime
import threading
from dataclasses import dataclass, field
from typing import Set, Dict, List, Optional


@dataclass
class RecordingInfo:
    start_time: datetime.datetime
    quality: str


class StateManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._recording: Set[str] = set()
        self._error_count = 0
        self._pre_max_request = 10
        self._max_request = 10
        self._max_request_lock = threading.Lock()
        self._error_window: List[int] = []
        self._error_window_size = 10
        self._error_threshold = 5
        self._monitoring_count = 0
        self._running_urls: List[str] = []
        self._url_comments: List[str] = []
        self._recording_info: Dict[str, RecordingInfo] = {}
        self._exit_recording = False
        self._first_start = True
        self._first_run = True
        self._not_record_list: List[str] = []
        self._need_update_line_list: List[str] = []
        self._url_tuples_list: List[tuple] = []
        self._semaphore: Optional[threading.Semaphore] = None

    @property
    def recording(self) -> Set[str]:
        return self._recording

    @property
    def error_count(self) -> int:
        with self._max_request_lock:
            return self._error_count

    @property
    def max_request(self) -> int:
        with self._max_request_lock:
            return self._max_request

    @max_request.setter
    def max_request(self, value: int) -> None:
        with self._max_request_lock:
            self._max_request = value

    @property
    def pre_max_request(self) -> int:
        with self._max_request_lock:
            return self._pre_max_request

    @pre_max_request.setter
    def pre_max_request(self, value: int) -> None:
        with self._max_request_lock:
            self._pre_max_request = value

    @property
    def error_window(self) -> List[int]:
        with self._max_request_lock:
            return self._error_window

    @property
    def monitoring(self) -> int:
        with self._lock:
            return self._monitoring_count

    @property
    def running_list(self) -> List[str]:
        return self._running_urls

    @property
    def url_comments(self) -> List[str]:
        return self._url_comments

    @property
    def recording_time_list(self) -> Dict[str, RecordingInfo]:
        return self._recording_info

    @property
    def exit_recording(self) -> bool:
        return self._exit_recording

    @exit_recording.setter
    def exit_recording(self, value: bool) -> None:
        self._exit_recording = value

    @property
    def first_start(self) -> bool:
        return self._first_start

    @first_start.setter
    def first_start(self, value: bool) -> None:
        self._first_start = value

    @property
    def first_run(self) -> bool:
        return self._first_run

    @first_run.setter
    def first_run(self, value: bool) -> None:
        self._first_run = value

    @property
    def not_record_list(self) -> List[str]:
        return self._not_record_list

    @property
    def need_update_line_list(self) -> List[str]:
        return self._need_update_line_list

    @property
    def url_tuples_list(self) -> List[tuple]:
        return self._url_tuples_list

    @property
    def semaphore(self) -> Optional[threading.Semaphore]:
        return self._semaphore

    @semaphore.setter
    def semaphore(self, value: threading.Semaphore) -> None:
        self._semaphore = value

    def add_recording(self, name: str, quality: str) -> None:
        with self._lock:
            self._recording.add(name)
            self._recording_info[name] = RecordingInfo(
                start_time=datetime.datetime.now(),
                quality=quality
            )

    def remove_recording(self, name: str) -> None:
        with self._lock:
            self._recording.discard(name)
            self._recording_info.pop(name, None)

    def increment_error(self) -> None:
        with self._max_request_lock:
            self._error_count += 1

    def reset_error_count(self) -> None:
        with self._max_request_lock:
            self._error_count = 0

    def append_error_window(self, value: int) -> None:
        with self._max_request_lock:
            self._error_window.append(value)
            if len(self._error_window) > self._error_window_size:
                self._error_window.pop(0)

    def increment_monitoring(self) -> None:
        with self._lock:
            self._monitoring_count += 1

    def decrement_monitoring(self) -> None:
        with self._lock:
            self._monitoring_count -= 1

    def add_running_url(self, url: str) -> None:
        with self._lock:
            if url not in self._running_urls:
                self._running_urls.append(url)

    def remove_running_url(self, url: str) -> None:
        with self._lock:
            if url in self._running_urls:
                self._running_urls.remove(url)

    def add_url_comment(self, url: str) -> None:
        with self._lock:
            if url not in self._url_comments:
                self._url_comments.append(url)

    def remove_url_comment(self, url: str) -> None:
        with self._lock:
            if url in self._url_comments:
                self._url_comments.remove(url)

    def clear_record_info(self, record_name: str, record_url: str) -> None:
        with self._lock:
            self._recording.discard(record_name)
            self._recording_info.pop(record_name, None)
            if record_url in self._url_comments and record_url in self._running_urls:
                self._running_urls.remove(record_url)
                self._monitoring_count -= 1

    def get_no_repeat_recording(self) -> List[str]:
        with self._lock:
            return list(set(self._recording))


state_manager = StateManager()

# -*- encoding: utf-8 -*-
import datetime
import os
import re
import shutil
import threading
from pathlib import Path
from typing import List, Optional, Tuple

from src.utils import logger

_TEXT_ENCODING = 'utf-8-sig'

_PLATFORM_HOST = [
    'live.douyin.com', 'v.douyin.com', 'www.douyin.com',
    'live.kuaishou.com', 'www.huya.com', 'www.douyu.com',
    'www.yy.com', 'live.bilibili.com', 'www.redelight.cn',
    'www.xiaohongshu.com', 'xhslink.com', 'www.bigo.tv',
    'slink.bigovideo.tv', 'app.blued.cn', 'cc.163.com',
    'qiandurebo.com', 'fm.missevan.com', 'look.163.com',
    'twitcasting.tv', 'live.baidu.com', 'weibo.com',
    'fanxing.kugou.com', 'fanxing2.kugou.com', 'mfanxing.kugou.com',
    'www.huajiao.com', 'www.7u66.com', 'wap.7u66.com',
    'live.acfun.cn', 'm.acfun.cn', 'live.tlclw.com',
    'wap.tlclw.com', 'live.ybw1666.com', 'wap.ybw1666.com',
    'www.inke.cn', 'www.zhihu.com', 'www.haixiutv.com',
    "h5webcdnp.vvxqiu.com", "17.live", 'www.lang.live',
    "m.pp.weimipopo.com", "v.6.cn", "m.6.cn",
    'www.lehaitv.com', 'h.catshow168.com', 'e.tb.cn',
    'm.tb.cn', 'tbzb.taobao.com', 'huodong.m.taobao.com',
    '3.cn', 'eco.m.jd.com', 'www.miguvideo.com',
    'm.miguvideo.com', 'show.lailianjie.com', 'www.imkktv.com',
    'www.picarto.tv', 'www.tiktok.com',
    'play.sooplive.co.kr', 'm.sooplive.co.kr',
    'www.sooplive.com', 'm.sooplive.com',
    'www.pandalive.co.kr', 'www.winktv.co.kr',
    'www.flextv.co.kr', 'www.ttinglive.com',
    'www.popkontv.com', 'www.twitch.tv',
    'www.liveme.com', 'www.showroom-live.com',
    'chzzk.naver.com', 'm.chzzk.naver.com',
    'live.shopee.', '.shp.ee', 'www.youtube.com',
    'youtu.be', 'www.faceit.com',
]

_CLEAN_URL_HOST_LIST = (
    "live.douyin.com", "live.bilibili.com", "www.huajiao.com",
    "www.zhihu.com", "www.huya.com", "chzzk.naver.com",
    "www.liveme.com", "www.haixiutv.com", "v.6.cn", "m.6.cn",
    'www.lehaitv.com',
)

_file_update_lock = threading.Lock()


def _contains_url(string: str) -> bool:
    pattern = r"(https?://)?(www\.)?[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+(:\d+)?(/.*)?"
    return re.search(pattern, string) is not None


class FileManager:
    def __init__(
        self,
        config_file: str,
        url_config_file: str,
        backup_dir_path: str,
        default_video_quality: str = '原画',
    ):
        self.config_file = config_file
        self.url_config_file = url_config_file
        self.backup_dir = backup_dir_path
        self.default_video_quality = default_video_quality
        self._ini_url_content = ''

    def update_file(
        self,
        file_path: str,
        old_str: str,
        new_str: str,
        start_str: Optional[str] = None,
    ) -> Optional[str]:
        if old_str == new_str and start_str is None:
            return old_str
        with _file_update_lock:
            file_data = []
            with open(file_path, "r", encoding=_TEXT_ENCODING) as f:
                try:
                    for text_line in f:
                        if old_str in text_line:
                            text_line = text_line.replace(old_str, new_str)
                            if start_str:
                                text_line = f'{start_str}{text_line}'
                        if text_line not in file_data:
                            file_data.append(text_line)
                except RuntimeError as e:
                    logger.error(f"错误信息: {e}")
                    if self._ini_url_content:
                        with open(file_path, "w", encoding=_TEXT_ENCODING) as f2:
                            f2.write(self._ini_url_content)
                        return old_str
            if file_data:
                with open(file_path, "w", encoding=_TEXT_ENCODING) as f:
                    f.write(''.join(file_data))
            return new_str

    @staticmethod
    def delete_line(file_path: str, del_line: str, delete_all: bool = False) -> None:
        with _file_update_lock:
            with open(file_path, 'r+', encoding=_TEXT_ENCODING) as f:
                lines = f.readlines()
                f.seek(0)
                f.truncate()
                skip_line = False
                for txt_line in lines:
                    if del_line == txt_line:
                        if delete_all or not skip_line:
                            skip_line = True
                            continue
                    else:
                        skip_line = False
                    f.write(txt_line)

    def backup_file(self, file_path: str, limit_counts: int = 6) -> None:
        try:
            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir)

            timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            backup_file_name = os.path.basename(file_path) + '_' + timestamp
            backup_file_path = os.path.join(self.backup_dir, backup_file_name).replace("\\", "/")
            shutil.copy2(file_path, backup_file_path)

            files = os.listdir(self.backup_dir)
            _files = [f for f in files if f.startswith(os.path.basename(file_path))]
            _files.sort(key=lambda x: os.path.getmtime(os.path.join(self.backup_dir, x)))

            while len(_files) > limit_counts:
                oldest_file = _files[0]
                os.remove(os.path.join(self.backup_dir, oldest_file))
                _files = _files[1:]

        except Exception as e:
            logger.error(f'\r备份配置文件 {file_path} 失败：{str(e)}')

    def backup_file_start(self) -> None:
        config_md5 = ''
        url_config_md5 = ''
        from src.utils import check_md5

        while True:
            try:
                if os.path.exists(self.config_file):
                    new_config_md5 = check_md5(self.config_file)
                    if new_config_md5 != config_md5:
                        self.backup_file(self.config_file)
                        config_md5 = new_config_md5

                if os.path.exists(self.url_config_file):
                    new_url_config_md5 = check_md5(self.url_config_file)
                    if new_url_config_md5 != url_config_md5:
                        self.backup_file(self.url_config_file)
                        url_config_md5 = new_url_config_md5
                time.sleep(600)
            except Exception as e:
                logger.error(f"备份配置文件失败, 错误信息: {e}")

    def parse_url_config(
        self,
        url_comments: List[str],
        running_list: List[str],
        need_update_line_list: List[str],
    ) -> Tuple[List[tuple], List[str]]:
        url_tuples_list = []
        new_url_comments = list(url_comments)

        if not os.path.isfile(self.url_config_file):
            return url_tuples_list, new_url_comments

        with open(self.url_config_file, 'r', encoding=_TEXT_ENCODING, errors='ignore') as file:
            self._ini_url_content = file.read().strip()

        if not self._ini_url_content.strip():
            return url_tuples_list, new_url_comments

        line_list = []
        url_line_list = []
        seen_urls = set()

        with open(self.url_config_file, "r", encoding=_TEXT_ENCODING, errors='ignore') as file:
            for origin_line in file:
                if origin_line in line_list:
                    self.delete_line(self.url_config_file, origin_line)
                line_list.append(origin_line)
                line = origin_line.strip()
                if len(line) < 18:
                    continue

                line_spilt = line.split('主播: ')
                if len(line_spilt) > 2:
                    line = self.update_file(
                        self.url_config_file, line,
                        f'{line_spilt[0]}主播: {line_spilt[-1]}') or line

                is_comment_line = line.startswith("#")
                if is_comment_line:
                    line = line.lstrip('#')

                if re.search('[,，]', line):
                    split_line = re.split('[,，]', line)
                else:
                    split_line = [line, '']

                if len(split_line) == 1:
                    url = split_line[0]
                    quality, name = [self.default_video_quality, '']
                elif len(split_line) == 2:
                    if _contains_url(split_line[0]):
                        quality = self.default_video_quality
                        url, name = split_line
                    else:
                        quality, url = split_line
                        name = ''
                else:
                    quality, url, name = split_line

                if quality not in ("原画", "蓝光", "超清", "高清", "标清", "流畅"):
                    quality = '原画'

                if url not in url_line_list:
                    url_line_list.append(url)
                else:
                    self.delete_line(self.url_config_file, origin_line)

                url = 'https://' + url if '://' not in url else url
                url_host = url.split('/')[2]

                if 'live.shopee.' in url_host or '.shp.ee' in url_host:
                    url_host = 'live.shopee.' if 'live.shopee.' in url_host else '.shp.ee'

                if url_host in _PLATFORM_HOST or any(ext in url for ext in (".flv", ".m3u8")):
                    if url_host in _CLEAN_URL_HOST_LIST:
                        url = self.update_file(
                            self.url_config_file, old_str=url,
                            new_str=url.split('?')[0]) or url

                    if 'xiaohongshu' in url:
                        host_id = re.search('&host_id=(.*?)(?=&|$)', url)
                        if host_id:
                            new_url = url.split('?')[0] + f'?host_id={host_id.group(1)}'
                            url = self.update_file(
                                self.url_config_file, old_str=url,
                                new_str=new_url) or url
                    seen_urls.add(url)
                    new_url_comments = [i for i in new_url_comments if url not in i]
                    if is_comment_line:
                        new_url_comments.append(url)
                    else:
                        new_line = (quality, url, name)
                        url_tuples_list.append(new_line)
                else:
                    if not origin_line.startswith('#'):
                        from src.utils import Color
                        color_obj = Color()
                        color_obj.print_colored(
                            f"\r{origin_line.strip()} 本行包含未知链接.此条跳过", color_obj.YELLOW)
                        self.update_file(
                            self.url_config_file, old_str=origin_line,
                            new_str=origin_line, start_str='#')

        while len(need_update_line_list):
            a = need_update_line_list.pop()
            replace_words = a.split('|')
            if replace_words[0] != replace_words[1]:
                if replace_words[1].startswith("#"):
                    start_with = '#'
                    new_word = replace_words[1][1:]
                else:
                    start_with = None
                    new_word = replace_words[1]
                self.update_file(
                    self.url_config_file, old_str=replace_words[0],
                    new_str=new_word, start_str=start_with)

        running_snapshot = list(running_list)
        for running_url in running_snapshot:
            if running_url not in seen_urls and running_url not in new_url_comments:
                new_url_comments.append(running_url)

        return url_tuples_list, new_url_comments


import time

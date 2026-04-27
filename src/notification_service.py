# -*- encoding: utf-8 -*-
from src.config_manager import AppConfig
from src.utils import logger, Color

color_obj = Color()


class NotificationService:
    def __init__(self, app_config: AppConfig):
        self.config = app_config.push

    def push_message(self, record_name: str, live_url: str, content: str) -> None:
        from msg_push import dingtalk, xizhi, tg_bot, send_email, bark, ntfy, pushplus

        msg_title = self.config.push_message_title.strip() or "直播间状态更新通知"
        
        def safe_tg_bot():
            try:
                chat_id = int(self.config.tg_chat_id) if self.config.tg_chat_id else 0
                return tg_bot(chat_id, self.config.tg_token, content)
            except (ValueError, TypeError):
                return {"success": [], "error": [1]}
        
        push_functions = {
            '微信': lambda: xizhi(self.config.xizhi_api_url, msg_title, content),
            '钉钉': lambda: dingtalk(
                self.config.dingtalk_api_url, content,
                self.config.dingtalk_phone_num, self.config.dingtalk_is_atall
            ),
            '邮箱': lambda: send_email(
                self.config.email_host, self.config.login_email,
                self.config.email_password, self.config.sender_email,
                self.config.sender_name, self.config.to_email,
                msg_title, content, self.config.smtp_port,
                self.config.open_smtp_ssl
            ),
            'TG': safe_tg_bot,
            'BARK': lambda: bark(
                self.config.bark_msg_api, title=msg_title, content=content,
                level=self.config.bark_msg_level, sound=self.config.bark_msg_ring
            ),
            'NTFY': lambda: ntfy(
                self.config.ntfy_api, title=msg_title, content=content,
                tags=self.config.ntfy_tags, action_url=live_url,
                email=self.config.ntfy_email
            ),
            'PUSHPLUS': lambda: pushplus(self.config.pushplus_token, msg_title, content),
        }

        for platform, func in push_functions.items():
            if platform in self.config.live_status_push.upper():
                try:
                    result = func()
                    logger.info(
                        f'提示信息：已经将[{record_name}]直播状态消息推送至你的{platform},'
                        f' 成功{len(result["success"])}, 失败{len(result["error"])}')
                except Exception as e:
                    color_obj.print_colored(f"直播消息推送到{platform}失败: {e}", color_obj.RED)

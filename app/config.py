"""
配置管理模块 - 从环境变量加载配置
"""
from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """应用配置，从环境变量或 .env 文件加载"""

    # ---- Lark / 飞书配置 ----
    lark_webhook_url: Optional[str] = None
    # 多个Webhook URL，逗号分隔
    lark_webhook_urls: Optional[str] = None

    # ---- AI 配置 (千问/Qwen) ----
    dashscope_api_key: Optional[str] = None
    ai_model: str = "qwen-plus"
    ai_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # ---- 新闻 API Keys ----
    news_api_key: Optional[str] = None
    finnhub_api_key: Optional[str] = None
    alpha_vantage_api_key: Optional[str] = None

    # ---- 数据库配置 ----
    database_url: str = "sqlite:///./stock_news.db"

    # ---- 定时任务配置 ----
    push_schedule_hour: int = 8
    push_schedule_minute: int = 0
    push_timezone: str = "Asia/Shanghai"

    # ---- 应用配置 ----
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    secret_key: str = "change-this-secret-key"
    log_level: str = "INFO"
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def get_lark_webhook_list(self) -> List[str]:
        """获取所有Lark Webhook URL列表"""
        urls = []
        if self.lark_webhook_url:
            urls.append(self.lark_webhook_url)
        if self.lark_webhook_urls:
            for url in self.lark_webhook_urls.split(","):
                url = url.strip()
                if url and url not in urls:
                    urls.append(url)
        return urls


# 全局配置实例
settings = Settings()

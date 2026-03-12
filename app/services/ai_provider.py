"""
AI 服务提供者模块 - Provider 模式
支持千问(Qwen) via DashScope OpenAI兼容API，预留其他Provider扩展接口
"""
import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseAIProvider(ABC):
    """AI Provider 基类 - 定义接口规范"""

    @abstractmethod
    def chat_completion(self, messages: list, **kwargs) -> str:
        """调用聊天补全接口"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查服务是否可用"""
        pass


class QwenProvider(BaseAIProvider):
    """
    千问(Qwen) AI Provider
    使用 DashScope OpenAI 兼容模式调用
    """

    def __init__(self, api_key: str, model: str = "qwen-plus", base_url: str = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self._client = None

    def _get_client(self):
        """懒加载 OpenAI 客户端"""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
            except ImportError:
                logger.error("openai 包未安装，请运行: pip install openai")
                raise
        return self._client

    def is_available(self) -> bool:
        """检查 API Key 是否已配置"""
        return bool(self.api_key and self.api_key != "your-dashscope-api-key")

    def chat_completion(self, messages: list, **kwargs) -> str:
        """
        调用千问聊天补全接口
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            **kwargs: 额外参数，如 temperature, max_tokens 等
        
        Returns:
            AI 回复内容
        """
        if not self.is_available():
            raise ValueError("DASHSCOPE_API_KEY 未配置，请在 .env 文件中设置")

        client = self._get_client()
        try:
            response = client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000),
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"千问API调用失败: {e}")
            raise


class AIProvider:
    """
    AI Provider 管理器 - 统一入口
    支持动态切换不同的AI服务提供商
    """

    def __init__(self):
        self._providers: Dict[str, BaseAIProvider] = {}
        self._default_provider: Optional[str] = None
        self._initialize_from_settings()

    def _initialize_from_settings(self):
        """从应用配置初始化默认Provider"""
        try:
            from app.config import settings
            if settings.dashscope_api_key:
                qwen = QwenProvider(
                    api_key=settings.dashscope_api_key,
                    model=settings.ai_model,
                    base_url=settings.ai_base_url,
                )
                self.register_provider("qwen", qwen)
                self._default_provider = "qwen"
                logger.info(f"千问AI Provider 已初始化，模型: {settings.ai_model}")
        except Exception as e:
            logger.warning(f"AI Provider 初始化失败: {e}")

    def register_provider(self, name: str, provider: BaseAIProvider):
        """注册 AI Provider"""
        self._providers[name] = provider
        logger.info(f"已注册 AI Provider: {name}")

    def get_provider(self, name: Optional[str] = None) -> Optional[BaseAIProvider]:
        """获取指定 Provider，默认返回默认 Provider"""
        provider_name = name or self._default_provider
        if provider_name:
            return self._providers.get(provider_name)
        return None

    def is_available(self, name: Optional[str] = None) -> bool:
        """检查指定 Provider 是否可用"""
        provider = self.get_provider(name)
        return provider is not None and provider.is_available()

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        使用 AI 进行情感分析
        
        Returns:
            {"label": "positive/negative/neutral", "score": 0.85, "reason": "..."}
        """
        provider = self.get_provider()
        if not provider or not provider.is_available():
            raise ValueError("AI Provider 不可用，请检查 API Key 配置")

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个金融情感分析专家。请对给定的文本进行情感分析，"
                    "返回JSON格式: {\"label\": \"positive/negative/neutral\", "
                    "\"score\": 0-1的浮点数, \"reason\": \"简要原因\"}"
                )
            },
            {
                "role": "user",
                "content": f"请分析以下文本的情感倾向:\n\n{text}"
            }
        ]

        try:
            response = provider.chat_completion(messages, temperature=0.3, max_tokens=500)
            # 尝试解析JSON响应
            import json
            # 提取JSON部分（如果有其他文字包裹）
            import re
            json_match = re.search(r'\{[^{}]+\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result
            else:
                return {"label": "neutral", "score": 0.5, "reason": response}
        except Exception as e:
            logger.error(f"AI情感分析失败: {e}")
            raise

    def summarize_news(self, articles: list) -> str:
        """
        使用 AI 生成新闻摘要报告
        
        Args:
            articles: 新闻文章列表
        
        Returns:
            摘要报告文本
        """
        provider = self.get_provider()
        if not provider or not provider.is_available():
            raise ValueError("AI Provider 不可用，请检查 API Key 配置")

        # 构建新闻内容
        news_text = "\n\n".join([
            f"标题: {a.get('title', '')}\n摘要: {a.get('content', '')[:200]}"
            for a in articles[:10]  # 最多取10条
        ])

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个专业的金融分析师。请对以下全球股票新闻进行综合分析，"
                    "生成一份简洁的中文日报摘要（300字以内），包含:\n"
                    "1. 今日市场核心动向\n"
                    "2. 重要新闻要点（3-5条）\n"
                    "3. 市场情绪判断\n"
                    "语言要专业但易懂。"
                )
            },
            {
                "role": "user",
                "content": f"以下是今日全球股票相关新闻:\n\n{news_text}"
            }
        ]

        return provider.chat_completion(messages, temperature=0.5, max_tokens=1500)

    def generate_investment_advice(self, analysis: Dict[str, Any]) -> str:
        """
        生成投资建议（含免责声明）
        
        Args:
            analysis: 分析数据
        
        Returns:
            投资建议文本
        """
        provider = self.get_provider()
        if not provider or not provider.is_available():
            raise ValueError("AI Provider 不可用，请检查 API Key 配置")

        content = str(analysis)
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个金融分析助手。基于给定的市场数据和情感分析结果，"
                    "提供参考性的市场观点。注意：必须在回复末尾包含免责声明："
                    "「⚠️ 以上内容仅供参考，不构成投资建议，投资有风险，入市需谨慎。」"
                )
            },
            {
                "role": "user",
                "content": f"基于以下分析数据，提供市场观点:\n\n{content}"
            }
        ]

        return provider.chat_completion(messages, temperature=0.6, max_tokens=1000)

    def custom_analyze(self, content: str, prompt: str) -> str:
        """
        自定义 Prompt 分析
        
        Args:
            content: 分析内容
            prompt: 自定义提示词
        
        Returns:
            分析结果
        """
        provider = self.get_provider()
        if not provider or not provider.is_available():
            raise ValueError("AI Provider 不可用，请检查 API Key 配置")

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ]

        return provider.chat_completion(messages)


# 全局 AI Provider 实例
ai_provider = AIProvider()

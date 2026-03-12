"""
AI Provider 服务测试
"""
import pytest
from unittest.mock import patch, MagicMock


def test_qwen_provider_not_available_without_key():
    """测试没有 API Key 时 Provider 不可用"""
    from app.services.ai_provider import QwenProvider
    provider = QwenProvider(api_key="", model="qwen-plus")
    assert not provider.is_available()


def test_qwen_provider_not_available_with_placeholder():
    """测试使用占位符 Key 时不可用"""
    from app.services.ai_provider import QwenProvider
    provider = QwenProvider(api_key="your-dashscope-api-key", model="qwen-plus")
    assert not provider.is_available()


def test_qwen_provider_available_with_real_key():
    """测试有真实 API Key 时可用"""
    from app.services.ai_provider import QwenProvider
    provider = QwenProvider(api_key="sk-test-real-key-123", model="qwen-plus")
    assert provider.is_available()


def test_ai_provider_manager_initialization():
    """测试 AI Provider 管理器初始化"""
    from app.services.ai_provider import AIProvider
    manager = AIProvider()
    # 即使没有 API Key，也应该能正常初始化
    assert manager is not None


def test_ai_provider_register_and_get():
    """测试注册和获取 Provider"""
    from app.services.ai_provider import AIProvider, QwenProvider
    manager = AIProvider()
    provider = QwenProvider(api_key="test-key-12345", model="qwen-turbo")
    manager.register_provider("test_qwen", provider)
    retrieved = manager.get_provider("test_qwen")
    assert retrieved is provider


def test_ai_provider_chat_completion():
    """测试 AI 聊天补全调用（Mock）"""
    from app.services.ai_provider import QwenProvider

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "这是AI的回复"
    mock_client.chat.completions.create.return_value = mock_response

    provider = QwenProvider(api_key="sk-test-real-key-123", model="qwen-plus")
    provider._client = mock_client  # 注入 mock 客户端

    result = provider.chat_completion([
        {"role": "user", "content": "测试消息"}
    ])
    assert result == "这是AI的回复"


def test_ai_provider_sentiment_analysis_mock():
    """测试 AI 情感分析（Mock）"""
    from app.services.ai_provider import AIProvider, QwenProvider

    mock_provider = MagicMock(spec=QwenProvider)
    mock_provider.is_available.return_value = True
    mock_provider.chat_completion.return_value = '{"label": "positive", "score": 0.85, "reason": "文本积极"}'

    manager = AIProvider()
    manager.register_provider("mock", mock_provider)
    manager._default_provider = "mock"

    result = manager.analyze_sentiment("今日股市大涨，盈利超预期")
    assert result["label"] == "positive"
    assert result["score"] == 0.85


def test_ai_provider_not_available_raises():
    """测试 Provider 不可用时抛出异常"""
    from app.services.ai_provider import AIProvider
    manager = AIProvider()
    # 确保没有可用的 Provider
    manager._providers = {}
    manager._default_provider = None

    with pytest.raises(ValueError, match="AI Provider 不可用"):
        manager.analyze_sentiment("测试文本")

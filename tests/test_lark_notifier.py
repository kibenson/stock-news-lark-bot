"""
Lark 推送服务测试
"""
import pytest
from unittest.mock import patch, MagicMock


def test_send_text_message_no_webhook():
    """测试未配置Webhook时的处理"""
    from app.services.lark_notifier import _send_to_lark
    with patch('app.services.lark_notifier.settings') as mock_settings:
        mock_settings.get_lark_webhook_list.return_value = []
        result = _send_to_lark({"msg_type": "text", "content": {"text": "test"}})
    assert result["code"] == -1
    assert "未配置" in result["msg"]


def test_send_text_message_success():
    """测试成功发送文本消息"""
    from app.services.lark_notifier import send_text_message
    mock_response = MagicMock()
    mock_response.json.return_value = {"code": 0, "msg": "success"}
    mock_response.raise_for_status = MagicMock()

    with patch('app.services.lark_notifier.requests.post', return_value=mock_response):
        result = send_text_message(
            "测试消息",
            webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/test-token"
        )

    assert result["code"] == 0


def test_send_card_message():
    """测试发送卡片消息"""
    from app.services.lark_notifier import send_card_message
    mock_response = MagicMock()
    mock_response.json.return_value = {"code": 0, "msg": "success"}
    mock_response.raise_for_status = MagicMock()

    with patch('app.services.lark_notifier.requests.post', return_value=mock_response) as mock_post:
        result = send_card_message(
            title="测试标题",
            content="**测试内容**",
            color="blue",
            webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/test-token"
        )

    assert result["code"] == 0
    # 验证发送的是 interactive 类型
    call_kwargs = mock_post.call_args
    assert call_kwargs[1]['json']['msg_type'] == 'interactive'


def test_send_post_message():
    """测试发送富文本消息"""
    from app.services.lark_notifier import send_post_message
    mock_response = MagicMock()
    mock_response.json.return_value = {"code": 0, "msg": "success"}
    mock_response.raise_for_status = MagicMock()

    content_lines = [
        [{"tag": "text", "text": "这是正文内容"}],
        [{"tag": "a", "text": "点击链接", "href": "https://example.com"}],
    ]

    with patch('app.services.lark_notifier.requests.post', return_value=mock_response) as mock_post:
        result = send_post_message(
            title="富文本标题",
            content_lines=content_lines,
            webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/test-token"
        )

    assert result["code"] == 0
    call_kwargs = mock_post.call_args
    assert call_kwargs[1]['json']['msg_type'] == 'post'


def test_send_request_timeout():
    """测试请求超时处理"""
    import requests as req
    from app.services.lark_notifier import send_text_message

    with patch('app.services.lark_notifier.requests.post', side_effect=req.exceptions.Timeout()):
        result = send_text_message(
            "测试",
            webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/test-token"
        )

    assert result["code"] == -1
    assert "超时" in result["msg"]


def test_send_daily_report_no_webhook():
    """测试没有配置Webhook时每日报告推送"""
    from app.services.lark_notifier import send_daily_report
    with patch('app.services.lark_notifier.settings') as mock_settings:
        mock_settings.get_lark_webhook_list.return_value = []
        results = send_daily_report(articles=[])
    assert len(results) == 1
    assert results[0]["code"] == -1

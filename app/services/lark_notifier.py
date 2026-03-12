"""
Lark / 飞书 Webhook 推送服务
支持文本、富文本(post)和交互式卡片(interactive)消息
"""
import logging
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)

LARK_WEBHOOK_BASE = "https://open.feishu.cn/open-apis/bot/v2/hook/"


def send_text_message(text: str, webhook_url: Optional[str] = None) -> Dict[str, Any]:
    """
    发送纯文本消息
    
    Args:
        text: 消息文本
        webhook_url: 指定的 Webhook URL，为空则使用配置的默认URL
    
    Returns:
        Lark API 响应
    """
    payload = {
        "msg_type": "text",
        "content": {"text": text}
    }
    return _send_to_lark(payload, webhook_url)


def send_post_message(
    title: str,
    content_lines: List[List[Dict]],
    webhook_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    发送富文本消息（post类型）
    
    Args:
        title: 消息标题
        content_lines: 内容行，每行为标签列表
        webhook_url: 指定的 Webhook URL
    
    Returns:
        Lark API 响应
    """
    payload = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": title,
                    "content": content_lines
                }
            }
        }
    }
    return _send_to_lark(payload, webhook_url)


def send_card_message(
    title: str,
    content: str,
    color: str = "blue",
    actions: Optional[List[Dict]] = None,
    webhook_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    发送交互式卡片消息（interactive类型）
    
    Args:
        title: 卡片标题
        content: 卡片内容（支持 Markdown）
        color: 卡片颜色标识 blue/green/red/yellow/purple
        actions: 按钮动作列表
        webhook_url: 指定的 Webhook URL
    
    Returns:
        Lark API 响应
    """
    # 卡片颜色映射
    color_map = {
        "blue": "blue",
        "green": "green",
        "red": "red",
        "yellow": "yellow",
        "purple": "purple",
        "orange": "orange",
        "carmine": "carmine",
        "violet": "violet",
        "wathet": "wathet",
        "turquoise": "turquoise",
    }
    header_color = color_map.get(color, "blue")

    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": title},
            "template": header_color
        },
        "elements": [
            {
                "tag": "div",
                "text": {"tag": "lark_md", "content": content}
            }
        ]
    }

    # 添加按钮
    if actions:
        action_elements = []
        for action in actions:
            action_elements.append({
                "tag": "button",
                "text": {"tag": "plain_text", "content": action.get("text", "点击")},
                "type": action.get("type", "default"),
                "url": action.get("url", ""),
            })
        if action_elements:
            card["elements"].append({
                "tag": "action",
                "actions": action_elements
            })

    payload = {
        "msg_type": "interactive",
        "card": card
    }
    return _send_to_lark(payload, webhook_url)


def send_daily_report(
    articles: List[Dict[str, Any]],
    sentiment_summary: Optional[Dict[str, Any]] = None,
    ai_summary: Optional[str] = None,
    webhook_url: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    发送每日股票新闻报告到 Lark 群
    
    Args:
        articles: 新闻文章列表
        sentiment_summary: 情感分析摘要
        ai_summary: AI生成的摘要
        webhook_url: 目标 Webhook URL，为空则推送到所有配置的群
    
    Returns:
        所有 Webhook 的响应列表
    """
    now = datetime.now()
    date_str = now.strftime("%Y年%m月%d日")

    # ---- 构建卡片内容 ----
    content_parts = []

    # AI 摘要部分
    if ai_summary:
        content_parts.append(f"**🤖 AI智能摘要**\n{ai_summary}\n")
    else:
        content_parts.append(f"**📅 {date_str} 全球股票新闻日报**\n")

    # 情感分析摘要
    if sentiment_summary:
        pos = sentiment_summary.get("positive_count", 0)
        neg = sentiment_summary.get("negative_count", 0)
        neu = sentiment_summary.get("neutral_count", 0)
        score = sentiment_summary.get("overall_score", 0)
        emoji = "📈" if score > 0.1 else ("📉" if score < -0.1 else "➡️")
        content_parts.append(
            f"**{emoji} 市场情绪分析**\n"
            f"正面: {pos} | 负面: {neg} | 中性: {neu}\n"
            f"情感指数: {score:+.2f}\n"
        )

    # 重点新闻（最多展示8条）
    if articles:
        content_parts.append("**📰 今日重点新闻**\n")
        for i, article in enumerate(articles[:8], 1):
            title = article.get("title", "")[:100]
            source = article.get("source", "")
            url = article.get("url", "")
            sentiment_label = article.get("sentiment_label", "")

            # 情感图标
            sentiment_icon = {
                "positive": "🟢",
                "negative": "🔴",
                "neutral": "⚪"
            }.get(sentiment_label, "⚪")

            if url:
                content_parts.append(f"{i}. {sentiment_icon} [{title}]({url})\n   *来源: {source}*\n")
            else:
                content_parts.append(f"{i}. {sentiment_icon} {title}\n   *来源: {source}*\n")

    content_parts.append(f"\n*推送时间: {now.strftime('%H:%M:%S')} | 由 Stock News Bot 自动生成*")

    full_content = "\n".join(content_parts)

    # 确定卡片颜色（基于整体情感）
    if sentiment_summary:
        score = sentiment_summary.get("overall_score", 0)
        card_color = "green" if score > 0.1 else ("red" if score < -0.1 else "blue")
    else:
        card_color = "blue"

    # 确定推送目标
    if webhook_url:
        targets = [webhook_url]
    else:
        targets = settings.get_lark_webhook_list()
        if not targets:
            logger.warning("没有配置 Lark Webhook URL，请在 .env 中设置 LARK_WEBHOOK_URL")
            return [{"code": -1, "msg": "未配置 Webhook URL"}]

    # 发送到所有目标群
    responses = []
    for target_url in targets:
        response = send_card_message(
            title=f"📊 {date_str} 全球股票新闻日报",
            content=full_content,
            color=card_color,
            webhook_url=target_url
        )
        responses.append(response)

    return responses


def _send_to_lark(payload: Dict[str, Any], webhook_url: Optional[str] = None) -> Dict[str, Any]:
    """
    内部方法：发送消息到 Lark Webhook
    
    Args:
        payload: 消息 payload
        webhook_url: 目标 Webhook URL，为空则使用配置的默认URL
    
    Returns:
        Lark API 响应
    """
    # 确定 Webhook URL
    url = webhook_url
    if not url:
        urls = settings.get_lark_webhook_list()
        if urls:
            url = urls[0]

    if not url:
        logger.error("Lark Webhook URL 未配置")
        return {"code": -1, "msg": "Webhook URL 未配置"}

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        result = response.json()
        if result.get("code") == 0 or result.get("StatusCode") == 0:
            logger.info(f"Lark 消息发送成功: {url[:50]}...")
        else:
            logger.warning(f"Lark 消息发送返回异常: {result}")
        return result

    except requests.exceptions.Timeout:
        logger.error("Lark Webhook 请求超时")
        return {"code": -1, "msg": "请求超时"}
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Lark Webhook 连接失败: {e}")
        return {"code": -1, "msg": f"连接失败: {str(e)}"}
    except Exception as e:
        logger.error(f"Lark Webhook 发送异常: {e}")
        return {"code": -1, "msg": str(e)}

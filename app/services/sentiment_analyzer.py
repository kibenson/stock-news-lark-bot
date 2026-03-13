"""
情感分析服务模块
支持两种模式：本地规则分析 和 AI深度分析（调用千问API）
"""
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# ---- 本地情感分析关键词词库 ----
POSITIVE_KEYWORDS = [
    # 中文正面
    "上涨", "涨", "暴涨", "飙升", "创新高", "突破", "强劲", "增长", "盈利",
    "利好", "好消息", "乐观", "看涨", "买入", "推荐", "超预期", "亮眼",
    "强势", "反弹", "回升", "复苏", "繁荣", "扩张", "增持", "牛市",
    # 英文正面
    "surge", "rally", "gain", "rise", "bull", "buy", "upgrade", "outperform",
    "beat", "record", "growth", "profit", "positive", "strong", "recovery",
]

NEGATIVE_KEYWORDS = [
    # 中文负面
    "下跌", "跌", "暴跌", "崩盘", "亏损", "利空", "坏消息", "悲观", "看跌",
    "卖出", "减持", "低于预期", "裁员", "破产", "违约", "熊市", "清仓",
    "抛售", "大跌", "闪崩", "跳水", "套牢", "割肉",
    # 英文负面
    "plunge", "crash", "fall", "drop", "bear", "sell", "downgrade", "underperform",
    "miss", "loss", "negative", "weak", "recession", "layoff", "bankruptcy",
    "default", "decline",
]

# 情感强度修饰词
INTENSIFIERS = ["非常", "极度", "严重", "大幅", "急剧", "大", "超", "very", "extremely", "heavily"]
NEGATIONS = ["不", "没有", "未", "非", "no", "not", "never", "without"]


def local_sentiment_analysis(text: str) -> Dict[str, Any]:
    """
    本地基于关键词/规则的情感分析
    
    Args:
        text: 待分析文本
    
    Returns:
        {
            "label": "positive/negative/neutral",
            "score": float (-1.0 到 1.0),
            "confidence": float (0 到 1.0),
            "positive_keywords": [...],
            "negative_keywords": [...],
            "method": "local"
        }
    """
    if not text:
        return {"label": "neutral", "score": 0.0, "confidence": 0.5, "method": "local"}

    text_lower = text.lower()
    words = re.findall(r'\w+', text_lower)

    # 统计正负面词汇
    found_positive = []
    found_negative = []

    for kw in POSITIVE_KEYWORDS:
        if kw.lower() in text_lower:
            found_positive.append(kw)

    for kw in NEGATIVE_KEYWORDS:
        if kw.lower() in text_lower:
            found_negative.append(kw)

    pos_count = len(found_positive)
    neg_count = len(found_negative)
    total = pos_count + neg_count

    if total == 0:
        return {
            "label": "neutral",
            "score": 0.0,
            "confidence": 0.5,
            "positive_keywords": [],
            "negative_keywords": [],
            "method": "local"
        }

    # 计算情感分数 (-1.0 到 1.0)
    score = (pos_count - neg_count) / total
    confidence = min(1.0, total / 5.0)  # 关键词越多，置信度越高

    if score > 0.2:
        label = "positive"
    elif score < -0.2:
        label = "negative"
    else:
        label = "neutral"

    return {
        "label": label,
        "score": round(score, 3),
        "confidence": round(confidence, 3),
        "positive_keywords": found_positive[:5],
        "negative_keywords": found_negative[:5],
        "method": "local"
    }


def analyze_batch(texts: List[str], use_ai: bool = False) -> List[Dict[str, Any]]:
    """
    批量情感分析
    
    Args:
        texts: 文本列表
        use_ai: 是否使用AI分析
    
    Returns:
        情感分析结果列表
    """
    results = []
    for text in texts:
        result = analyze_text(text, use_ai=use_ai)
        results.append(result)
    return results


def analyze_text(text: str, use_ai: bool = False) -> Dict[str, Any]:
    """
    对单条文本进行情感分析
    
    Args:
        text: 待分析文本
        use_ai: 是否使用AI深度分析
    
    Returns:
        情感分析结果
    """
    if use_ai:
        try:
            from app.services.ai_provider import ai_provider
            if ai_provider.is_available():
                result = ai_provider.analyze_sentiment(text)
                result["method"] = "ai"
                return result
            else:
                logger.warning("AI Provider 不可用，降级为本地分析")
        except Exception as e:
            logger.warning(f"AI分析失败，降级为本地分析: {e}")

    # 使用本地规则分析
    return local_sentiment_analysis(text)


def generate_sentiment_report(
    items: List[Dict[str, Any]],
    target_type: str,
    target_name: Optional[str] = None,
    use_ai: bool = False
) -> Dict[str, Any]:
    """
    为一批内容生成情感分析报告
    
    Args:
        items: 内容列表，每项需包含 'content' 或 'title' 字段
        target_type: 分析目标类型 (news/user_post/keyword)
        target_name: 目标名称
        use_ai: 是否使用AI
    
    Returns:
        情感分析报告
    """
    if not items:
        return {
            "target_type": target_type,
            "target_name": target_name,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "overall_score": 0.0,
            "conclusion": "暂无数据",
            "details": [],
            "created_at": datetime.utcnow().isoformat()
        }

    # 分析每条内容
    analyzed = []
    for item in items:
        text = item.get("content") or item.get("title") or ""
        if text:
            result = analyze_text(text, use_ai=use_ai)
            result["source"] = item
            analyzed.append(result)

    # 统计
    positive_count = sum(1 for r in analyzed if r["label"] == "positive")
    negative_count = sum(1 for r in analyzed if r["label"] == "negative")
    neutral_count = sum(1 for r in analyzed if r["label"] == "neutral")
    total = len(analyzed)

    # 计算整体情感分数
    if total > 0:
        scores = [r.get("score", 0) for r in analyzed]
        overall_score = sum(scores) / len(scores)
    else:
        overall_score = 0.0

    # 生成结论
    conclusion = _generate_conclusion(
        positive_count, negative_count, neutral_count,
        overall_score, target_type, target_name
    )

    return {
        "target_type": target_type,
        "target_name": target_name,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count,
        "overall_score": round(overall_score, 3),
        "conclusion": conclusion,
        "analysis": {
            "total": total,
            "distribution": {
                "positive": f"{positive_count/total*100:.1f}%" if total > 0 else "0%",
                "negative": f"{negative_count/total*100:.1f}%" if total > 0 else "0%",
                "neutral": f"{neutral_count/total*100:.1f}%" if total > 0 else "0%",
            }
        },
        "created_at": datetime.utcnow().isoformat()
    }


def _generate_conclusion(
    positive: int, negative: int, neutral: int,
    score: float, target_type: str, target_name: Optional[str]
) -> str:
    """生成文字结论"""
    total = positive + negative + neutral
    if total == 0:
        return "暂无数据可供分析"

    name_str = f"「{target_name}」" if target_name else ""

    if score > 0.3:
        sentiment_desc = "整体情绪**偏正面**，市场情绪乐观"
    elif score < -0.3:
        sentiment_desc = "整体情绪**偏负面**，市场情绪谨慎"
    elif score > 0.1:
        sentiment_desc = "整体情绪**略偏正面**，市场情绪温和"
    elif score < -0.1:
        sentiment_desc = "整体情绪**略偏负面**，需关注风险"
    else:
        sentiment_desc = "整体情绪**中性**，市场情绪平稳"

    return (
        f"共分析 {total} 条{target_type}内容{name_str}，{sentiment_desc}。"
        f"正面: {positive}条({positive/total*100:.0f}%)，"
        f"负面: {negative}条({negative/total*100:.0f}%)，"
        f"中性: {neutral}条({neutral/total*100:.0f}%)。"
    )

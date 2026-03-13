"""
AI 分析 API 路由
"""
from fastapi import APIRouter, HTTPException
from app.schemas.schemas import AIAnalyzeRequest

router = APIRouter(prefix="/api/ai", tags=["AI分析"])


@router.post("/analyze", response_model=dict)
def ai_analyze(request: AIAnalyzeRequest):
    """
    AI 内容分析接口
    
    支持分析类型:
    - sentiment: 情感分析
    - summary: 内容摘要
    - advice: 投资建议（含免责声明）
    - custom: 自定义Prompt分析
    """
    from app.services.ai_provider import ai_provider

    if not ai_provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI 服务不可用，请检查 DASHSCOPE_API_KEY 配置"
        )

    try:
        analysis_type = request.analysis_type

        if analysis_type == "sentiment":
            result = ai_provider.analyze_sentiment(request.content)
            return {"type": "sentiment", "result": result}

        elif analysis_type == "summary":
            articles = [{"title": request.content, "content": ""}]
            result = ai_provider.summarize_news(articles)
            return {"type": "summary", "result": result}

        elif analysis_type == "advice":
            result = ai_provider.generate_investment_advice({"content": request.content})
            return {"type": "advice", "result": result}

        elif analysis_type == "custom":
            if not request.custom_prompt:
                raise HTTPException(status_code=400, detail="自定义分析需要提供 custom_prompt")
            result = ai_provider.custom_analyze(request.content, request.custom_prompt)
            return {"type": "custom", "result": result}

        else:
            raise HTTPException(status_code=400, detail=f"不支持的分析类型: {analysis_type}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 分析失败: {str(e)}")


@router.get("/status", response_model=dict)
def ai_status():
    """获取 AI Provider 状态"""
    from app.services.ai_provider import ai_provider
    from app.config import settings

    return {
        "available": ai_provider.is_available(),
        "model": settings.ai_model,
        "provider": "qwen" if ai_provider.is_available() else None,
        "base_url": settings.ai_base_url,
    }

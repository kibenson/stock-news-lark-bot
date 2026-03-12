"""
定时任务调度模块 - 使用 APScheduler
默认每天早上8点执行推送任务
"""
import logging
from datetime import datetime
from typing import Optional, Dict

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from app.config import settings

logger = logging.getLogger(__name__)

# 全局调度器实例
scheduler = BackgroundScheduler(timezone=settings.push_timezone)
_scheduler_started = False


def _job_listener(event):
    """任务执行事件监听器"""
    if event.exception:
        logger.error(f"调度任务执行失败: {event.job_id}, 错误: {event.exception}")
    else:
        logger.info(f"调度任务执行完成: {event.job_id}")


def run_daily_pipeline():
    """
    每日执行的完整任务流程:
    1. 抓取新闻
    2. 爬取关键词资讯
    3. 抓取监控用户发言
    4. 情感分析
    5. 生成报告
    6. 推送到 Lark
    """
    logger.info("===== 开始执行每日推送任务 =====")
    start_time = datetime.now()

    from app.database import SessionLocal
    db = SessionLocal()

    try:
        # 1. 获取配置
        from app.models.models import WatchStock, Keyword
        active_stocks = db.query(WatchStock).filter(WatchStock.is_active == True).all()
        active_keywords = db.query(Keyword).filter(Keyword.is_active == True).all()

        symbols = [s.symbol for s in active_stocks]
        keywords = [k.keyword for k in active_keywords]

        logger.info(f"关注股票: {symbols}, 关键词: {keywords}")

        # 2. 抓取新闻
        from app.services.news_fetcher import fetch_all_news, save_articles_to_db
        articles = fetch_all_news(symbols=symbols, keywords=keywords)
        new_count = save_articles_to_db(articles, db)
        logger.info(f"新增新闻: {new_count} 条")

        # 3. 爬取关键词资讯
        if keywords:
            from app.services.keyword_crawler import crawl_all_keywords, save_keyword_news_to_db
            keyword_articles = crawl_all_keywords(keywords, max_per_keyword=5)
            kw_count = save_keyword_news_to_db(keyword_articles, db)
            logger.info(f"关键词资讯: 新增 {kw_count} 条")

        # 4. 抓取监控用户发言
        from app.services.user_monitor import user_monitor_service
        post_count = user_monitor_service.fetch_all_monitored_users(db)
        logger.info(f"用户发言: 新增 {post_count} 条")

        # 5. 生成报告
        from app.services.report_generator import generate_daily_report
        use_ai = settings.dashscope_api_key and settings.dashscope_api_key != "your-dashscope-api-key"
        report = generate_daily_report(db, use_ai=bool(use_ai))

        # 6. 推送到 Lark
        from app.services.lark_notifier import send_daily_report
        from app.models.models import PushHistory

        responses = send_daily_report(
            articles=report.get("articles", []),
            sentiment_summary=report.get("sentiment_summary"),
            ai_summary=report.get("ai_summary"),
        )

        # 记录推送历史
        for response in responses:
            status = "success" if response.get("code") == 0 or response.get("StatusCode") == 0 else "failed"
            history = PushHistory(
                push_type="daily_report",
                title=f"{report['date']} 全球股票新闻日报",
                content=f"共推送 {len(report.get('articles', []))} 条新闻",
                status=status,
                lark_response=response,
            )
            db.add(history)
        db.commit()

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"===== 每日推送任务完成，耗时 {elapsed:.1f}s =====")

    except Exception as e:
        logger.error(f"每日推送任务执行失败: {e}", exc_info=True)
        # 记录失败历史
        try:
            from app.models.models import PushHistory
            history = PushHistory(
                push_type="daily_report",
                title="每日报告推送失败",
                status="failed",
                error_message=str(e),
            )
            db.add(history)
            db.commit()
        except Exception:
            pass
    finally:
        db.close()


def start_scheduler():
    """启动定时任务调度器"""
    global _scheduler_started

    if _scheduler_started:
        logger.warning("调度器已在运行")
        return

    # 添加事件监听器
    scheduler.add_listener(
        _job_listener,
        EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
    )

    # 添加每日推送任务
    scheduler.add_job(
        run_daily_pipeline,
        trigger=CronTrigger(
            hour=settings.push_schedule_hour,
            minute=settings.push_schedule_minute,
            timezone=settings.push_timezone,
        ),
        id="daily_push",
        name="每日股票新闻推送",
        replace_existing=True,
        misfire_grace_time=3600,  # 1小时内的错过执行仍可补执行
    )

    scheduler.start()
    _scheduler_started = True

    next_run = scheduler.get_job("daily_push").next_run_time
    logger.info(
        f"定时调度器启动成功，下次执行时间: "
        f"{next_run.strftime('%Y-%m-%d %H:%M:%S %Z') if next_run else 'N/A'}"
    )


def stop_scheduler():
    """停止定时任务调度器"""
    global _scheduler_started
    if _scheduler_started:
        scheduler.shutdown(wait=False)
        _scheduler_started = False
        logger.info("定时调度器已停止")


def trigger_manual_push(db=None) -> Dict:
    """
    手动触发推送任务
    
    Args:
        db: 可选的数据库会话，为None时自动创建
    
    Returns:
        执行结果
    """
    logger.info("手动触发推送任务")
    try:
        run_daily_pipeline()
        return {"success": True, "message": "推送任务执行完成"}
    except Exception as e:
        logger.error(f"手动触发失败: {e}")
        return {"success": False, "message": str(e)}


def get_scheduler_status() -> dict:
    """获取调度器状态"""
    job = scheduler.get_job("daily_push") if _scheduler_started else None
    return {
        "running": _scheduler_started,
        "next_run_time": (
            job.next_run_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            if job and job.next_run_time else None
        ),
        "schedule": f"每天 {settings.push_schedule_hour:02d}:{settings.push_schedule_minute:02d} ({settings.push_timezone})",
    }

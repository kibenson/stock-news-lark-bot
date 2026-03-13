"""
用户发言监控服务 - 预留多平台爬虫接口
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class BasePlatformMonitor:
    """平台监控器基类"""

    platform_name: str = "unknown"

    def fetch_user_posts(
        self,
        username: str,
        limit: int = 20,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        抓取用户最新发言（子类实现）
        
        Returns:
            发言列表，每项包含: content, post_url, posted_at
        """
        raise NotImplementedError


class TwitterMonitor(BasePlatformMonitor):
    """
    Twitter/X 用户监控
    预留接口 - 需要配置 Twitter API Bearer Token
    """
    platform_name = "twitter"

    def __init__(self, bearer_token: Optional[str] = None):
        self.bearer_token = bearer_token

    def fetch_user_posts(
        self,
        username: str,
        limit: int = 20,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        通过 Twitter API v2 抓取用户推文
        注意：需要申请 Twitter Developer 账号并配置 Bearer Token
        """
        if not self.bearer_token:
            logger.warning("Twitter Bearer Token 未配置，跳过抓取")
            return []

        try:
            import requests
            headers = {"Authorization": f"Bearer {self.bearer_token}"}

            # 获取用户ID
            user_url = f"https://api.twitter.com/2/users/by/username/{username}"
            user_resp = requests.get(user_url, headers=headers, timeout=10)
            user_resp.raise_for_status()
            user_id = user_resp.json().get("data", {}).get("id")
            if not user_id:
                return []

            # 获取用户时间线
            timeline_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
            params = {
                "max_results": min(limit, 100),
                "tweet.fields": "created_at,text",
            }
            if since:
                params["start_time"] = since.strftime("%Y-%m-%dT%H:%M:%SZ")

            resp = requests.get(timeline_url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            tweets = resp.json().get("data", [])

            return [
                {
                    "content": tweet.get("text", ""),
                    "post_url": f"https://twitter.com/{username}/status/{tweet.get('id')}",
                    "posted_at": (
                        datetime.fromisoformat(tweet["created_at"].replace("Z", "+00:00"))
                        if tweet.get("created_at") else None
                    ),
                    "platform": "twitter",
                }
                for tweet in tweets
            ]

        except Exception as e:
            logger.error(f"Twitter抓取失败 (用户: {username}): {e}")
            return []


class XueqiuMonitor(BasePlatformMonitor):
    """
    雪球 用户发言监控
    预留接口 - 注意遵守平台爬取协议
    """
    platform_name = "xueqiu"

    def fetch_user_posts(
        self,
        username: str,
        limit: int = 20,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        雪球用户动态抓取（预留，需要处理登录态）
        """
        logger.warning("雪球监控接口预留，请参考 README 配置实现")
        return []


class UserMonitorService:
    """用户监控服务 - 统一管理多平台监控"""

    def __init__(self):
        self._monitors: Dict[str, BasePlatformMonitor] = {
            "twitter": TwitterMonitor(),
            "xueqiu": XueqiuMonitor(),
        }

    def register_monitor(self, platform: str, monitor: BasePlatformMonitor):
        """注册新的平台监控器"""
        self._monitors[platform] = monitor
        logger.info(f"注册平台监控器: {platform}")

    def fetch_user_posts(
        self,
        platform: str,
        username: str,
        limit: int = 20,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        从指定平台抓取用户发言
        
        Args:
            platform: 平台名称 (twitter/xueqiu)
            username: 用户名
            limit: 最大抓取条数
            since: 起始时间
        
        Returns:
            发言列表
        """
        monitor = self._monitors.get(platform.lower())
        if not monitor:
            logger.warning(f"未找到平台监控器: {platform}")
            return []
        return monitor.fetch_user_posts(username, limit, since)

    def fetch_all_monitored_users(self, db, use_ai_sentiment: bool = False) -> int:
        """
        抓取数据库中所有激活用户的最新发言并保存
        
        Args:
            db: 数据库会话
            use_ai_sentiment: 是否使用AI情感分析
        
        Returns:
            新增发言总数
        """
        from app.models.models import MonitoredUser, UserPost
        from app.services.sentiment_analyzer import analyze_text

        active_users = db.query(MonitoredUser).filter(
            MonitoredUser.is_active == True
        ).all()

        total_new = 0
        for user in active_users:
            try:
                # 获取最近一条记录时间
                latest_post = db.query(UserPost).filter(
                    UserPost.monitored_user_id == user.id
                ).order_by(UserPost.posted_at.desc()).first()

                since = latest_post.posted_at if latest_post else None

                # 抓取新发言
                posts = self.fetch_user_posts(
                    platform=user.platform,
                    username=user.username,
                    limit=20,
                    since=since
                )

                for post_data in posts:
                    # 检查是否已存在
                    if post_data.get("post_url"):
                        exists = db.query(UserPost).filter(
                            UserPost.post_url == post_data["post_url"]
                        ).first()
                        if exists:
                            continue

                    # 情感分析
                    sentiment = analyze_text(
                        post_data.get("content", ""),
                        use_ai=use_ai_sentiment
                    )

                    post = UserPost(
                        monitored_user_id=user.id,
                        content=post_data.get("content", "")[:5000],
                        platform=user.platform,
                        post_url=post_data.get("post_url", "")[:1000] if post_data.get("post_url") else None,
                        posted_at=post_data.get("posted_at"),
                        sentiment_score=sentiment.get("score"),
                        sentiment_label=sentiment.get("label"),
                    )
                    db.add(post)
                    total_new += 1

                db.commit()
                logger.info(f"用户 {user.platform}/{user.username}: 新增 {len(posts)} 条发言")

            except Exception as e:
                logger.error(f"抓取用户 {user.username} 发言失败: {e}")
                db.rollback()

        return total_new


# 全局实例
user_monitor_service = UserMonitorService()

from django_redis import get_redis_connection

UNIQUE_VISITORS_KEY = "article:{article_id}:unique_visitors"
TOTAL_VIEWS_KEY = "article:{article_id}:total_views"
USER_VIEW_KEY = "user:{user_id}:view_count"


class RedisService:
    def __init__(self):
        self.conn = get_redis_connection("default")

    def increment_unique_visitors(self, article_id):
        """增加用户人次"""
        self.conn.incr(UNIQUE_VISITORS_KEY.format(article_id=article_id))

    def increment_total_views(self, article_id):
        """增加总阅读数"""
        self.conn.incr(TOTAL_VIEWS_KEY.format(article_id=article_id))

    def increment_user_view(self, user_id, article_id):
        """增加用户阅读某文章次数"""
        with self.conn.pipeline() as pipe:
            pipe.hget(USER_VIEW_KEY.format(user_id=user_id), article_id)
            pipe.hincrby(USER_VIEW_KEY.format(user_id=user_id), article_id, 1)
            results = pipe.execute()

            has_viewed = results[0]
            # 3. 如果之前没有读过，则增加阅读次数
            if has_viewed is None:
                self.increment_unique_visitors(article_id)

    def get_article_stats(self, article_id, user_id):
        """
        获取文章的：
        - 总阅读数(total_views)
        - 用户人次(unique_visitors)
        - 当前用户对该文章的阅读次数(user_view_count)
        """
        with self.conn.pipeline() as pipe:
            # 1. 获取总阅读数
            pipe.get(TOTAL_VIEWS_KEY.format(article_id=article_id))

            # 2. 获取独立访客数(hash 的 field 数量 = 不同用户的数量)
            pipe.get(UNIQUE_VISITORS_KEY.format(article_id=article_id))

            # 3. 获取当前用户阅读此文章的次数
            pipe.hget(USER_VIEW_KEY.format(user_id=user_id), article_id)

            # 执行所有查询
            total_views_str, unique_visitors, user_view_count_str = pipe.execute()

        # 处理可能为 None 的情况
        total_views = int(total_views_str) if total_views_str else 0
        unique_visitors = int(unique_visitors) if unique_visitors else 0
        user_view_count = int(user_view_count_str) if user_view_count_str else 0

        return {
            "total_views": total_views,
            "unique_visitors": unique_visitors,
            "user_view_count": user_view_count,
        }

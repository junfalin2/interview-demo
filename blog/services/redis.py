from django_redis import get_redis_connection

from blog.models import UNIQUE_VISITORS_KEY,TOTAL_VIEWS_KEY

ARTICLE_KEY = "article:{article_id}"

USER_VIEW_KEY = "user:{user_id}:view_count"


class RedisService:
    def __init__(self):
        self.conn = get_redis_connection("default")

    def increment_unique_visitors(self, article_id):
        """增加用户人次"""
        self.conn.hincrby(
            ARTICLE_KEY.format(article_id=article_id), UNIQUE_VISITORS_KEY, 1
        )

    def increment_total_views(self, article_id):
        """增加总阅读数"""
        self.conn.hincrby(ARTICLE_KEY.format(article_id=article_id), TOTAL_VIEWS_KEY, 1)

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

    def get_articles_cache(self, article_id):
        data = {}
        # 获取所有或指定id的key
        keys = self.conn.keys(ARTICLE_KEY.format(article_id=article_id))
        with self.conn.pipeline() as pipe:
            for k in keys:
                pipe.hgetall(k)
            results = pipe.execute()

        for k, result in zip(keys, results):
            uid = int(k.decode("utf-8").split(":")[1])
            # 解码哈希表的键值对
            data[uid] = {
                sub_k.decode("utf-8"): int(sub_v.decode("utf-8"))
                for sub_k, sub_v in result.items()
            }
        return data

    def get_user_view_count(self, user_id):
        data = {}
        # 获取所有或指定id的key
        keys = self.conn.keys(USER_VIEW_KEY.format(user_id=user_id))
        with self.conn.pipeline() as pipe:
            for k in keys:
                pipe.hgetall(k)
            results = pipe.execute()

        for k, result in zip(keys, results):
            uid = int(k.decode("utf-8").split(":")[1])
            # 解码哈希表的键值对
            data[uid] = {
                sub_k.decode("utf-8"): int(sub_v.decode("utf-8"))
                for sub_k, sub_v in result.items()
            }
        return data

    def get_statistics(self, article_id, user_id):
        """获取统计量"""
        article_cache = self.get_articles_cache(article_id=article_id)
        user_view_count = self.get_user_view_count(user_id=user_id)
        return {
            "articles": article_cache,
            "user_view_count": user_view_count,
        }

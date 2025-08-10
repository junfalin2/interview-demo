from contextlib import contextmanager
import json
import random
from django_redis import get_redis_connection

from blog.exceptions.redis import redis_catch
from blog.models import UNIQUE_VISITORS_KEY, TOTAL_VIEWS_KEY, VIEW_COUNT_KEY

STATISTICS_ARTICLE_KEY = "statistics:article:{article_id}"

STATISTICS_USER_VIEW_KEY = "statistics:user_view_count:{user_id}"

ARTICLE_CONTENT_KEY = "warm:article_content:{article_id}"

SYNC_UNIQUE_VISITORS_KEY = "sync:unique_visitors:{article_id}"
SYNC_TOTAL_VIEWS_KEY = "sync:total_views:{article_id}"
SYNC_VIEW_COUNT_KEY = "sync:view_count:{user_id}:{article_id}"


class RedisService:
    @redis_catch
    def __init__(self):
        self.conn = get_redis_connection("default")

    @redis_catch
    def get_keys(self, match):
        cursor = 0
        keys = []
        while True:
            cursor, batch_keys = self.conn.scan(
                cursor=cursor, match=match, count=100  # 每次扫描100个键（可调整）
            )
            keys.extend(batch_keys)
            if cursor == 0:
                break  # 扫描结束
        return keys

    @redis_catch
    def increment_unique_visitors(self, article_id):
        """增加用户人次"""
        self.conn.hincrby(
            STATISTICS_ARTICLE_KEY.format(article_id=article_id), UNIQUE_VISITORS_KEY, 1
        )
        self.conn.incr(SYNC_UNIQUE_VISITORS_KEY.format(article_id=article_id))

    @redis_catch
    def increment_total_views(self, article_id):
        """增加总阅读数"""
        self.conn.hincrby(
            STATISTICS_ARTICLE_KEY.format(article_id=article_id), TOTAL_VIEWS_KEY, 1
        )
        self.conn.incr(SYNC_TOTAL_VIEWS_KEY.format(article_id=article_id))

    @redis_catch
    def increment_user_view(self, user_id, article_id):
        """增加用户阅读某文章次数"""
        with self.conn.pipeline() as pipe:
            pipe.hget(STATISTICS_USER_VIEW_KEY.format(user_id=user_id), article_id)
            pipe.hincrby(
                STATISTICS_USER_VIEW_KEY.format(user_id=user_id), article_id, 1
            )
            pipe.incr(
                SYNC_VIEW_COUNT_KEY.format(user_id=user_id, article_id=article_id)
            )
            results = pipe.execute()

            has_viewed = results[0]
            # 3. 如果之前没有读过，则增加阅读次数
            if has_viewed is None:
                self.increment_unique_visitors(article_id)

    @redis_catch
    def get_articles_statistics(self, article_id):
        data = {}
        # 获取所有或指定id的key
        keys = self.get_keys(STATISTICS_ARTICLE_KEY.format(article_id=article_id))
        print(keys)
        with self.conn.pipeline() as pipe:
            for k in keys:
                pipe.hgetall(k)
            results = pipe.execute()

        for k, result in zip(keys, results):
            aid = int(k.decode("utf-8").split(":")[-1])
            # 解码哈希表的键值对
            data[aid] = {
                sub_k.decode("utf-8"): int(sub_v.decode("utf-8"))
                for sub_k, sub_v in result.items()
            }
        return data

    @redis_catch
    def get_user_view_count_statistics(self, article_id, user_id):
        data = {}
        # 获取所有或指定id的key
        keys = self.get_keys(
            STATISTICS_USER_VIEW_KEY.format(article_id=article_id, user_id=user_id)
        )
        with self.conn.pipeline() as pipe:
            for k in keys:
                pipe.hgetall(k)
            results = pipe.execute()

        for k, result in zip(keys, results):
            uid = int(k.decode("utf-8").split(":")[-1])
            # 解码哈希表的键值对
            data[uid] = {
                sub_k.decode("utf-8"): int(sub_v.decode("utf-8"))
                for sub_k, sub_v in result.items()
            }
        return data

    @redis_catch
    def get_statistics(self, article_id, user_id):
        """获取统计量"""
        article_cache = self.get_articles_statistics(article_id=article_id)
        user_view_count = self.get_user_view_count_statistics(
            article_id=article_id, user_id=user_id
        )
        return {
            "articles": article_cache,
            "user_view_count": user_view_count,
        }

    @redis_catch
    def get_article_content(self, article_id):
        """获取文章内容"""
        cached_article = self.conn.get(
            ARTICLE_CONTENT_KEY.format(article_id=article_id)
        )
        article = None
        if cached_article:
            try:
                article = json.loads(cached_article)
            except json.JSONDecodeError as e:
                article = None
        return article

    @redis_catch
    def set_article_content(self, article_id, val):
        "缓存文章内容"
        return self.conn.set(
            ARTICLE_CONTENT_KEY.format(article_id=article_id),
            json.dumps(val),
            ex=3600 + random.randint(0, 600),
        )

    @redis_catch
    @contextmanager
    def sync_totalview(self):
        """同步总阅读次数"""
        data = {}
        # 获取所有或指定id的key
        keys = self.get_keys(SYNC_TOTAL_VIEWS_KEY.format(article_id="*"))
        with self.conn.pipeline() as pipe:
            for k in keys:
                pipe.getset(k, 0)
            result = pipe.execute()
            data = {
                int(k.decode("utf-8").split(":")[-1]): int(v)
                for k, v in zip(keys, result)
                if v is not None
            }
        try:
            yield data
        except Exception as e:
            with self.conn.pipeline() as pipe:
                for aid, old_value in data.items():
                    # 旧值可能为None（键不存在），或字符串类型的数字
                    if old_value is not None:
                        pipe.incrby(
                            SYNC_TOTAL_VIEWS_KEY.format(article_id=aid), old_value
                        )  # 加回旧值
                pipe.execute()
            raise e

    @redis_catch
    @contextmanager
    def sync_unique_visitors(self):
        "同步用户人次"
        data = {}
        # 获取所有或指定id的key
        keys = self.get_keys(SYNC_UNIQUE_VISITORS_KEY.format(article_id="*"))
        with self.conn.pipeline() as pipe:
            for k in keys:
                pipe.getset(k, 0)
            result = pipe.execute()
            data = {
                int(k.decode("utf-8").split(":")[-1]): int(v)
                for k, v in zip(keys, result)
                if v is not None
            }
        try:
            yield data
        except Exception as e:
            with self.conn.pipeline() as pipe:
                for aid, old_value in data.items():
                    # 旧值可能为None（键不存在），或字符串类型的数字
                    if old_value is not None:
                        pipe.incrby(
                            SYNC_UNIQUE_VISITORS_KEY.format(article_id=aid), old_value
                        )  # 加回旧值
                pipe.execute()
            raise e

    @redis_catch
    @contextmanager
    def sync_view_count(self):
        "同步用户阅读次数"
        data = {}
        # 获取所有或指定id的key
        keys = self.get_keys(SYNC_VIEW_COUNT_KEY.format(article_id="*", user_id="*"))
        with self.conn.pipeline() as pipe:
            for k in keys:
                pipe.getset(k, 0)
            result = pipe.execute()
            data = [
                {
                    "user_id": int(k.decode("utf-8").split(":")[-2]),
                    "article_id": int(k.decode("utf-8").split(":")[-1]),
                    VIEW_COUNT_KEY: int(v),
                }
                for k, v in zip(keys, result)
                if v is not None
            ]
        try:
            yield data
        except Exception as e:
            with self.conn.pipeline() as pipe:
                for item in data:
                    # 旧值可能为None（键不存在），或字符串类型的数字
                    aid = item["article_id"]
                    uid = item["user_id"]
                    old_value = item[VIEW_COUNT_KEY]
                    if old_value is not None:
                        pipe.incrby(
                            SYNC_VIEW_COUNT_KEY.format(article_id=aid, user_id=uid),
                            old_value,
                        )  # 加回旧值
                pipe.execute()
            raise e

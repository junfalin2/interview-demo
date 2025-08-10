# services/local_queue.py
import threading
import time

from django_q.tasks import async_task

from blog.tasks import update_view_count


class Worker:
    _queue = []
    _lock = threading.Lock()

    @classmethod
    def enqueue(cls, queue_type, item):
        with cls._lock:
            cls._queue.append((queue_type, item))

    @classmethod
    def start_worker(cls):
        """
        启动后台线程，定期重试本地队列中的任务
        """

        def worker():
            while True:
                time.sleep(5)  # 每 5 秒检查一次
                items = []
                with cls._lock:
                    items = cls._queue[:]
                    cls._queue.clear()

                for q_type, item in items:
                    if q_type == "db":
                        try:
                            if item["action"] == "update_view_count":
                                async_task(
                                    update_view_count,
                                    item['article_id'],
                                    item['user_id'],
                                    task_name="increment_user_view_and_total_views",
                                )
                        except Exception as e:
                            # 重新加入队列
                            with cls._lock:
                                cls._queue.append((q_type, item))

        t = threading.Thread(target=worker, daemon=True)
        t.start()

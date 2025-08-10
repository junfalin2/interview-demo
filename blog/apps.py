from datetime import datetime
from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "blog"

    def ready(self):
        post_migrate.connect(create_schedule, sender=self)


@receiver(post_migrate)
def create_schedule(sender, **kwargs):
    if sender.name != "blog":
        return

    from django_q.models import Schedule

    Schedule.objects.get_or_create(
        name="sync_articles_to_db",
        func="blog.tasks.sync_articles_to_db",
        schedule_type=Schedule.MINUTES,
        minutes=1,
    )

    # 模拟低峰时期或者冷启动时加载
    Schedule.objects.get_or_create(
        name="warm_up_cache",
        func="blog.tasks.warm_up_cache",
        schedule_type=Schedule.DAILY,
        repeats=-1,  # 永久重复
        next_run=datetime.now().replace(
            hour=2, minute=0, second=0, microsecond=0
        ),  # 凌晨2点
    )

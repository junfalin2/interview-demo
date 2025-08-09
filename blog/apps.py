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

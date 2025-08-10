from django.urls import path

from . import views

app_name = "blogs"

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:article_id>/<int:user_id>", views.detail, name="detail"),
    path("statistics", views.statistics, name="statistics"),
    path("metrics", views.metrics, name="metrics"),
]
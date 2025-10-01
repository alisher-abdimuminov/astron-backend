from django.urls import path

from .views import (
    payme_callback,
    get_announcement,
    telemetry,
    increment_receivers,
)


urlpatterns = [
    path("payme/", payme_callback),
    path("announcement/", get_announcement),
    path("telemetry/", telemetry),
    path("increment-receivers/", increment_receivers),
]

from django.urls import path

from .views import (
    payme_callback,
    get_announcement,
    telemetry,
)


urlpatterns = [
    path("payme/", payme_callback),
    path("announcement/", get_announcement),
    path("telemetry/", telemetry),
]

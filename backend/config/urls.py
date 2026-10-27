from core import views
from django.urls import path, re_path
from django.views.generic import TemplateView
from django.views.static import serve

from . import settings

urlpatterns = [
    path("api/session/", views.session),
    path("api/register/", views.register),
    path("api/login/", views.sign_in),
    path("api/logout/", views.sign_out),
    path("api/claim/", views.claim),
    path("api/redeem/", views.redeem),
    re_path(
        r"^api/.*$",
        views.not_found,
    ),
    # Servidor de demonstração local; em produção, servir assets num servidor estático.
    re_path(
        r"^assets/(?P<path>.*)$",
        serve,
        {"document_root": settings.BASE_DIR.parent / "frontend/dist/assets"},
    ),
    path("", TemplateView.as_view(template_name="index.html")),
    path("dashboard", TemplateView.as_view(template_name="index.html")),
]

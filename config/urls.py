from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

from campus.weather import venue_weather

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("api/token/", obtain_auth_token, name="api-token"),
    path("api/", include("campus.api_urls")),
    path("weather/", venue_weather, name="weather"),
    path("", include("campus.urls")),
]

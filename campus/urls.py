from django.urls import path

from . import views
from .location_search import location_search

app_name = "campus"

urlpatterns = [
    path("location-search/", location_search, name="location_search"),
    path("", views.dashboard, name="dashboard"),
    path("records/events/upcoming/", views.record_list, {"slug": "events", "upcoming": True}, name="upcoming_events"),
    path("records/<slug:slug>/", views.record_list, name="record_list"),
    path("records/<slug:slug>/new/", views.edit_record, name="record_create"),
    path("records/<slug:slug>/<int:pk>/", views.record_detail, name="record_detail"),
    path("records/<slug:slug>/<int:pk>/edit/", views.edit_record, name="record_update"),
    path("records/<slug:slug>/<int:pk>/delete/", views.delete_record, name="record_delete"),
]

from rest_framework.routers import DefaultRouter

from .api import (
    CampusViewSet, CategoryViewSet, EventViewSet, OrganizationViewSet,
    RegistrationViewSet, StudentViewSet, VenueViewSet,
)

router = DefaultRouter()
router.register("campuses", CampusViewSet)
router.register("venues", VenueViewSet)
router.register("organizations", OrganizationViewSet)
router.register("categories", CategoryViewSet)
router.register("students", StudentViewSet)
router.register("events", EventViewSet)
router.register("registrations", RegistrationViewSet)
urlpatterns = router.urls

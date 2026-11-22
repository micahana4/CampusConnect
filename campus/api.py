from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.response import Response

from .models import Campus, Category, Event, Organization, Registration, Student, Venue
from .permissions import has_record_permission
from .serializers import (
    CampusSerializer, CategorySerializer, EventSerializer, OrganizationSerializer,
    RegistrationSerializer, StudentSerializer, VenueSerializer,
)


class CampusAccess(BasePermission):
    def has_permission(self, request, view):
        model = view.queryset.model
        if request.method in SAFE_METHODS:
            action = "view"
        else:
            action = {"POST": "add", "PUT": "change", "PATCH": "change", "DELETE": "delete"}.get(request.method)
            if action is None:
                return False
        return has_record_permission(request.user, model, action)


class CampusModelViewSet(viewsets.ModelViewSet):
    permission_classes = [CampusAccess]

    def _save(self, serializer):
        try:
            with transaction.atomic():
                serializer.save()
        except IntegrityError:
            raise ValidationError("A related record changed or this record already exists.")

    def perform_create(self, serializer):
        self._save(serializer)

    def perform_update(self, serializer):
        self._save(serializer)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "This record is still in use. Update or remove its related records first."},
                status=status.HTTP_409_CONFLICT,
            )


class CampusViewSet(CampusModelViewSet):
    queryset = Campus.objects.all()
    serializer_class = CampusSerializer


class VenueViewSet(CampusModelViewSet):
    queryset = Venue.objects.all()
    serializer_class = VenueSerializer


class OrganizationViewSet(CampusModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


class CategoryViewSet(CampusModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class StudentViewSet(CampusModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer


class EventViewSet(CampusModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer


class RegistrationViewSet(CampusModelViewSet):
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer

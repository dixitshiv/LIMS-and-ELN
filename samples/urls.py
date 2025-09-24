from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SampleViewSet, StorageLocationViewSet

router = DefaultRouter()
router.register(r'samples', SampleViewSet)
router.register(r'storage-locations', StorageLocationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
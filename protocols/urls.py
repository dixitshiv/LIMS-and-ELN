from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProtocolViewSet, ProtocolCategoryViewSet

router = DefaultRouter()
router.register(r'protocols', ProtocolViewSet)
router.register(r'protocol-categories', ProtocolCategoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
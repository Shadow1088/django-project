from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'trucks', views.TruckViewSet, basename='truck')
router.register(r'locations', views.LocationViewSet, basename='location')

urlpatterns = [
    path('', include(router.urls)),
]

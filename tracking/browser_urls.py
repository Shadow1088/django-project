from django.urls import path
from . import views

urlpatterns = [
    path('', views.TruckListView.as_view(), name='truck_list'),
    path('trucks/<int:pk>/', views.TruckDetailView.as_view(), name='truck_detail'),
    path('trucks/new/', views.TruckCreateView.as_view(), name='truck_create'),
    path('trucks/<int:pk>/edit/', views.TruckUpdateView.as_view(), name='truck_update'),
    path('trucks/<int:pk>/report-location/', views.report_location, name='report_location'),
]

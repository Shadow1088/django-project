from django.urls import path
from . import views

urlpatterns = [
    path('', views.TruckListView.as_view(), name='truck_list'),
    path('gallery/', views.TruckGalleryView.as_view(), name='truck_gallery'),
    path('locations/', views.LocationListView.as_view(), name='location_list'),
    path('trucks/<int:pk>/', views.TruckDetailView.as_view(), name='truck_detail'),
    path('trucks/new/', views.TruckCreateView.as_view(), name='truck_create'),
    path('trucks/<int:pk>/edit/', views.TruckUpdateView.as_view(), name='truck_update'),
    path('trucks/<int:pk>/report-location/', views.report_location, name='report_location'),
    path('trucks/<int:pk>/export-csv/', views.export_locations_csv, name='export_locations_csv'),
]

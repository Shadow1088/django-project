import csv
import json
from datetime import datetime

from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import FloatField, OuterRef, Subquery
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.timezone import make_aware
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Truck, Location
from .serializers import (
    TruckListSerializer,
    TruckDetailSerializer,
    LocationSerializer,
)
from .permissions import IsAdminOrReadOnly, IsAdminOrAssignedDriver


class TruckViewSet(viewsets.ModelViewSet):
    queryset = Truck.objects.select_related('driver').all()
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly, IsAdminOrAssignedDriver]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TruckDetailSerializer
        return TruckListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == 'driver':
            qs = qs.filter(driver=self.request.user)
        if self.request.query_params.get('active'):
            qs = qs.filter(is_active=(self.request.query_params['active'].lower() == 'true'))
        if self.request.query_params.get('plate'):
            qs = qs.filter(plate_number__icontains=self.request.query_params['plate'])
        return qs

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['get'])
    def recent_locations(self, request, pk=None):
        truck = self.get_object()
        locations = truck.locations.all()[:10]
        serializer = LocationSerializer(locations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def locations(self, request, pk=None):
        truck = self.get_object()
        locations = truck.locations.all()
        page = self.paginate_queryset(locations)
        if page is not None:
            serializer = LocationSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = LocationSerializer(locations, many=True)
        return Response(serializer.data)


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.select_related('truck__driver').all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated, IsAdminOrAssignedDriver]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == 'driver':
            qs = qs.filter(truck__driver=self.request.user)
        truck_id = self.request.query_params.get('truck')
        if truck_id:
            qs = qs.filter(truck_id=truck_id)
        return qs

    def perform_create(self, serializer):
        truck = serializer.validated_data['truck']
        if self.request.user.role == 'driver' and truck.driver != self.request.user:
            self.permission_denied(self.request, 'You can only report location for your assigned truck.')
        serializer.save()


# ---------- Browser Views ----------

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role == 'admin'


class TruckListView(LoginRequiredMixin, ListView):
    model = Truck
    template_name = 'tracking/truck_list.html'
    context_object_name = 'trucks'

    def get_queryset(self):
        qs = Truck.objects.select_related('driver').all()
        if self.request.user.role == 'driver':
            qs = qs.filter(driver=self.request.user)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(plate_number__icontains=q)
        active = self.request.GET.get('active')
        if active == 'true':
            qs = qs.filter(is_active=True)
        elif active == 'false':
            qs = qs.filter(is_active=False)
        return qs


class TruckGalleryView(LoginRequiredMixin, ListView):
    model = Truck
    template_name = 'tracking/truck_gallery.html'
    context_object_name = 'trucks'

    def get_queryset(self):
        latest = Location.objects.filter(truck=OuterRef('pk')).order_by('-recorded_at')
        qs = Truck.objects.select_related('driver').annotate(
            latest_lat=Subquery(latest.values('latitude')[:1], output_field=FloatField()),
            latest_lng=Subquery(latest.values('longitude')[:1], output_field=FloatField()),
            latest_speed=Subquery(latest.values('speed')[:1], output_field=FloatField()),
            latest_time=Subquery(latest.values('recorded_at')[:1]),
        )
        if self.request.user.role == 'driver':
            qs = qs.filter(driver=self.request.user)
        return qs


class TruckDetailView(LoginRequiredMixin, DetailView):
    model = Truck
    template_name = 'tracking/truck_detail.html'
    context_object_name = 'truck'

    def get_queryset(self):
        qs = Truck.objects.select_related('driver').all()
        if self.request.user.role == 'driver':
            qs = qs.filter(driver=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        truck = self.object

        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        locs = truck.locations.all()
        if date_from:
            try:
                dt = make_aware(datetime.strptime(date_from, '%Y-%m-%d'))
                locs = locs.filter(recorded_at__gte=dt)
            except ValueError:
                pass
        if date_to:
            try:
                dt = make_aware(datetime.strptime(date_to, '%Y-%m-%d'))
                locs = locs.filter(recorded_at__lte=dt)
            except ValueError:
                pass

        context['date_from'] = date_from
        context['date_to'] = date_to

        paginator = Paginator(locs, 20)
        page = self.request.GET.get('page', 1)
        context['page_obj'] = paginator.get_page(page)
        context['is_paginated'] = True

        map_locs = list(locs.values('id', 'latitude', 'longitude', 'speed', 'note', 'recorded_at'))
        for loc in map_locs:
            loc['latitude'] = float(loc['latitude'])
            loc['longitude'] = float(loc['longitude'])
            loc['recorded_at'] = loc['recorded_at'].strftime('%Y-%m-%d %H:%M:%S') if loc['recorded_at'] else None
        context['locations_json'] = json.dumps(map_locs).replace('</', '<\\/')
        context['has_locations'] = len(map_locs) > 0

        context['can_ping'] = self.request.user.role == 'admin' or (
            self.request.user.role == 'driver' and truck.driver == self.request.user
        )
        context['ping_success'] = self.request.GET.get('ping_success') == '1'
        return context


class TruckCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Truck
    template_name = 'tracking/truck_form.html'
    fields = ['plate_number', 'description', 'driver', 'is_active']
    success_url = reverse_lazy('truck_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Truck'
        return context


class TruckUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Truck
    template_name = 'tracking/truck_form.html'
    fields = ['plate_number', 'description', 'driver', 'is_active']
    success_url = reverse_lazy('truck_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit {self.object.plate_number}'
        return context


class LocationListView(LoginRequiredMixin, ListView):
    model = Location
    template_name = 'tracking/location_list.html'
    context_object_name = 'locations'
    paginate_by = 50

    def get_queryset(self):
        qs = Location.objects.select_related('truck__driver').all()
        if self.request.user.role == 'driver':
            qs = qs.filter(truck__driver=self.request.user)
        truck_id = self.request.GET.get('truck')
        if truck_id:
            qs = qs.filter(truck_id=truck_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trucks = Truck.objects.select_related('driver').all()
        if self.request.user.role == 'driver':
            trucks = trucks.filter(driver=self.request.user)
        context['trucks'] = trucks
        context['selected_truck'] = self.request.GET.get('truck', '')
        return context


def report_location(request, pk):
    truck = get_object_or_404(Truck, pk=pk)
    if request.user.role == 'driver' and truck.driver != request.user:
        messages.error(request, 'You can only report location for your assigned truck.')
    return redirect('truck_detail', pk=pk)


def export_locations_csv(request, pk):
    truck = get_object_or_404(Truck, pk=pk)
    if request.user.role == 'driver' and truck.driver != request.user:
        messages.error(request, 'Access denied.')
        return redirect('truck_detail', pk=pk)

    locs = truck.locations.all()
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        try:
            dt = make_aware(datetime.strptime(date_from, '%Y-%m-%d'))
            locs = locs.filter(recorded_at__gte=dt)
        except ValueError:
            pass
    if date_to:
        try:
            dt = make_aware(datetime.strptime(date_to, '%Y-%m-%d'))
            locs = locs.filter(recorded_at__lte=dt)
        except ValueError:
            pass
    locs = locs.order_by('recorded_at')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{truck.plate_number}_locations.csv"'
    writer = csv.writer(response)
    writer.writerow(['id', 'latitude', 'longitude', 'speed', 'note', 'recorded_at'])
    for loc in locs:
        writer.writerow([
            loc.id,
            loc.latitude,
            loc.longitude,
            loc.speed or '',
            loc.note,
            loc.recorded_at.strftime('%Y-%m-%d %H:%M:%S') if loc.recorded_at else '',
        ])
    return response

    if request.method == 'POST':
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        speed = request.POST.get('speed') or None
        note = request.POST.get('note', '')
        if lat and lng:
            Location.objects.create(
                truck=truck,
                latitude=lat,
                longitude=lng,
                speed=speed,
                note=note,
            )
            return redirect(f'{reverse("truck_detail", args=[pk])}?ping_success=1')
        else:
            messages.error(request, 'Latitude and longitude are required.')
    return redirect('truck_detail', pk=pk)

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView
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
        context['locations'] = self.object.locations.all()[:10]
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


def report_location(request, pk):
    truck = get_object_or_404(Truck, pk=pk)
    if request.user.role == 'driver' and truck.driver != request.user:
        messages.error(request, 'You can only report location for your assigned truck.')
        return redirect('truck_detail', pk=pk)
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
            messages.success(request, 'Location reported.')
        else:
            messages.error(request, 'Latitude and longitude are required.')
    return redirect('truck_detail', pk=pk)

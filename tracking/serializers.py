from rest_framework import serializers
from .models import Truck, Location


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'truck', 'latitude', 'longitude', 'speed', 'note', 'recorded_at']
        read_only_fields = ['recorded_at']


class TruckListSerializer(serializers.ModelSerializer):
    driver_name = serializers.SerializerMethodField()

    class Meta:
        model = Truck
        fields = ['id', 'plate_number', 'description', 'driver', 'driver_name', 'is_active', 'created_at']

    def get_driver_name(self, obj):
        if obj.driver:
            return obj.driver.get_full_name() or obj.driver.username
        return None


class TruckDetailSerializer(serializers.ModelSerializer):
    driver_name = serializers.SerializerMethodField()
    recent_locations = serializers.SerializerMethodField()

    class Meta:
        model = Truck
        fields = [
            'id', 'plate_number', 'description', 'driver', 'driver_name',
            'is_active', 'created_at', 'updated_at', 'recent_locations',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_driver_name(self, obj):
        if obj.driver:
            return obj.driver.get_full_name() or obj.driver.username
        return None

    def get_recent_locations(self, obj):
        locations = obj.locations.all()[:10]
        return LocationSerializer(locations, many=True).data

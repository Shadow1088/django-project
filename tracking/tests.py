from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import Truck, Location
from accounts.models import User


class TrackingTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin1', password='adminpass', role='admin',
        )
        self.driver = User.objects.create_user(
            username='driver1', password='driverpass', role='driver',
        )
        self.client = APIClient()

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list_trucks_empty(self):
        self._auth(self.admin)
        response = self.client.get('/api/trucks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_create_truck_admin(self):
        self._auth(self.admin)
        data = {'plate_number': 'AB-1234', 'description': 'Scania R500'}
        response = self.client.post('/api/trucks/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['plate_number'], 'AB-1234')

    def test_driver_cannot_create_truck(self):
        self._auth(self.driver)
        data = {'plate_number': 'CD-5678', 'description': 'Volvo FH'}
        response = self.client.post('/api/trucks/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_driver_sees_only_assigned_trucks(self):
        self._auth(self.admin)
        t1 = Truck.objects.create(plate_number='T1', driver=self.driver)
        Truck.objects.create(plate_number='T2')
        self._auth(self.driver)
        response = self.client.get('/api/trucks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['plate_number'], 'T1')

    def test_driver_can_ping_location_on_assigned_truck(self):
        truck = Truck.objects.create(plate_number='AB-1234', driver=self.driver)
        self._auth(self.driver)
        data = {
            'truck': truck.id,
            'latitude': 48.7164,
            'longitude': 21.2611,
            'speed': 65.5,
            'note': 'Entering highway',
        }
        response = self.client.post('/api/locations/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Location.objects.count(), 1)

    def test_driver_cannot_ping_unassigned_truck(self):
        Truck.objects.create(plate_number='CD-5678')
        self._auth(self.driver)
        data = {'truck': 1, 'latitude': 48.7, 'longitude': 21.26}
        response = self.client.post('/api/locations/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_recent_locations_endpoint(self):
        self._auth(self.admin)
        truck = Truck.objects.create(plate_number='AB-1234')
        for i in range(15):
            Location.objects.create(
                truck=truck,
                latitude=48.7 + i * 0.001,
                longitude=21.26 + i * 0.001,
            )
        response = self.client.get(f'/api/trucks/{truck.id}/recent_locations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data), 10)

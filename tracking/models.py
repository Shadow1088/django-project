from django.db import models
from django.conf import settings
from django.core.validators import MinLengthValidator


class Truck(models.Model):
    plate_number = models.CharField(max_length=8, unique=True, validators=[MinLengthValidator(5)])
    description = models.TextField(blank=True, default='')
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trucks',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.plate_number} — {self.description[:30]}" if self.description else self.plate_number


class Location(models.Model):
    truck = models.ForeignKey(
        Truck,
        on_delete=models.CASCADE,
        related_name='locations',
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    speed = models.FloatField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True, default='')
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['truck', '-recorded_at']),
        ]

    def __str__(self):
        return f"{self.truck.plate_number} @ ({self.latitude}, {self.longitude})"

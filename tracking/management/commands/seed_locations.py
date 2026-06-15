import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from tracking.models import Truck, Location

CITIES = [
    ("Prague", 50.0755, 14.4378),
    ("Berlin", 52.5200, 13.4050),
    ("Vienna", 48.2082, 16.3738),
    ("Budapest", 47.4979, 19.0402),
    ("Warsaw", 52.2297, 21.0122),
    ("Bratislava", 48.1486, 17.1077),
    ("Krakow", 50.0647, 19.9450),
    ("Munich", 48.1351, 11.5820),
    ("Zagreb", 45.8150, 15.9819),
    ("Ljubljana", 46.0569, 14.5058),
]

def is_null_island(lat, lng):
    return abs(float(lat)) < 0.01 and abs(float(lng)) < 0.01


class Command(BaseCommand):
    help = "Replaces near-zero coordinates with realistic European city locations"

    def add_arguments(self, parser):
        parser.add_argument(
            "--add",
            type=int,
            default=0,
            help="Number of additional random locations per truck",
        )

    def handle(self, *args, **options):
        extra = options["add"]
        trucks = list(Truck.objects.all())
        random.shuffle(trucks)

        for i, truck in enumerate(trucks):
            city, base_lat, base_lng = CITIES[i % len(CITIES)]
            locations = list(truck.locations.all().order_by("recorded_at"))

            null_locs = [loc for loc in locations if is_null_island(loc.latitude, loc.longitude)]
            if null_locs:
                for loc in null_locs:
                    offset_lat = random.uniform(-0.02, 0.02)
                    offset_lng = random.uniform(-0.02, 0.02)
                    loc.latitude = round(base_lat + offset_lat, 6)
                    loc.longitude = round(base_lng + offset_lng, 6)
                    loc.speed = loc.speed or round(random.uniform(20, 90), 1)
                    loc.save(update_fields=["latitude", "longitude", "speed"])
                self.stdout.write(f"{truck.plate_number}: updated {len(null_locs)} null-island locations to {city}")

            if extra > 0:
                now = timezone.now()
                last_time = locations[-1].recorded_at if locations else now - timedelta(hours=1)
                for j in range(extra):
                    last_time += timedelta(minutes=random.randint(5, 30))
                    lat_offset = random.uniform(-0.015, 0.015)
                    lng_offset = random.uniform(-0.015, 0.015)
                    Location.objects.create(
                        truck=truck,
                        latitude=round(base_lat + lat_offset, 6),
                        longitude=round(base_lng + lng_offset, 6),
                        speed=round(random.uniform(20, 90), 1),
                        recorded_at=last_time,
                    )
                self.stdout.write(f"{truck.plate_number}: added {extra} new locations near {city}")

        self.stdout.write(self.style.SUCCESS("Done seeding locations"))

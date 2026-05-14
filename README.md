# Truck Tracker

A Django backend for tracking trucks and their GPS locations. Built with Django REST Framework (API) and server-rendered templates (browser UI).

## Features

- **Truck management** — Create, edit, list, and view trucks with plate numbers (5–8 chars), descriptions, and driver assignments
- **GPS location pinging** — Report latitude/longitude, speed, and notes for any truck
- **Location history** — View paginated history per truck, plus a quick "last 10 pings" snapshot
- **Role-based access** — Admins manage everything; drivers only see and ping their assigned truck
- **Dual interface** — REST API for programmatic access + browser UI for humans

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Browser UI

| URL | Description |
|-----|-------------|
| `/` | Truck list |
| `/trucks/<id>/` | Truck detail + location history + ping form |
| `/trucks/new/` | Add truck (admin only) |
| `/trucks/<id>/edit/` | Edit truck (admin only) |
| `/login/` | Login |
| `/admin/` | Django admin panel |

## REST API

All endpoints return JSON. Authenticate with JWT Bearer token.

### Auth

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register/` | `{username, password, role, email?}` | Register |
| POST | `/api/auth/login/` | `{username, password}` | Returns access + refresh tokens |
| POST | `/api/auth/refresh/` | `{refresh}` | Refresh access token |
| GET | `/api/auth/me/` | — | Current user info |

### Trucks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/trucks/` | List (drivers see only assigned) |
| POST | `/api/trucks/` | Create (admin only) |
| GET | `/api/trucks/<id>/` | Detail (includes 10 latest locations) |
| PUT/PATCH | `/api/trucks/<id>/` | Update (admin only) |
| DELETE | `/api/trucks/<id>/` | Delete (admin only) |
| GET | `/api/trucks/<id>/locations/` | Paginated location history |
| GET | `/api/trucks/<id>/recent_locations/` | Last 10 pings |

### Locations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/locations/` | Report a ping `{truck, latitude, longitude, speed?, note?}` |
| GET | `/api/locations/?truck=X` | Filtered location list |

**Query params for trucks:** `?active=true&plate=AB`

## Roles

- **admin** — Full CRUD on trucks, can ping any truck
- **driver** — Read-only on assigned truck, can only ping their own truck

## Tech

- **Django 6.0** + **Django REST Framework 3.17**
- **SimpleJWT** authentication
- **SQLite** (dev), easily swappable to PostgreSQL
- **Bootstrap 5** for browser UI

## DB Schema

![schema image](https://github.com/Shadow1088/django-project/blob/main/schema.png)

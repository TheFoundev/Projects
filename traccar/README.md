# Traccar GPS Tracking

A compact fleet-tracking service: register devices, ingest positions, draw
trails on a live map, compute trips and trigger geofence alerts.

Built as an original Foundev implementation of the GPS-tracking product space.
The domain model and HTTP API are ours; see `LICENSE` and the notes below.

## Features

- Device registry with online/offline status and last-seen timestamps
- Position ingestion with coordinate validation
- Latest position per device and recent trail history
- Trip detection from position gaps, with distance, duration and average speed
- Circular geofences with entry alerts
- Live Leaflet map, device list, trip summary and alert feed
- H2 by default for zero-setup demos; PostgreSQL profile for deployment
- Haversine unit tests

## Stack

`Java; React; PostgreSQL; Docker` — this implementation uses Java 21 +
Spring Boot, a dependency-free browser client with Leaflet, and both H2 and
PostgreSQL. It stays close to the backend stack; the client is intentionally
plain JavaScript rather than a React build step so the jar is self-contained.

## Run

```bash
mvn spring-boot:run
# open http://localhost:8080
mvn test
```

No database is required: the default profile uses in-memory H2 and seeds three
demo devices. Data resets when the process stops.

### PostgreSQL

```bash
docker compose up --build
# app:      http://localhost:8080
# postgres: localhost:5432 (traccar/traccar)
```

Or point the app at any PostgreSQL instance:

```bash
export SPRING_DATASOURCE_URL='jdbc:postgresql://localhost:5432/traccar'
export SPRING_DATASOURCE_USERNAME=traccar
export SPRING_DATASOURCE_PASSWORD=secret
export SPRING_DATASOURCE_DRIVER=org.postgresql.Driver
mvn spring-boot:run
```

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/devices` | list devices |
| POST | `/api/devices` | register `{name, uniqueId, model}` |
| PUT | `/api/devices/{id}` | update name/status/model |
| DELETE | `/api/devices/{id}` | remove a device |
| POST | `/api/positions` | ingest `{deviceId, latitude, longitude, speedKph}` |
| GET | `/api/positions/latest` | latest position per device |
| GET | `/api/positions?deviceId=&limit=` | recent positions |
| GET | `/api/trips?deviceId=&from=&to=` | computed trips |
| GET/POST | `/api/geofences` | circular fences |
| GET | `/api/alerts` | recent geofence alerts |
| GET | `/api/summary` | dashboard counters |

Example:

```bash
curl -X POST localhost:8080/api/positions \
  -H 'Content-Type: application/json' \
  -d '{"deviceId":1,"latitude":51.51,"longitude":-0.12,"speedKph":22}'
```

## Structure

```text
traccar/
├── pom.xml
├── src/main/java/dev/foundev/traccar/
│   ├── TraccarApplication.java   app + demo seed
│   ├── domain/                   Device, Position, Geofence, Alert
│   ├── repo/                     Spring Data repositories
│   ├── service/                  distance, ingestion, trip detection
│   └── web/                      REST API and error handling
├── src/main/resources/
│   ├── application.properties
│   └── static/                   Leaflet map client
├── src/test/java/                Haversine tests and the tracking behaviour tests
├── Dockerfile
└── docker-compose.yml
```

## Testing

```bash
mvn test        # 13 tests: the Haversine helper and the tracking behaviour
```

`TrackingServiceBehaviourTest` covers the behaviour of the service with
mocked repositories: a recorded position marks the device online, an unknown
device and out-of-range coordinates are refused, a position inside a geofence
raises an alert (and one outside raises none), and the trip detection splits
the trail on a gap of more than twenty minutes, on a jump of more than five
kilometres and not at all when the device stands still.

## Notes and limitations

- Authentication, tenants and per-user permissions are not included; put the
  API behind an authenticating proxy before exposing it.
- The tracker protocols (OsmAnd, GT06, Teltonika, etc.) are not implemented;
  positions are accepted over the HTTP JSON API.
- Geofence alerts are emitted on every position inside a fence, without
  enter/exit state or notification delivery.
- Trips are split by a 20-minute gap or a 5 km jump between points; this is a
  practical heuristic, not map matching.
- Map tiles require internet access. The demo is not a replacement for a
  production dispatch system.

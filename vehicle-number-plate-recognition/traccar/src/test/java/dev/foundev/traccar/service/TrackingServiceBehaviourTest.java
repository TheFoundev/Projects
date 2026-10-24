package dev.foundev.traccar.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import dev.foundev.traccar.domain.Alert;
import dev.foundev.traccar.domain.Device;
import dev.foundev.traccar.domain.Geofence;
import dev.foundev.traccar.domain.Position;
import dev.foundev.traccar.repo.AlertRepository;
import dev.foundev.traccar.repo.DeviceRepository;
import dev.foundev.traccar.repo.GeofenceRepository;
import dev.foundev.traccar.repo.PositionRepository;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

/** The behaviour of the tracking service: the trips, the fences and the status. */
class TrackingServiceBehaviourTest {

    private DeviceRepository devices;
    private PositionRepository positions;
    private GeofenceRepository geofences;
    private AlertRepository alerts;
    private TrackingService service;

    @BeforeEach
    void setUp() {
        devices = mock(DeviceRepository.class);
        positions = mock(PositionRepository.class);
        geofences = mock(GeofenceRepository.class);
        alerts = mock(AlertRepository.class);
        service = new TrackingService(devices, positions, geofences, alerts);
        when(geofences.findByActiveTrue()).thenReturn(List.of());
        when(positions.save(any(Position.class))).thenAnswer(call -> {
            Position saved = call.getArgument(0);
            if (saved.getId() == null) {
                saved.setId(1L);
            }
            return saved;
        });
        when(devices.save(any(Device.class))).thenAnswer(call -> call.getArgument(0));
    }

    private Device knownDevice() {
        Device device = new Device("Delivery van", "VAN-1042", "Teltonika FMB920");
        device.setId(7L);
        when(devices.findById(7L)).thenReturn(Optional.of(device));
        return device;
    }

    private Position point(double lat, double lon, Instant when) {
        Position position = new Position();
        position.setLatitude(lat);
        position.setLongitude(lon);
        position.setRecordedAt(when);
        return position;
    }

    @Test
    void recordingAPositionMarksTheDeviceOnline() {
        Device device = knownDevice();
        Instant stamp = Instant.parse("2026-02-01T10:00:00Z");

        Position saved = service.record(7L, point(51.5, -0.12, stamp));

        assertNotNull(saved);
        assertEquals("online", device.getStatus());
        assertEquals(stamp, device.getLastUpdate());
        verify(devices).save(device);
    }

    @Test
    void recordingForAnUnknownDeviceIsRefused() {
        when(devices.findById(99L)).thenReturn(Optional.empty());
        IllegalArgumentException problem = assertThrows(IllegalArgumentException.class,
                () -> service.record(99L, point(51.5, -0.12, Instant.now())));
        assertTrue(problem.getMessage().contains("not found"));
    }

    @Test
    void coordinatesOutOfRangeAreRefused() {
        knownDevice();
        assertThrows(IllegalArgumentException.class,
                () -> service.record(7L, point(91.0, -0.12, Instant.now())));
        assertThrows(IllegalArgumentException.class,
                () -> service.record(7L, point(51.5, 181.0, Instant.now())));
    }

    @Test
    void aPositionInsideAGeofenceRaisesAnAlert() {
        Device device = knownDevice();
        Geofence fence = new Geofence();
        fence.setName("Depot");
        fence.setLatitude(51.5000);
        fence.setLongitude(-0.1200);
        fence.setRadiusMeters(500);
        fence.setActive(true);
        when(geofences.findByActiveTrue()).thenReturn(List.of(fence));

        service.record(7L, point(51.5005, -0.1200, Instant.now()));

        verify(alerts).save(any(Alert.class));
    }

    @Test
    void aPositionFarFromTheGeofenceRaisesNothing() {
        knownDevice();
        Geofence fence = new Geofence();
        fence.setName("Depot");
        fence.setLatitude(51.5000);
        fence.setLongitude(-0.1200);
        fence.setRadiusMeters(500);
        fence.setActive(true);
        when(geofences.findByActiveTrue()).thenReturn(List.of(fence));

        service.record(7L, point(52.5000, -0.1200, Instant.now()));

        verify(alerts, never()).save(any(Alert.class));
    }

    @Test
    void aGapOfMoreThanTwentyMinutesBreaksTheTrip() {
        Instant start = Instant.parse("2026-02-01T08:00:00Z");
        List<Position> points = new ArrayList<>();
        points.add(point(51.5000, -0.1200, start));
        points.add(point(51.5100, -0.1200, start.plus(5, ChronoUnit.MINUTES)));
        points.add(point(51.5200, -0.1200, start.plus(90, ChronoUnit.MINUTES)));
        points.add(point(51.5300, -0.1200, start.plus(95, ChronoUnit.MINUTES)));
        when(positions.findByDeviceIdOrderByRecordedAtAsc(7L)).thenReturn(points);

        List<TrackingService.Trip> trips = service.trips(7L, null, null);

        assertEquals(2, trips.size());
        assertEquals(5, trips.get(0).durationMinutes());
        assertEquals(5, trips.get(1).durationMinutes());
    }

    @Test
    void aLongJumpBreaksTheTrip() {
        Instant start = Instant.parse("2026-02-01T08:00:00Z");
        List<Position> points = new ArrayList<>();
        points.add(point(51.5000, -0.1200, start));
        points.add(point(51.5100, -0.1200, start.plus(2, ChronoUnit.MINUTES)));
        // More than five kilometres away in one minute.
        points.add(point(51.6000, -0.1200, start.plus(3, ChronoUnit.MINUTES)));
        when(positions.findByDeviceIdOrderByRecordedAtAsc(7L)).thenReturn(points);

        List<TrackingService.Trip> trips = service.trips(7L, null, null);

        assertEquals(1, trips.size());
    }

    @Test
    void aStationaryDeviceHasNoTrip() {
        Instant start = Instant.parse("2026-02-01T08:00:00Z");
        List<Position> points = new ArrayList<>();
        points.add(point(51.5000, -0.1200, start));
        points.add(point(51.5000, -0.1200, start.plus(1, ChronoUnit.MINUTES)));
        when(positions.findByDeviceIdOrderByRecordedAtAsc(7L)).thenReturn(points);

        assertTrue(service.trips(7L, null, null).isEmpty());
    }

    @Test
    void aSinglePointIsNotATrip() {
        Instant start = Instant.parse("2026-02-01T08:00:00Z");
        when(positions.findByDeviceIdOrderByRecordedAtAsc(7L))
                .thenReturn(List.of(point(51.5000, -0.1200, start)));

        assertTrue(service.trips(7L, null, null).isEmpty());
    }

    @Test
    void theTripCarriesTheDistanceAndTheAverageSpeed() {
        Instant start = Instant.parse("2026-02-01T08:00:00Z");
        List<Position> points = new ArrayList<>();
        points.add(point(51.5000, -0.1200, start));
        points.add(point(51.5100, -0.1200, start.plus(10, ChronoUnit.MINUTES)));
        when(positions.findByDeviceIdOrderByRecordedAtAsc(7L)).thenReturn(points);

        TrackingService.Trip trip = service.trips(7L, null, null).get(0);

        assertEquals(10, trip.durationMinutes());
        assertTrue(trip.distanceKm() > 1.0 && trip.distanceKm() < 1.2, "got " + trip.distanceKm());
        assertTrue(trip.avgSpeedKph() > 6.0 && trip.avgSpeedKph() < 7.5, "got " + trip.avgSpeedKph());
    }
}

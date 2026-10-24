package dev.foundev.traccar.service;

import dev.foundev.traccar.domain.Alert;
import dev.foundev.traccar.domain.Device;
import dev.foundev.traccar.domain.Geofence;
import dev.foundev.traccar.domain.Position;
import dev.foundev.traccar.repo.AlertRepository;
import dev.foundev.traccar.repo.DeviceRepository;
import dev.foundev.traccar.repo.GeofenceRepository;
import dev.foundev.traccar.repo.PositionRepository;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class TrackingService {

    public record Trip(Instant start, Instant end, double distanceKm, long durationMinutes, double avgSpeedKph) {
    }

    private final DeviceRepository devices;
    private final PositionRepository positions;
    private final GeofenceRepository geofences;
    private final AlertRepository alerts;

    public TrackingService(DeviceRepository devices, PositionRepository positions,
                           GeofenceRepository geofences, AlertRepository alerts) {
        this.devices = devices;
        this.positions = positions;
        this.geofences = geofences;
        this.alerts = alerts;
    }

    /** Great-circle distance in kilometres. */
    public static double haversineKm(double lat1, double lon1, double lat2, double lon2) {
        final double earthRadiusKm = 6371.0088;
        double dLat = Math.toRadians(lat2 - lat1);
        double dLon = Math.toRadians(lon2 - lon1);
        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2)
                + Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2))
                * Math.sin(dLon / 2) * Math.sin(dLon / 2);
        return earthRadiusKm * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }

    @Transactional
    public Position record(Long deviceId, Position position) {
        Device device = devices.findById(deviceId)
                .orElseThrow(() -> new IllegalArgumentException("Device " + deviceId + " not found"));
        if (position.getRecordedAt() == null) {
            position.setRecordedAt(Instant.now());
        }
        if (position.getLatitude() < -90 || position.getLatitude() > 90
                || position.getLongitude() < -180 || position.getLongitude() > 180) {
            throw new IllegalArgumentException("Coordinates are out of range");
        }
        Position saved = positions.save(position);
        device.setStatus("online");
        device.setLastUpdate(saved.getRecordedAt());
        devices.save(device);

        for (Geofence fence : geofences.findByActiveTrue()) {
            double distanceKm = haversineKm(saved.getLatitude(), saved.getLongitude(),
                    fence.getLatitude(), fence.getLongitude());
            if (distanceKm * 1000 <= fence.getRadiusMeters()) {
                alerts.save(new Alert(deviceId, "geofence",
                        device.getName() + " entered " + fence.getName()));
            }
        }
        return saved;
    }

    @Transactional(readOnly = true)
    public List<Trip> trips(Long deviceId, Instant from, Instant to) {
        List<Position> points;
        if (from != null && to != null) {
            points = positions.findByDeviceIdAndRecordedAtBetweenOrderByRecordedAtAsc(deviceId, from, to);
        } else {
            points = positions.findByDeviceIdOrderByRecordedAtAsc(deviceId);
        }
        List<Trip> trips = new ArrayList<>();
        if (points.size() < 2) {
            return trips;
        }
        int start = 0;
        for (int i = 1; i < points.size(); i++) {
            Position previous = points.get(i - 1);
            Position current = points.get(i);
            long gapMinutes = Duration.between(previous.getRecordedAt(), current.getRecordedAt()).toMinutes();
            double segmentKm = haversineKm(previous.getLatitude(), previous.getLongitude(),
                    current.getLatitude(), current.getLongitude());
            boolean breakTrip = gapMinutes > 20 || segmentKm > 5.0;
            if (breakTrip) {
                addTrip(trips, points.subList(start, i));
                start = i;
            }
        }
        addTrip(trips, points.subList(start, points.size()));
        return trips;
    }

    private void addTrip(List<Trip> trips, List<Position> points) {
        if (points.size() < 2) {
            return;
        }
        double distance = 0;
        for (int i = 1; i < points.size(); i++) {
            Position a = points.get(i - 1);
            Position b = points.get(i);
            distance += haversineKm(a.getLatitude(), a.getLongitude(), b.getLatitude(), b.getLongitude());
        }
        Instant start = points.get(0).getRecordedAt();
        Instant end = points.get(points.size() - 1).getRecordedAt();
        long minutes = Math.max(1, Duration.between(start, end).toMinutes());
        if (distance < 0.05) {
            return;
        }
        trips.add(new Trip(start, end, round(distance), minutes, round(distance / (minutes / 60.0))));
    }

    private static double round(double value) {
        return Math.round(value * 100.0) / 100.0;
    }
}

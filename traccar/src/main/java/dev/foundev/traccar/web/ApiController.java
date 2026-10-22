package dev.foundev.traccar.web;

import dev.foundev.traccar.domain.Alert;
import dev.foundev.traccar.domain.Device;
import dev.foundev.traccar.domain.Geofence;
import dev.foundev.traccar.domain.Position;
import dev.foundev.traccar.repo.AlertRepository;
import dev.foundev.traccar.repo.DeviceRepository;
import dev.foundev.traccar.repo.GeofenceRepository;
import dev.foundev.traccar.repo.PositionRepository;
import dev.foundev.traccar.service.TrackingService;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
@CrossOrigin
public class ApiController {

    public record DeviceRequest(String name, String uniqueId, String model, String status) {
    }

    private final DeviceRepository devices;
    private final PositionRepository positions;
    private final GeofenceRepository geofences;
    private final AlertRepository alerts;
    private final TrackingService tracking;

    public ApiController(DeviceRepository devices, PositionRepository positions,
                         GeofenceRepository geofences, AlertRepository alerts, TrackingService tracking) {
        this.devices = devices;
        this.positions = positions;
        this.geofences = geofences;
        this.alerts = alerts;
        this.tracking = tracking;
    }

    @GetMapping("/devices")
    public List<Device> devices() {
        return devices.findAll();
    }

    @PostMapping("/devices")
    @ResponseStatus(HttpStatus.CREATED)
    public Device createDevice(@RequestBody DeviceRequest request) {
        if (request.name() == null || request.name().isBlank()
                || request.uniqueId() == null || request.uniqueId().isBlank()) {
            throw new IllegalArgumentException("name and uniqueId are required");
        }
        devices.findByUniqueId(request.uniqueId()).ifPresent(existing -> {
            throw new IllegalArgumentException("uniqueId is already registered");
        });
        Device device = new Device(request.name().trim(), request.uniqueId().trim(), request.model());
        if (request.status() != null && !request.status().isBlank()) {
            device.setStatus(request.status());
        }
        return devices.save(device);
    }

    @PutMapping("/devices/{id}")
    public Device updateDevice(@PathVariable Long id, @RequestBody DeviceRequest request) {
        Device device = devices.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Device not found"));
        if (request.name() != null && !request.name().isBlank()) {
            device.setName(request.name().trim());
        }
        if (request.status() != null && !request.status().isBlank()) {
            device.setStatus(request.status());
        }
        if (request.model() != null) {
            device.setModel(request.model());
        }
        return devices.save(device);
    }

    @DeleteMapping("/devices/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteDevice(@PathVariable Long id) {
        devices.deleteById(id);
    }

    @PostMapping("/positions")
    @ResponseStatus(HttpStatus.CREATED)
    public Position recordPosition(@RequestBody Position position) {
        if (position.getDeviceId() == null) {
            throw new IllegalArgumentException("deviceId is required");
        }
        return tracking.record(position.getDeviceId(), position);
    }

    @GetMapping("/positions/latest")
    public List<Position> latest() {
        return devices.findAll().stream()
                .map(device -> positions.findFirstByDeviceIdOrderByRecordedAtDesc(device.getId()).orElse(null))
                .filter(java.util.Objects::nonNull)
                .toList();
    }

    @GetMapping("/positions")
    public List<Position> positionsFor(@RequestParam Long deviceId,
                                       @RequestParam(defaultValue = "100") int limit) {
        int size = Math.max(1, Math.min(limit, 1000));
        return positions.findByDeviceIdOrderByRecordedAtDesc(deviceId, PageRequest.of(0, size));
    }

    @GetMapping("/trips")
    public List<TrackingService.Trip> trips(@RequestParam Long deviceId,
                                            @RequestParam(required = false) Instant from,
                                            @RequestParam(required = false) Instant to) {
        return tracking.trips(deviceId, from, to);
    }

    @GetMapping("/geofences")
    public List<Geofence> geofences() {
        return geofences.findAll();
    }

    @PostMapping("/geofences")
    @ResponseStatus(HttpStatus.CREATED)
    public Geofence createGeofence(@RequestBody Geofence fence) {
        if (fence.getName() == null || fence.getName().isBlank() || fence.getRadiusMeters() <= 0) {
            throw new IllegalArgumentException("name and a positive radiusMeters are required");
        }
        return geofences.save(fence);
    }

    @DeleteMapping("/geofences/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteGeofence(@PathVariable Long id) {
        geofences.deleteById(id);
    }

    @GetMapping("/alerts")
    public List<Alert> alerts(@RequestParam(required = false) Long deviceId) {
        return deviceId == null
                ? alerts.findTop50ByOrderByCreatedAtDesc()
                : alerts.findTop50ByDeviceIdOrderByCreatedAtDesc(deviceId);
    }

    @GetMapping("/summary")
    public Map<String, Object> summary() {
        Instant today = Instant.now().truncatedTo(ChronoUnit.DAYS);
        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("devices", devices.count());
        summary.put("online", devices.countByStatus("online"));
        summary.put("positionsToday", positions.countByRecordedAtAfter(today));
        summary.put("alertsToday", alerts.countByCreatedAtAfter(today));
        summary.put("geofences", geofences.count());
        return summary;
    }
}

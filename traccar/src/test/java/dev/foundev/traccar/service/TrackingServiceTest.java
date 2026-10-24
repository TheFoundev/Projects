package dev.foundev.traccar.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class TrackingServiceTest {

    @Test
    void haversineMatchesKnownDistance() {
        // London to Paris is roughly 343 km.
        double km = TrackingService.haversineKm(51.5074, -0.1278, 48.8566, 2.3522);
        assertEquals(343.0, km, 5.0);
    }

    @Test
    void haversineIsZeroForSamePoint() {
        assertEquals(0.0, TrackingService.haversineKm(40.0, -74.0, 40.0, -74.0), 0.0001);
    }

    @Test
    void shortHopIsSensible() {
        // 0.01 degrees of latitude is about 1.11 km.
        double km = TrackingService.haversineKm(51.5000, -0.1200, 51.5100, -0.1200);
        assertTrue(km > 1.0 && km < 1.2, "expected about 1.11 km, got " + km);
    }
}

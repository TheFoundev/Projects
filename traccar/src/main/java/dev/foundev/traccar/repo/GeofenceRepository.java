package dev.foundev.traccar.repo;

import dev.foundev.traccar.domain.Geofence;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface GeofenceRepository extends JpaRepository<Geofence, Long> {
    List<Geofence> findByActiveTrue();
}

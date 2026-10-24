package dev.foundev.traccar.repo;

import dev.foundev.traccar.domain.Device;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DeviceRepository extends JpaRepository<Device, Long> {
    Optional<Device> findByUniqueId(String uniqueId);

    long countByStatus(String status);
}

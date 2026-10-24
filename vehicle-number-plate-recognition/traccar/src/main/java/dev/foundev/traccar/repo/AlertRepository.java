package dev.foundev.traccar.repo;

import dev.foundev.traccar.domain.Alert;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AlertRepository extends JpaRepository<Alert, Long> {
    List<Alert> findTop50ByOrderByCreatedAtDesc();

    List<Alert> findTop50ByDeviceIdOrderByCreatedAtDesc(Long deviceId);

    long countByCreatedAtAfter(java.time.Instant since);
}

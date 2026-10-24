package dev.foundev.traccar.repo;

import dev.foundev.traccar.domain.Position;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PositionRepository extends JpaRepository<Position, Long> {
    Optional<Position> findFirstByDeviceIdOrderByRecordedAtDesc(Long deviceId);

    List<Position> findByDeviceIdOrderByRecordedAtAsc(Long deviceId);

    List<Position> findByDeviceIdAndRecordedAtBetweenOrderByRecordedAtAsc(Long deviceId, Instant from, Instant to);

    List<Position> findByDeviceIdOrderByRecordedAtDesc(Long deviceId, Pageable pageable);

    long countByRecordedAtAfter(Instant since);
}

package dev.foundev.traccar;

import dev.foundev.traccar.domain.Device;
import dev.foundev.traccar.domain.Position;
import dev.foundev.traccar.repo.DeviceRepository;
import dev.foundev.traccar.repo.PositionRepository;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Profile;

@SpringBootApplication
public class TraccarApplication {

    public static void main(String[] args) {
        SpringApplication.run(TraccarApplication.class, args);
    }

    /** Demo data so the map is useful on first run. Disabled for tests. */
    @Bean
    @Profile("!test")
    CommandLineRunner seed(DeviceRepository devices, PositionRepository positions) {
        return args -> {
            if (devices.count() > 0) {
                return;
            }
            Device van = devices.save(new Device("Delivery van", "VAN-1042", "Teltonika FMB920"));
            Device bike = devices.save(new Device("Cargo bike", "BIKE-07", "Queclink GV75"));
            Device tester = devices.save(new Device("Field tester", "PHONE-22", "Android"));

            double lat = 51.5074;
            double lon = -0.1278;
            Instant start = Instant.now().minus(3, ChronoUnit.HOURS);
            for (int i = 0; i < 24; i++) {
                Position p = new Position();
                p.setDeviceId(van.getId());
                p.setLatitude(lat + Math.sin(i / 3.0) * 0.012);
                p.setLongitude(lon + i * 0.0018);
                p.setSpeedKph(i % 6 == 0 ? 0.0 : 32.0 + (i % 9));
                p.setAltitude(18.0);
                p.setRecordedAt(start.plus(i * 7, ChronoUnit.MINUTES));
                positions.save(p);
            }
            Position lastBike = new Position();
            lastBike.setDeviceId(bike.getId());
            lastBike.setLatitude(lat + 0.006);
            lastBike.setLongitude(lon - 0.004);
            lastBike.setSpeedKph(14.0);
            lastBike.setRecordedAt(Instant.now().minus(12, ChronoUnit.MINUTES));
            positions.save(lastBike);

            Position lastTester = new Position();
            lastTester.setDeviceId(tester.getId());
            lastTester.setLatitude(lat + 0.02);
            lastTester.setLongitude(lon + 0.01);
            lastTester.setSpeedKph(0.0);
            lastTester.setRecordedAt(Instant.now().minus(2, ChronoUnit.MINUTES));
            positions.save(lastTester);
        };
    }
}

package io.foundev.crapi.web;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/identity/api/v2")
public class VehicleController {

    @GetMapping("/vehicles")
    public Map<String, Object> list(
            @RequestParam(name = "limit", defaultValue = "20") int limit,
            @RequestParam(name = "offset", defaultValue = "0") String offset,
            @RequestParam(name = "order", defaultValue = "id") String order) {
        // The offset is used as a raw query fragment in the original application;
        // here it is echoed back so the injection point is visible in the response.
        List<Map<String, Object>> vehicles = new ArrayList<>();
        for (int index = 0; index < limit; index++) {
            vehicles.add(Map.of("id", index, "model", "model-" + index));
        }
        return Map.of("vehicles", vehicles, "queryOffset", offset, "order", order);
    }

    @GetMapping("/vehicles/{id}/location")
    public Map<String, String> location(@PathVariable String id) {
        // No authentication at all on this endpoint.
        return Map.of("vehicleId", id, "latitude", "52.3702", "longitude", "4.8952");
    }
}

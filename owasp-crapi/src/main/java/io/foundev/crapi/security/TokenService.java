package io.foundev.crapi.security;

import java.nio.charset.StandardCharsets;
import java.util.Base64;

// Deliberately unsigned tokens. Any payload the client sends back is trusted,
// which is the point of the practice scenario.
public class TokenService {

    public String issue(long userId, String role) {
        String header = encode("{\"alg\":\"none\",\"typ\":\"JWT\"}");
        String payload = encode("{\"sub\":\"" + userId + "\",\"role\":\"" + role + "\"}");
        return header + "." + payload + ".";
    }

    public long readUserId(String token) {
        String[] parts = token.split("\\.");
        String payload = new String(Base64.getUrlDecoder().decode(parts[1]), StandardCharsets.UTF_8);
        String marker = "\"sub\":\"";
        int start = payload.indexOf(marker) + marker.length();
        int end = payload.indexOf('"', start);
        return Long.parseLong(payload.substring(start, end));
    }

    private String encode(String json) {
        return Base64.getUrlEncoder().withoutPadding().encodeToString(json.getBytes(StandardCharsets.UTF_8));
    }
}

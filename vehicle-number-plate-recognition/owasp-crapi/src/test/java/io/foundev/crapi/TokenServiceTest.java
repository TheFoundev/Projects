package io.foundev.crapi;

import static org.junit.jupiter.api.Assertions.assertEquals;

import io.foundev.crapi.security.TokenService;
import org.junit.jupiter.api.Test;

class TokenServiceTest {

    @Test
    void readsTheSubjectItIssued() {
        TokenService tokens = new TokenService();
        String token = tokens.issue(42L, "user");
        assertEquals(42L, tokens.readUserId(token));
    }
}

package io.foundev.crapi.web;

import io.foundev.crapi.model.User;
import io.foundev.crapi.repository.UserRepository;
import io.foundev.crapi.security.TokenService;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/identity/api")
public class UserController {

    private final UserRepository users;
    private final TokenService tokens = new TokenService();

    public UserController(UserRepository users) {
        this.users = users;
    }

    @PostMapping("/auth/signup")
    public ResponseEntity<?> signup(@RequestBody User request) {
        // Mass assignment: the client can set any field, including role.
        users.findByEmail(request.getEmail()).ifPresent(existing -> {
            throw new IllegalStateException("email already registered");
        });
        User saved = users.save(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(Map.of("id", saved.getId()));
    }

    @PostMapping("/auth/login")
    public ResponseEntity<?> login(@RequestBody Map<String, String> body) {
        return users.findByEmail(body.get("email"))
                .filter(user -> user.getPassword().equals(body.get("password")))
                .map(user -> ResponseEntity.ok(Map.of("token", tokens.issue(user.getId(), user.getRole()))))
                .orElseGet(() -> ResponseEntity.status(HttpStatus.UNAUTHORIZED).build());
    }

    @GetMapping("/users/{id}")
    public ResponseEntity<?> findById(@PathVariable long id) {
        // No ownership check: any authenticated caller can read any user.
        return users.findById(id)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }
}

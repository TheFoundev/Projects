// Thunderdome Planning Poker - real-time agile collaboration.
//
// A small, dependency-free Go server that keeps sessions in memory and pushes
// changes to browsers over server-sent events. It supports planning poker,
// retrospectives and daily standups.
package main

import (
	"crypto/rand"
	"embed"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"io/fs"
	"log"
	"net/http"
	"sort"
	"strings"
	"sync"
	"time"
)

//go:embed static/*
var staticFiles embed.FS

type Participant struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	Role      string    `json:"role"`
	JoinedAt  time.Time `json:"joined_at"`
	Connected bool      `json:"connected"`
}

type Story struct {
	ID       string            `json:"id"`
	Title    string            `json:"title"`
	Votes    map[string]string `json:"votes"`
	Revealed bool              `json:"revealed"`
	Created  time.Time         `json:"created_at"`
}

type Note struct {
	ID      string    `json:"id"`
	Column  string    `json:"column"`
	Body    string    `json:"body"`
	Author  string    `json:"author"`
	Created time.Time `json:"created_at"`
}

type Session struct {
	ID string `json:"id"`
	// FacilitatorToken is the token of the one who may reveal the cards and
	// may close the session.
	FacilitatorToken string         `json:"-"`
	Name             string         `json:"name"`
	Mode             string         `json:"mode"`
	Participants     []*Participant `json:"participants"`
	Stories          []*Story       `json:"stories"`
	Notes            []*Note        `json:"notes"`
	Created          time.Time      `json:"created_at"`
	Updated          time.Time      `json:"updated_at"`
}

type Store struct {
	mu       sync.RWMutex
	sessions map[string]*Session
	clients  map[string]map[chan []byte]struct{}
}

func NewStore() *Store {
	return &Store{sessions: map[string]*Session{}, clients: map[string]map[chan []byte]struct{}{}}
}

func newID() string {
	buf := make([]byte, 5)
	if _, err := rand.Read(buf); err != nil {
		return fmt.Sprintf("%d", time.Now().UnixNano()%1_000_000)
	}
	return hex.EncodeToString(buf)
}

func (s *Store) Create(name, mode string) *Session {
	s.mu.Lock()
	defer s.mu.Unlock()
	id := newID()
	for s.sessions[id] != nil {
		id = newID()
	}
	session := &Session{
		ID: id, Name: name, Mode: mode, Created: time.Now().UTC(), Updated: time.Now().UTC(),
		// The token of the facilitator, so only they may reveal the cards.
		FacilitatorToken: newID() + newID(),
		Participants:     []*Participant{}, Stories: []*Story{}, Notes: []*Note{},
	}
	s.sessions[id] = session
	s.broadcastLocked(id)
	return session
}

func (s *Store) Get(id string) *Session {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.sessions[id]
}

func (s *Store) mutate(id string, fn func(*Session) error) (*Session, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	session := s.sessions[id]
	if session == nil {
		return nil, fmt.Errorf("session not found")
	}
	if err := fn(session); err != nil {
		return nil, err
	}
	session.Updated = time.Now().UTC()
	s.broadcastLocked(id)
	return session, nil
}

// Summary is the state of the running instance: it feeds the home page.
func (s *Store) Summary() map[string]any {
	s.mu.RLock()
	defer s.mu.RUnlock()
	participants := 0
	cards := 0
	modes := map[string]int{}
	for _, session := range s.sessions {
		participants += len(session.Participants)
		modes[session.Mode]++
		for _, story := range session.Stories {
			cards += len(story.Votes)
		}
	}
	list := make([]map[string]any, 0, len(s.sessions))
	for _, session := range s.sessions {
		list = append(list, map[string]any{
			"name":         session.Name,
			"mode":         session.Mode,
			"participants": len(session.Participants),
			"stories":      len(session.Stories),
			"revealed":     session.Stories[0].Revealed && len(session.Stories) > 0,
		})
	}
	sort.Slice(list, func(i, j int) bool {
		return list[i]["name"].(string) < list[j]["name"].(string)
	})
	return map[string]any{
		"stats": map[string]any{
			"sessions":     len(s.sessions),
			"participants": participants,
			"cards":        cards,
		},
		"series": []map[string]any{
			{"label": "planning", "value": modes["planning"]},
			{"label": "retro", "value": modes["retro"]},
			{"label": "standup", "value": modes["standup"]},
		},
		"lists": map[string]any{"sessions": list},
	}
}

func (s *Store) Subscribe(id string) (chan []byte, func()) {
	s.mu.Lock()
	defer s.mu.Unlock()
	ch := make(chan []byte, 8)
	if s.clients[id] == nil {
		s.clients[id] = map[chan []byte]struct{}{}
	}
	s.clients[id][ch] = struct{}{}
	cancel := func() {
		s.mu.Lock()
		defer s.mu.Unlock()
		if set := s.clients[id]; set != nil {
			if _, ok := set[ch]; ok {
				delete(set, ch)
				close(ch)
			}
			if len(set) == 0 {
				delete(s.clients, id)
			}
		}
	}
	return ch, cancel
}

func (s *Store) broadcastLocked(id string) {
	payload := []byte(`{"type":"update"}`)
	for ch := range s.clients[id] {
		select {
		case ch <- payload:
		default:
		}
	}
}

func writeJSON(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(value)
}

func readJSON(r *http.Request, target any) error {
	defer r.Body.Close()
	decoder := json.NewDecoder(io.LimitReader(r.Body, 1<<20))
	decoder.DisallowUnknownFields()
	return decoder.Decode(target)
}

func fail(w http.ResponseWriter, status int, message string) {
	writeJSON(w, status, map[string]string{"error": message})
}

func mainHandler(store *Store) http.Handler {
	mux := http.NewServeMux()

	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	})

	mux.HandleFunc("GET /api/summary", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, store.Summary())
	})

	mux.HandleFunc("POST /api/sessions", func(w http.ResponseWriter, r *http.Request) {
		var body struct {
			Name string `json:"name"`
			Mode string `json:"mode"`
		}
		if err := readJSON(r, &body); err != nil {
			fail(w, http.StatusBadRequest, "invalid JSON body")
			return
		}
		body.Name = strings.TrimSpace(body.Name)
		if body.Name == "" {
			fail(w, http.StatusBadRequest, "a session name is required")
			return
		}
		switch body.Mode {
		case "", "planning":
			body.Mode = "planning"
		case "retro", "standup":
		default:
			fail(w, http.StatusBadRequest, "mode must be planning, retro or standup")
			return
		}
		session := store.Create(body.Name, body.Mode)
		// The token of the facilitator is only given to the one who makes
		// the session, so they may reveal the cards.
		payload := map[string]any{}
		raw, _ := json.Marshal(session)
		_ = json.Unmarshal(raw, &payload)
		payload["facilitator_token"] = session.FacilitatorToken
		writeJSON(w, http.StatusCreated, payload)
	})

	mux.HandleFunc("GET /api/sessions/{id}", func(w http.ResponseWriter, r *http.Request) {
		session := store.Get(r.PathValue("id"))
		if session == nil {
			fail(w, http.StatusNotFound, "session not found")
			return
		}
		writeJSON(w, http.StatusOK, session)
	})

	mux.HandleFunc("POST /api/sessions/{id}/join", func(w http.ResponseWriter, r *http.Request) {
		var body struct {
			Name string `json:"name"`
			Role string `json:"role"`
		}
		if err := readJSON(r, &body); err != nil {
			fail(w, http.StatusBadRequest, "invalid JSON body")
			return
		}
		name := strings.TrimSpace(body.Name)
		if name == "" {
			fail(w, http.StatusBadRequest, "a display name is required")
			return
		}
		if body.Role == "" {
			body.Role = "participant"
		}
		var participant *Participant
		_, err := store.mutate(r.PathValue("id"), func(session *Session) error {
			for _, existing := range session.Participants {
				if strings.EqualFold(existing.Name, name) {
					participant = existing
					return nil
				}
			}
			if len(session.Participants) >= 60 {
				return fmt.Errorf("this session is full")
			}
			participant = &Participant{ID: newID(), Name: name, Role: body.Role, JoinedAt: time.Now().UTC(), Connected: true}
			session.Participants = append(session.Participants, participant)
			return nil
		})
		if err != nil {
			fail(w, http.StatusBadRequest, err.Error())
			return
		}
		writeJSON(w, http.StatusOK, participant)
	})

	mux.HandleFunc("POST /api/sessions/{id}/stories", func(w http.ResponseWriter, r *http.Request) {
		var body struct {
			Title string `json:"title"`
		}
		if err := readJSON(r, &body); err != nil {
			fail(w, http.StatusBadRequest, "invalid JSON body")
			return
		}
		title := strings.TrimSpace(body.Title)
		if title == "" {
			fail(w, http.StatusBadRequest, "a story title is required")
			return
		}
		var story *Story
		_, err := store.mutate(r.PathValue("id"), func(session *Session) error {
			story = &Story{ID: newID(), Title: title, Votes: map[string]string{}, Created: time.Now().UTC()}
			session.Stories = append(session.Stories, story)
			return nil
		})
		if err != nil {
			fail(w, http.StatusNotFound, err.Error())
			return
		}
		writeJSON(w, http.StatusCreated, story)
	})

	mux.HandleFunc("POST /api/sessions/{id}/vote", func(w http.ResponseWriter, r *http.Request) {
		var body struct {
			StoryID       string `json:"story_id"`
			ParticipantID string `json:"participant_id"`
			Value         string `json:"value"`
		}
		if err := readJSON(r, &body); err != nil {
			fail(w, http.StatusBadRequest, "invalid JSON body")
			return
		}
		allowed := map[string]bool{"0": true, "1": true, "2": true, "3": true, "5": true, "8": true, "13": true, "21": true, "?": true}
		if !allowed[body.Value] {
			fail(w, http.StatusBadRequest, "vote must be a Fibonacci card or ?")
			return
		}
		_, err := store.mutate(r.PathValue("id"), func(session *Session) error {
			for _, story := range session.Stories {
				if story.ID == body.StoryID {
					if story.Revealed {
						return fmt.Errorf("this story has already been revealed")
					}
					story.Votes[body.ParticipantID] = body.Value
					return nil
				}
			}
			return fmt.Errorf("story not found")
		})
		if err != nil {
			fail(w, http.StatusBadRequest, err.Error())
			return
		}
		writeJSON(w, http.StatusOK, map[string]bool{"ok": true})
	})

	mux.HandleFunc("POST /api/sessions/{id}/reveal", func(w http.ResponseWriter, r *http.Request) {
		// Only the facilitator may reveal the cards.
		if !isFacilitator(r, store) {
			fail(w, http.StatusForbidden, "only the facilitator may reveal the cards.")
			return
		}
		var body struct {
			StoryID string `json:"story_id"`
		}
		if err := readJSON(r, &body); err != nil {
			fail(w, http.StatusBadRequest, "invalid JSON body")
			return
		}
		_, err := store.mutate(r.PathValue("id"), func(session *Session) error {
			for _, story := range session.Stories {
				if story.ID == body.StoryID {
					story.Revealed = true
					return nil
				}
			}
			return fmt.Errorf("story not found")
		})
		if err != nil {
			fail(w, http.StatusBadRequest, err.Error())
			return
		}
		writeJSON(w, http.StatusOK, map[string]bool{"ok": true})
	})

	mux.HandleFunc("POST /api/sessions/{id}/reset", func(w http.ResponseWriter, r *http.Request) {
		var body struct {
			StoryID string `json:"story_id"`
		}
		if err := readJSON(r, &body); err != nil {
			fail(w, http.StatusBadRequest, "invalid JSON body")
			return
		}
		_, err := store.mutate(r.PathValue("id"), func(session *Session) error {
			for _, story := range session.Stories {
				if story.ID == body.StoryID {
					story.Votes = map[string]string{}
					story.Revealed = false
					return nil
				}
			}
			return fmt.Errorf("story not found")
		})
		if err != nil {
			fail(w, http.StatusBadRequest, err.Error())
			return
		}
		writeJSON(w, http.StatusOK, map[string]bool{"ok": true})
	})

	mux.HandleFunc("POST /api/sessions/{id}/notes", func(w http.ResponseWriter, r *http.Request) {
		var body struct {
			Column string `json:"column"`
			Body   string `json:"body"`
			Author string `json:"author"`
		}
		if err := readJSON(r, &body); err != nil {
			fail(w, http.StatusBadRequest, "invalid JSON body")
			return
		}
		body.Body = strings.TrimSpace(body.Body)
		if body.Body == "" {
			fail(w, http.StatusBadRequest, "a note body is required")
			return
		}
		if body.Column == "" {
			body.Column = "went-well"
		}
		var note *Note
		_, err := store.mutate(r.PathValue("id"), func(session *Session) error {
			note = &Note{ID: newID(), Column: body.Column, Body: body.Body, Author: body.Author, Created: time.Now().UTC()}
			session.Notes = append(session.Notes, note)
			return nil
		})
		if err != nil {
			fail(w, http.StatusNotFound, err.Error())
			return
		}
		writeJSON(w, http.StatusCreated, note)
	})

	mux.HandleFunc("GET /api/sessions/{id}/events", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		if store.Get(id) == nil {
			fail(w, http.StatusNotFound, "session not found")
			return
		}
		flusher, ok := w.(http.Flusher)
		if !ok {
			fail(w, http.StatusInternalServerError, "streaming unsupported")
			return
		}
		w.Header().Set("Content-Type", "text/event-stream")
		w.Header().Set("Cache-Control", "no-cache")
		w.Header().Set("Connection", "keep-alive")
		ch, cancel := store.Subscribe(id)
		defer cancel()
		fmt.Fprint(w, "event: ready\ndata: {}\n\n")
		flusher.Flush()
		ticker := time.NewTicker(20 * time.Second)
		defer ticker.Stop()
		for {
			select {
			case <-r.Context().Done():
				return
			case payload, open := <-ch:
				if !open {
					return
				}
				fmt.Fprintf(w, "event: change\ndata: %s\n\n", payload)
				flusher.Flush()
			case <-ticker.C:
				fmt.Fprint(w, ": ping\n\n")
				flusher.Flush()
			}
		}
	})

	static, _ := fs.Sub(staticFiles, "static")
	fileServer := http.FileServer(http.FS(static))
	mux.Handle("GET /", fileServer)
	return mux
}

// isFacilitator says whether the request comes from the facilitator of the
// session.
//
// The facilitator is the one who made the session, or the one who was given
// the token of it.
func isFacilitator(r *http.Request, store *Store) bool {
	token := ""
	if header := r.Header.Get("X-Facilitator-Token"); header != "" {
		token = header
	} else if cookie, err := r.Cookie("facilitator"); err == nil {
		token = cookie.Value
	}
	if token == "" {
		return false
	}
	session := store.Get(r.PathValue("id"))
	if session == nil {
		return false
	}
	return session.FacilitatorToken != "" && session.FacilitatorToken == token
}

func summarize(session *Session) map[string]any {
	votes := []int{}
	for _, story := range session.Stories {
		for _, value := range story.Votes {
			if value != "?" {
				var n int
				if _, err := fmt.Sscanf(value, "%d", &n); err == nil {
					votes = append(votes, n)
				}
			}
		}
	}
	sort.Ints(votes)
	return map[string]any{"votes": votes, "stories": len(session.Stories), "participants": len(session.Participants)}
}

func main() {
	store := NewStore()
	handler := mainHandler(store)
	server := &http.Server{
		Addr:              ":8080",
		Handler:           handler,
		ReadHeaderTimeout: 5 * time.Second,
	}
	log.Println("Thunderdome listening on http://localhost:8080")
	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatal(err)
	}
}

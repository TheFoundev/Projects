package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func request(t *testing.T, server *httptest.Server, method, path string, body any, facilitator ...string) (int, map[string]any) {
	t.Helper()
	var reader *bytes.Reader
	if body != nil {
		data, err := json.Marshal(body)
		if err != nil {
			t.Fatalf("marshal: %v", err)
		}
		reader = bytes.NewReader(data)
	} else {
		reader = bytes.NewReader(nil)
	}
	req, err := http.NewRequest(method, server.URL+path, reader)
	if len(facilitator) > 0 && facilitator[0] != "" {
		req.Header.Set("X-Facilitator-Token", facilitator[0])
	}
	if err != nil {
		t.Fatalf("request: %v", err)
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := server.Client().Do(req)
	if err != nil {
		t.Fatalf("do: %v", err)
	}
	defer resp.Body.Close()
	var decoded map[string]any
	_ = json.NewDecoder(resp.Body).Decode(&decoded)
	return resp.StatusCode, decoded
}

func TestPlanningSessionFlow(t *testing.T) {
	store := NewStore()
	server := httptest.NewServer(mainHandler(store))
	defer server.Close()

	status, session := request(t, server, "POST", "/api/sessions", map[string]string{"name": "Sprint 1", "mode": "planning"})
	if status != http.StatusCreated {
		t.Fatalf("create session status = %d", status)
	}
	id, _ := session["id"].(string)
	facilitator, _ := session["facilitator_token"].(string)
	if id == "" {
		t.Fatal("missing session id")
	}

	status, participant := request(t, server, "POST", "/api/sessions/"+id+"/join", map[string]string{"name": "Alex"})
	if status != http.StatusOK || participant["id"] == "" {
		t.Fatalf("join failed: %d %v", status, participant)
	}
	pid, _ := participant["id"].(string)

	status, story := request(t, server, "POST", "/api/sessions/"+id+"/stories", map[string]string{"title": "Checkout flow"})
	if status != http.StatusCreated {
		t.Fatalf("story status = %d", status)
	}
	sid, _ := story["id"].(string)

	status, _ = request(t, server, "POST", "/api/sessions/"+id+"/vote", map[string]string{
		"story_id": sid, "participant_id": pid, "value": "8",
	})
	if status != http.StatusOK {
		t.Fatalf("vote status = %d", status)
	}

	status, _ = request(t, server, "POST", "/api/sessions/"+id+"/reveal", map[string]string{"story_id": sid}, facilitator)
	if status != http.StatusOK {
		t.Fatalf("reveal status = %d", status)
	}

	status, fetched := request(t, server, "GET", "/api/sessions/"+id, nil)
	if status != http.StatusOK {
		t.Fatalf("get session status = %d", status)
	}
	stories, _ := fetched["stories"].([]any)
	if len(stories) != 1 {
		t.Fatalf("expected one story, got %d", len(stories))
	}
	first := stories[0].(map[string]any)
	if first["revealed"] != true {
		t.Fatal("story should be revealed")
	}
	votes := first["votes"].(map[string]any)
	if votes[pid] != "8" {
		t.Fatalf("expected vote 8, got %v", votes[pid])
	}
}

func TestNotesAndValidation(t *testing.T) {
	store := NewStore()
	server := httptest.NewServer(mainHandler(store))
	defer server.Close()

	status, session := request(t, server, "POST", "/api/sessions", map[string]string{"name": "Retro", "mode": "retro"})
	if status != http.StatusCreated {
		t.Fatalf("create session status = %d", status)
	}
	id := session["id"].(string)

	status, _ = request(t, server, "POST", "/api/sessions/"+id+"/notes", map[string]string{
		"column": "went-well", "body": "We shipped on time", "author": "Alex",
	})
	if status != http.StatusCreated {
		t.Fatalf("note status = %d", status)
	}

	status, _ = request(t, server, "POST", "/api/sessions/"+id+"/notes", map[string]string{"column": "went-well", "body": " "})
	if status != http.StatusBadRequest {
		t.Fatalf("blank note should be rejected, got %d", status)
	}

	status, _ = request(t, server, "POST", "/api/sessions", map[string]string{"name": "Bad", "mode": "dance"})
	if status != http.StatusBadRequest {
		t.Fatalf("invalid mode should be rejected, got %d", status)
	}
}

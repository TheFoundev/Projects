(function () {
  "use strict";

  var $ = function (sel, root) {
    return (root || document).querySelector(sel);
  };

  var els = {
    form: $("#composer-form"),
    input: $("#composer-input"),
    charCount: $("#char-count"),
    note: $("#composer-note"),
    error: $("#composer-error"),
    send: $("#send-btn"),
    stop: $("#stop-btn"),
    clearInput: $("#clear-btn"),
    thread: $("#thread"),
    banner: $("#demo-banner"),
    count: $("#thread-count"),
    exportJson: $("#export-json"),
    exportMd: $("#export-md"),
    clearThread: $("#clear-thread"),
    demoToggle: $("#demo-toggle"),
    playDemo: $("#play-demo"),
    modeHint: $("#mode-hint"),
    chips: $("#chips"),
    explorer: $("#explorer"),
    slotChat: $("#explorer-slot-chat"),
    slotFull: $("#explorer-slot-full")
  };

  if (!els.form || !els.input || !els.thread || !els.demoToggle || !els.error) {
    return;
  }

  var LS_DEMO = "campuswise.demoMode";
  var LS_TAB = "campuswise.tab";
  var MAX_CHARS = 600;

  var emptyNode = $("#empty-state");

  var reduceMotion = false;
  try {
    reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch (err) {
    reduceMotion = false;
  }

  var DEMO_SCRIPT = [
    {
      q: "What are the admission requirements?",
      a: "Admissions to the B.Tech programme follow the process recorded in the college admissions sections: candidates apply with their qualifying examination details and admission is confirmed through the notified counselling route. The knowledge base also lists the documents typically requested during verification. (Scripted demo answer — the live backend would quote the exact clauses from the source document.)",
      refused: false,
      sources: [
        { section: "Admissions", score: 0.8412 },
        { section: "Eligibility & Documents", score: 0.7957 }
      ],
      meta: { normalized: "admission requirements", rewritten: "college B.Tech admission eligibility and process", chunks: 5, latencyMs: 412 }
    },
    {
      q: "What hostel facilities are available for students?",
      a: "The knowledge base describes on-campus hostel accommodation for students, covering resident wards, mess facilities, warden supervision and study areas in the hostel section. Room allocation and fee notes live in the same block of the document. (Scripted demo answer — sample data, not live model output.)",
      refused: false,
      sources: [
        { section: "Hostel Facilities", score: 0.8236 },
        { section: "Campus Amenities", score: 0.7618 }
      ],
      meta: { normalized: "hostel facilities available", rewritten: "hostel accommodation facilities for students on campus", chunks: 5, latencyMs: 388 }
    },
    {
      q: "How are placements structured for graduating students?",
      a: "A dedicated training and placement cell coordinates the process: pre-placement training, recruiter drives announced through the cell, and per-company eligibility published in advance. Placement statistics and recruiter information are recorded under the placements section of the knowledge base. (Scripted demo answer — sample data, not live model output.)",
      refused: false,
      sources: [
        { section: "Placements", score: 0.8731 },
        { section: "Training & Placement Cell", score: 0.8064 }
      ],
      meta: { normalized: "placements structure graduating students", rewritten: "training and placement process for graduating students", chunks: 5, latencyMs: 431 }
    },
    {
      q: "Who is the Prime Minister of India?",
      a: "I can only answer questions that can be grounded in the college knowledge base. That question falls outside the document, so I would rather decline than guess. Try asking about admissions, hostels, branches, faculty or placements instead.",
      refused: true,
      sources: [],
      meta: { normalized: "prime minister of india", rewritten: "prime minister of india", gate: "refused — best score 0.1148 < RELEVANCE_SCORE_THRESHOLD 0.20" }
    }
  ];

  var state = {
    messages: [],
    typing: false,
    playing: false,
    demoMode: false,
    token: 0,
    timers: []
  };

  /* ---------- helpers ---------- */

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) { node.className = className; }
    if (text !== undefined && text !== null) { node.textContent = text; }
    return node;
  }

  function store(key, value) {
    try {
      window.localStorage.setItem(key, value);
    } catch (err) { /* storage unavailable */ }
  }

  function recall(key) {
    try {
      return window.localStorage.getItem(key);
    } catch (err) {
      return null;
    }
  }

  function later(fn, ms) {
    var id = window.setTimeout(fn, ms);
    state.timers.push(id);
    return id;
  }

  function clearTimers() {
    state.timers.forEach(function (id) { window.clearTimeout(id); });
    state.timers = [];
  }

  function copyText(text, done) {
    var finish = function (ok) {
      if (typeof done === "function") { done(ok); }
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { finish(true); }, function () {
        finish(fallbackCopy(text));
      });
    } else {
      finish(fallbackCopy(text));
    }
  }

  function fallbackCopy(text) {
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "readonly");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (err) { ok = false; }
    document.body.removeChild(area);
    return ok;
  }

  function download(filename, text, mime) {
    var blob = new Blob([text], { type: mime });
    var url = URL.createObjectURL(blob);
    var link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1500);
  }

  function showError(text) {
    if (!els.error) { return; }
    els.error.textContent = text;
    els.error.hidden = false;
  }

  function hideError() {
    if (!els.error) { return; }
    els.error.hidden = true;
    els.error.textContent = "";
  }

  function setNote(text) {
    if (els.note) { els.note.textContent = text; }
  }

  function scrollToThread() {
    var surface = $("#chat-surface");
    if (surface) { surface.scrollTop = surface.scrollHeight; }
  }

  /* ---------- rendering ---------- */

  function updateControls() {
    var total = state.messages.length;
    if (els.count) {
      els.count.textContent = total + (total === 1 ? " message" : " messages");
    }
    if (els.exportJson) { els.exportJson.disabled = total === 0; }
    if (els.exportMd) { els.exportMd.disabled = total === 0; }
    if (els.clearThread) { els.clearThread.disabled = total === 0 && !state.typing; }
    if (els.stop) { els.stop.disabled = !state.playing; }
    if (els.banner) { els.banner.hidden = !hasDemoMessages(); }
  }

  function hasDemoMessages() {
    return state.messages.some(function (m) { return m.demo; });
  }

  function buildCommandRow(cmd) {
    var row = el("div", "cmd-row");
    row.appendChild(el("code", null, cmd));
    var btn = el("button", "copy-btn btn-mini", "Copy");
    btn.type = "button";
    btn.setAttribute("data-cmd", cmd);
    row.appendChild(btn);
    return row;
  }

  function buildOfflineCard(msg) {
    var card = el("div", "offline-card");

    var badge = el("span", "badge badge-offline", "Backend offline");
    card.appendChild(badge);

    card.appendChild(el("h4", null, "Live answers require the RAG backend"));

    var intro = el("p");
    intro.textContent = "This page is a static interface. The project ships a Streamlit chat app and no REST API, so there is nothing here to fetch — a real answer needs the backend running:";
    card.appendChild(intro);

    var list = el("ol", "run-steps");
    var steps = [
      "python -m venv .venv   (then activate it)",
      "pip install -r requirements.txt",
      "Copy .env.example to .env and set OPENROUTER_API_KEY=sk-or-v1-…",
      "python scripts/ingest.py   — one-time ingestion into chroma_db/",
      "streamlit run app/app.py   (or: python run.py) → http://localhost:8501"
    ];
    steps.forEach(function (cmd) {
      var li = document.createElement("li");
      li.appendChild(buildCommandRow(cmd));
      list.appendChild(li);
    });
    card.appendChild(list);

    card.appendChild(el("p", "offline-foot", "Other real keys in .env.example: LLM_MODEL (openai/gpt-4o-mini), EMBEDDING_MODEL, RETRIEVAL_TOP_K, RELEVANCE_SCORE_THRESHOLD, FETCH_K, LAMBDA_MULT, ADAPTIVE_K_THRESHOLD."));

    var actions = el("div", "offline-actions");
    var play = el("button", "btn btn-brass", "Play demo conversation");
    play.type = "button";
    play.setAttribute("data-action", "play-demo");
    actions.appendChild(play);
    card.appendChild(actions);

    return card;
  }

  function buildScorePanel(msg) {
    var panel = el("div", "score-panel");
    var meta = msg.meta || {};

    if (msg.refused && meta.gate) {
      panel.appendChild(el("h5", null, "Retrieval gate (demo)"));
      panel.appendChild(el("p", "score-meta", meta.gate));
      return panel;
    }

    if (msg.sources && msg.sources.length) {
      panel.appendChild(el("h5", null, "Retrieval scores (demo)"));
      msg.sources.forEach(function (src) {
        var row = el("div", "score-row");
        row.appendChild(el("span", "score-name", src.section));
        row.appendChild(el("span", "score-val", src.score.toFixed(4)));
        var track = el("div", "score-track");
        var fill = document.createElement("i");
        fill.style.width = Math.max(4, Math.min(100, src.score * 100)) + "%";
        track.appendChild(fill);
        row.appendChild(track);
        panel.appendChild(row);
      });
      var bits = [];
      if (meta.chunks) { bits.push(meta.chunks + " chunks retrieved"); }
      if (meta.latencyMs) { bits.push(meta.latencyMs + " ms"); }
      if (meta.rewritten) { bits.push('query: "' + meta.rewritten + '"'); }
      if (bits.length) {
        panel.appendChild(el("p", "score-meta", bits.join("  ·  ")));
      }
    }
    return panel;
  }

  function buildAssistantBubble(msg) {
    var wrap = el("div", "msg msg-assistant");
    wrap.appendChild(el("span", "msg-label", msg.demo ? "CampusWise · demo" : "CampusWise"));

    if (msg.kind === "offline") {
      wrap.appendChild(buildOfflineCard(msg));
      return wrap;
    }

    var bubble = el("div", "bubble");
    bubble.appendChild(el("p", null, msg.text));
    wrap.appendChild(bubble);

    var foot = el("div", "msg-foot");
    if (msg.demo) { foot.appendChild(el("span", "badge badge-demo", "Demo")); }
    if (msg.refused) { foot.appendChild(el("span", "badge badge-refused", "Refused · out of scope")); }

    var copyBtn = el("button", "copy-btn", "Copy answer");
    copyBtn.type = "button";
    copyBtn.setAttribute("data-copy", String(msg.index));
    foot.appendChild(copyBtn);
    wrap.appendChild(foot);

    if (msg.sources && msg.sources.length) {
      var pills = el("div", "pills");
      msg.sources.forEach(function (src) {
        pills.appendChild(el("span", "pill", src.section));
      });
      wrap.appendChild(pills);
    }

    if (msg.demo) {
      wrap.appendChild(buildScorePanel(msg));
    }

    return wrap;
  }

  function buildUserBubble(msg) {
    var wrap = el("div", "msg msg-user");
    wrap.appendChild(el("span", "msg-label", "You"));
    var bubble = el("div", "bubble");
    bubble.appendChild(el("p", null, msg.text));
    wrap.appendChild(bubble);
    return wrap;
  }

  function buildTyping() {
    var wrap = el("div", "msg msg-assistant");
    wrap.appendChild(el("span", "msg-label", "CampusWise"));
    var bubble = el("div", "bubble typing");
    if (reduceMotion) {
      bubble.appendChild(el("span", null, "retrieving…"));
    } else {
      bubble.appendChild(document.createElement("i"));
      bubble.appendChild(document.createElement("i"));
      bubble.appendChild(document.createElement("i"));
    }
    wrap.appendChild(bubble);
    return wrap;
  }

  function render() {
    var nodes = [];
    if (state.messages.length === 0) {
      if (emptyNode) { nodes.push(emptyNode); }
    } else {
      state.messages.forEach(function (msg, i) {
        msg.index = i;
        nodes.push(msg.role === "user" ? buildUserBubble(msg) : buildAssistantBubble(msg));
      });
    }
    if (state.typing) { nodes.push(buildTyping()); }
    els.thread.replaceChildren.apply(els.thread, nodes);
    updateControls();
  }

  /* ---------- playback ---------- */

  function stopPlayback() {
    state.token += 1;
    clearTimers();
    state.playing = false;
    state.typing = false;
    render();
  }

  function startDemo() {
    stopPlayback();
    var token = state.token;
    state.messages = [];
    state.playing = true;
    setDemoMode(true, true);
    render();
    scrollToThread();

    var i = 0;
    function nextTurn() {
      if (token !== state.token) { return; }
      if (i >= DEMO_SCRIPT.length) {
        state.playing = false;
        state.typing = false;
        render();
        setNote("Demo transcript complete — sample data, not live model output.");
        return;
      }
      var turn = DEMO_SCRIPT[i];
      i += 1;
      state.messages.push({ role: "user", text: turn.q, ts: Date.now() });
      state.typing = true;
      render();
      scrollToThread();

      later(function () {
        if (token !== state.token) { return; }
        state.typing = false;
        state.messages.push({
          role: "assistant",
          text: turn.a,
          refused: turn.refused,
          sources: turn.sources,
          meta: turn.meta,
          demo: true,
          ts: Date.now()
        });
        render();
        scrollToThread();
        later(nextTurn, reduceMotion ? 120 : 520);
      }, reduceMotion ? 200 : (680 + turn.a.length * 0.6));
    }

    later(nextTurn, reduceMotion ? 150 : 420);
    setNote("Demo playing — Stop cancels playback.");
  }

  /* ---------- demo mode ---------- */

  function setDemoMode(on, silent) {
    state.demoMode = !!on;
    els.demoToggle.checked = state.demoMode;
    store(LS_DEMO, state.demoMode ? "1" : "0");
    if (els.modeHint) {
      els.modeHint.textContent = state.demoMode
        ? "Demo mode on — Send plays the scripted 4-turn transcript; typed text is not sent anywhere."
        : "Live mode: every send explains how to start the real backend, or plays the labelled demo.";
    }
    if (els.input) {
      els.input.placeholder = state.demoMode
        ? "Demo mode — Send plays the scripted transcript…"
        : "Ask about admissions, hostels, placements, branches…";
    }
    if (!silent) { setNote(""); }
  }

  function leaveDemoMode() {
    stopPlayback();
    state.messages = state.messages.filter(function (m) { return !m.demo; });
    setDemoMode(false);
    render();
    setNote("Demo mode off — scripted transcript removed.");
  }

  /* ---------- sending ---------- */

  function handleSend() {
    var text = els.input.value.trim();
    hideError();

    if (!text) {
      showError("Type a question first — the composer is empty.");
      els.input.focus();
      return;
    }
    if (text.length > MAX_CHARS) {
      showError("That question is longer than " + MAX_CHARS + " characters.");
      return;
    }

    stopPlayback();

    if (state.demoMode) {
      els.input.value = "";
      updateCharCount();
      startDemo();
      return;
    }

    state.messages.push({ role: "user", text: text, ts: Date.now() });
    state.messages.push({
      role: "assistant",
      kind: "offline",
      text: "Live answers require the RAG backend — run: streamlit run app/app.py with OPENROUTER_API_KEY set in .env.",
      ts: Date.now()
    });
    els.input.value = "";
    updateCharCount();
    render();
    scrollToThread();
    setNote("Backend offline — run the Streamlit app for live answers.");
  }

  function clearConversation() {
    stopPlayback();
    state.messages = [];
    render();
    setNote("Thread cleared.");
    hideError();
  }

  /* ---------- export ---------- */

  function exportJSON() {
    var payload = {
      ui: "CampusWise",
      project: "college-faq-chatbot-rag",
      exportedAt: new Date().toISOString(),
      note: "Transcript exported from the static UI. demo:true entries are scripted sample data, not live model output.",
      messages: state.messages.map(function (m) {
        return {
          role: m.role,
          kind: m.kind || (m.demo ? "demo-answer" : "answer"),
          text: m.text,
          demo: !!m.demo,
          refused: !!m.refused,
          sources: m.sources || []
        };
      })
    };
    download("campuswise-transcript.json", JSON.stringify(payload, null, 2), "application/json");
    setNote("Exported JSON transcript (" + state.messages.length + " messages).");
  }

  function exportMarkdown() {
    var lines = [];
    lines.push("# CampusWise transcript");
    lines.push("");
    lines.push("Exported: " + new Date().toISOString());
    lines.push("Source: static UI for college-faq-chatbot-rag · demo entries are scripted sample data.");
    lines.push("");
    state.messages.forEach(function (m) {
      if (m.role === "user") {
        lines.push("**You:** " + m.text);
      } else if (m.kind === "offline") {
        lines.push("**CampusWise (backend offline):** Live answers require the RAG backend — `streamlit run app/app.py` with `OPENROUTER_API_KEY` set in `.env`.");
      } else {
        lines.push("**CampusWise" + (m.demo ? " (demo)" : "") + ":** " + m.text);
        if (m.refused) { lines.push("_Refused — out of scope for the knowledge base._"); }
        if (m.sources && m.sources.length) {
          m.sources.forEach(function (s) {
            lines.push("- source: " + s.section + " (score " + s.score.toFixed(4) + ")");
          });
        }
      }
      lines.push("");
    });
    download("campuswise-transcript.md", lines.join("\n"), "text/markdown");
    setNote("Exported Markdown transcript (" + state.messages.length + " messages).");
  }

  /* ---------- composer ---------- */

  function updateCharCount() {
    var len = els.input.value.length;
    if (els.charCount) {
      els.charCount.textContent = len + " / " + MAX_CHARS;
      els.charCount.classList.toggle("is-warn", len > MAX_CHARS - 40);
    }
  }

  /* ---------- tabs ---------- */

  function activateTab(tab) {
    var tabs = Array.prototype.slice.call(document.querySelectorAll('[role="tab"]'));
    tabs.forEach(function (t) {
      var active = t === tab;
      t.setAttribute("aria-selected", active ? "true" : "false");
      t.classList.toggle("is-active", active);
      t.tabIndex = active ? 0 : -1;
      var panel = document.getElementById(t.getAttribute("aria-controls"));
      if (panel) { panel.hidden = !active; }
    });

    if (els.explorer && els.slotChat && els.slotFull) {
      if (tab.id === "tab-knowledge") {
        els.slotFull.appendChild(els.explorer);
      } else {
        els.slotChat.appendChild(els.explorer);
      }
    }
    store(LS_TAB, tab.id);
  }

  function initTabs() {
    var tabs = Array.prototype.slice.call(document.querySelectorAll('[role="tab"]'));
    tabs.forEach(function (tab, idx) {
      tab.addEventListener("click", function () { activateTab(tab); });
      tab.addEventListener("keydown", function (ev) {
        var next = null;
        if (ev.key === "ArrowRight") { next = tabs[(idx + 1) % tabs.length]; }
        if (ev.key === "ArrowLeft") { next = tabs[(idx - 1 + tabs.length) % tabs.length]; }
        if (ev.key === "Home") { next = tabs[0]; }
        if (ev.key === "End") { next = tabs[tabs.length - 1]; }
        if (next) {
          ev.preventDefault();
          next.focus();
          activateTab(next);
        }
      });
    });
    var saved = recall(LS_TAB);
    if (saved) {
      var target = document.getElementById(saved);
      if (target && target.getAttribute("role") === "tab") { activateTab(target); }
    }
  }

  /* ---------- wiring ---------- */

  els.form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    handleSend();
  });

  els.input.addEventListener("input", function () {
    updateCharCount();
    if (!els.error.hidden) { hideError(); }
  });

  els.input.addEventListener("keydown", function (ev) {
    if (ev.key === "Enter" && !ev.shiftKey) {
      ev.preventDefault();
      handleSend();
    }
  });

  if (els.clearInput) {
    els.clearInput.addEventListener("click", function () {
      els.input.value = "";
      updateCharCount();
      hideError();
      els.input.focus();
      setNote("Composer cleared.");
    });
  }

  if (els.stop) {
    els.stop.addEventListener("click", function () {
      stopPlayback();
      setNote("Playback stopped.");
    });
  }

  if (els.clearThread) {
    els.clearThread.addEventListener("click", clearConversation);
  }

  if (els.exportJson) { els.exportJson.addEventListener("click", exportJSON); }
  if (els.exportMd) { els.exportMd.addEventListener("click", exportMarkdown); }

  if (els.playDemo) {
    els.playDemo.addEventListener("click", function () {
      startDemo();
      var surface = $("#chat-surface");
      if (surface) { surface.scrollIntoView({ block: "nearest" }); }
    });
  }

  els.demoToggle.addEventListener("change", function () {
    if (els.demoToggle.checked) {
      startDemo();
    } else {
      leaveDemoMode();
    }
  });

  if (els.chips) {
    els.chips.addEventListener("click", function (ev) {
      var chip = ev.target.closest ? ev.target.closest(".chip") : null;
      if (!chip) { return; }
      var q = chip.getAttribute("data-q") || chip.textContent;
      els.input.value = q;
      updateCharCount();
      hideError();
      els.input.focus();
      setNote("Question loaded into the composer — press Send.");
    });
  }

  els.thread.addEventListener("click", function (ev) {
    var target = ev.target;
    if (!target || !target.getAttribute) { return; }

    var action = target.getAttribute("data-action");
    if (action === "play-demo") {
      startDemo();
      return;
    }

    var cmd = target.getAttribute("data-cmd");
    if (cmd) {
      copyText(cmd, function (ok) {
        target.textContent = ok ? "Copied" : "Copy failed";
        window.setTimeout(function () { target.textContent = "Copy"; }, 1400);
      });
      return;
    }

    var idx = target.getAttribute("data-copy");
    if (idx !== null && idx !== undefined && idx !== "") {
      var msg = state.messages[Number(idx)];
      if (msg && msg.text) {
        copyText(msg.text, function (ok) {
          target.textContent = ok ? "Copied" : "Copy failed";
          window.setTimeout(function () { target.textContent = "Copy answer"; }, 1400);
        });
      }
    }
  });

  /* ---------- init ---------- */

  var savedDemo = recall(LS_DEMO);
  setDemoMode(savedDemo === "1", true);
  if (savedDemo === "1") {
    setNote("Demo mode remembered — press Send or Play demo conversation to load the transcript.");
  }
  initTabs();
  updateCharCount();
  render();
})();

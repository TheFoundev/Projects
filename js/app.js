/* PlateSight — ANPR operator console */
(function () {
  "use strict";

  var SAMPLES = [
    { file: "uploads/Cars18.png", name: "Cars18.png" },
    { file: "uploads/Cars23.png", name: "Cars23.png" },
    { file: "uploads/Cars65.png", name: "Cars65.png" },
    { file: "uploads/Cars72.png", name: "Cars72.png" },
    { file: "uploads/Cars78.png", name: "Cars78.png" },
    { file: "uploads/Cars9.png", name: "Cars9.png" },
    { file: "uploads/test.jpg", name: "test.jpg" }
  ];

  var ACCEPTED = ["image/png", "image/jpeg", "image/bmp", "image/jpg"];
  var ACCEPTED_EXT = ["png", "jpg", "jpeg", "bmp"];

  var state = {
    tab: "analyze",
    file: null,
    objectUrl: null,
    lbIndex: -1
  };

  function $(id) { return document.getElementById(id); }

  /* ---------- toast ---------- */
  var toastTimer = null;
  function toast(msg) {
    var el = $("toast");
    if (!el) return;
    el.textContent = msg;
    el.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { el.hidden = true; }, 2400);
  }

  function copyText(text, okMsg) {
    function fallback() {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy"); toast(okMsg || "Copied"); }
      catch (e) { toast("Copy failed"); }
      document.body.removeChild(ta);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { toast(okMsg || "Copied"); }, fallback);
    } else { fallback(); }
  }

  function formatBytes(n) {
    if (n < 1024) return n + " B";
    if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
    return (n / (1024 * 1024)).toFixed(2) + " MB";
  }

  /* ---------- tabs ---------- */
  var TABS = ["analyze", "samples", "about"];

  function showTab(name) {
    if (TABS.indexOf(name) === -1) return;
    state.tab = name;
    TABS.forEach(function (t) {
      var btn = $("tab-" + t);
      var panel = $("panel-" + t);
      if (!btn || !panel) return;
      var on = t === name;
      btn.setAttribute("aria-selected", on ? "true" : "false");
      btn.tabIndex = on ? 0 : -1;
      panel.hidden = !on;
    });
    try { localStorage.setItem("platesight-tab", name); } catch (e) { /* storage unavailable */ }
  }

  function initTabs() {
    TABS.forEach(function (t) {
      var btn = $("tab-" + t);
      if (btn) btn.addEventListener("click", function () { showTab(t); });
    });
    var saved = null;
    try { saved = localStorage.getItem("platesight-tab"); } catch (e) { /* ignore */ }
    if (saved) showTab(saved);
  }

  /* ---------- file intake ---------- */
  function showError(msg) {
    var el = $("intake-error");
    if (!el) return;
    el.textContent = msg;
    el.hidden = !msg;
  }

  function extensionOf(name) {
    var i = name.lastIndexOf(".");
    return i === -1 ? "" : name.slice(i + 1).toLowerCase();
  }

  function acceptFile(file) {
    if (!file) return;
    var ext = extensionOf(file.name);
    var typeOk = ACCEPTED.indexOf(file.type) !== -1 || (file.type === "" && ACCEPTED_EXT.indexOf(ext) !== -1) || (file.type === "image/jpg" && ACCEPTED_EXT.indexOf(ext) !== -1);
    var extOk = ACCEPTED_EXT.indexOf(ext) !== -1;
    if (!typeOk && !extOk) {
      showError("Unsupported file type: " + (file.type || ext || "unknown") + ". The Streamlit uploader accepts PNG, JPG, BMP and JPEG only.");
      return;
    }
    if (file.size === 0) {
      showError("That file is empty (0 bytes).");
      return;
    }
    showError("");
    if (state.objectUrl) URL.revokeObjectURL(state.objectUrl);
    state.file = file;
    state.objectUrl = URL.createObjectURL(file);

    var img = $("preview-img");
    var empty = $("preview-empty");
    var meta = $("file-meta");
    if (img) { img.src = state.objectUrl; img.hidden = false; }
    if (empty) empty.hidden = true;
    if (meta) meta.hidden = false;

    var nameEl = $("meta-name"); if (nameEl) nameEl.textContent = file.name;
    var sizeEl = $("meta-size"); if (sizeEl) sizeEl.textContent = formatBytes(file.size) + " (" + file.size.toLocaleString() + " bytes)";
    var typeEl = $("meta-type"); if (typeEl) typeEl.textContent = file.type || ("." + ext);

    var runPanel = $("run-panel");
    if (runPanel) runPanel.hidden = true;
    var skeleton = $("result-skeleton");
    if (skeleton) skeleton.hidden = false;

    toast("Staged: " + file.name);
  }

  function clearFile() {
    if (state.objectUrl) URL.revokeObjectURL(state.objectUrl);
    state.file = null;
    state.objectUrl = null;
    var img = $("preview-img");
    if (img) { img.removeAttribute("src"); img.hidden = true; }
    var empty = $("preview-empty");
    if (empty) empty.hidden = false;
    var meta = $("file-meta");
    if (meta) meta.hidden = true;
    var input = $("file-input");
    if (input) input.value = "";
    var runPanel = $("run-panel");
    if (runPanel) runPanel.hidden = true;
    var skeleton = $("result-skeleton");
    if (skeleton) skeleton.hidden = false;
    showError("");
    toast("Cleared");
  }

  function downloadPreview() {
    if (!state.file || !state.objectUrl) { toast("No image staged"); return; }
    var a = document.createElement("a");
    a.href = state.objectUrl;
    a.download = state.file.name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    toast("Downloaded " + state.file.name + " (original file, unchanged)");
  }

  function initIntake() {
    var dz = $("dropzone");
    var input = $("file-input");
    if (!dz || !input) return;

    dz.addEventListener("click", function () { input.click(); });
    dz.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.click(); }
    });

    ["dragenter", "dragover"].forEach(function (ev) {
      dz.addEventListener(ev, function (e) {
        e.preventDefault();
        e.stopPropagation();
        dz.classList.add("dragover");
      });
    });
    ["dragleave", "drop"].forEach(function (ev) {
      dz.addEventListener(ev, function (e) {
        e.preventDefault();
        e.stopPropagation();
        dz.classList.remove("dragover");
      });
    });
    dz.addEventListener("drop", function (e) {
      var files = e.dataTransfer && e.dataTransfer.files;
      if (files && files.length) acceptFile(files[0]);
    });

    input.addEventListener("change", function () {
      if (input.files && input.files.length) acceptFile(input.files[0]);
    });

    var detect = $("btn-detect");
    if (detect) detect.addEventListener("click", function () {
      if (!state.file) { showError("Stage an image first — drop a file or click the drop zone."); return; }
      showError("");
      var runPanel = $("run-panel");
      var skeleton = $("result-skeleton");
      if (runPanel) runPanel.hidden = false;
      if (skeleton) skeleton.hidden = true;
      if (runPanel) runPanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
      toast("No REST API — run instructions shown below");
    });

    var dl = $("btn-download-preview");
    if (dl) dl.addEventListener("click", downloadPreview);

    var clear = $("btn-clear");
    if (clear) clear.addEventListener("click", clearFile);

    document.querySelectorAll(".copy-btn[data-copy]").forEach(function (b) {
      b.addEventListener("click", function () { copyText(b.getAttribute("data-copy"), "Command copied"); });
    });
  }

  /* ---------- samples ---------- */
  function renderSamples() {
    var grid = $("sample-grid");
    if (!grid) return;
    SAMPLES.forEach(function (s, i) {
      var card = document.createElement("button");
      card.type = "button";
      card.className = "sample-card";
      card.setAttribute("aria-label", "Open sample " + s.name);
      var img = document.createElement("img");
      img.src = s.file;
      img.alt = "Sample vehicle image " + s.name;
      img.loading = "lazy";
      var meta = document.createElement("div");
      meta.className = "sample-card__meta";
      meta.innerHTML = '<span class="sample-card__name"></span><span class="sample-card__tag">uploads/</span><span class="sample-tag">SAMPLE INPUT</span>';
      meta.querySelector(".sample-card__name").textContent = s.name;
      card.appendChild(img);
      card.appendChild(meta);
      card.addEventListener("click", function () { openLightbox(i); });
      grid.appendChild(card);
    });
    var fallbackCheck = SAMPLES[0];
    var probe = new Image();
    probe.onerror = function () {
      var note = document.createElement("p");
      note.className = "inline-error";
      note.textContent = "Sample images could not be loaded from uploads/ — serve this folder over HTTP (python -m http.server 8000) if opened via file://.";
      grid.parentNode.insertBefore(note, grid);
    };
    probe.src = fallbackCheck.file;
  }

  /* ---------- lightbox ---------- */
  function openLightbox(i) {
    var lb = $("lightbox");
    if (!lb) return;
    state.lbIndex = i;
    updateLightbox();
    lb.hidden = false;
    var close = $("lb-close");
    if (close) close.focus();
  }

  function updateLightbox() {
    var s = SAMPLES[state.lbIndex];
    if (!s) return;
    var img = $("lb-img");
    var cap = $("lb-caption");
    if (img) {
      img.src = s.file;
      img.alt = "Sample vehicle image " + s.name;
    }
    if (cap) cap.textContent = s.name + " — sample input, run the app to get detections";
  }

  function closeLightbox() {
    var lb = $("lightbox");
    if (lb) lb.hidden = true;
    state.lbIndex = -1;
  }

  function stepLightbox(delta) {
    state.lbIndex = (state.lbIndex + delta + SAMPLES.length) % SAMPLES.length;
    updateLightbox();
  }

  function initLightbox() {
    var close = $("lb-close");
    var prev = $("lb-prev");
    var next = $("lb-next");
    var lb = $("lightbox");
    if (close) close.addEventListener("click", closeLightbox);
    if (prev) prev.addEventListener("click", function () { stepLightbox(-1); });
    if (next) next.addEventListener("click", function () { stepLightbox(1); });
    if (lb) lb.addEventListener("click", function (e) { if (e.target === lb) closeLightbox(); });
    document.addEventListener("keydown", function (e) {
      if (!lb || lb.hidden) return;
      if (e.key === "Escape") closeLightbox();
      else if (e.key === "ArrowLeft") stepLightbox(-1);
      else if (e.key === "ArrowRight") stepLightbox(1);
    });
  }

  /* ---------- init ---------- */
  function init() {
    initTabs();
    initIntake();
    renderSamples();
    initLightbox();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

(function () {
  "use strict";

  var $ = function (id) {
    return document.getElementById(id);
  };

  var form = $("scan-form");
  var tabText = $("tab-text");
  var tabFile = $("tab-file");
  var panelText = $("panel-text");
  var panelFile = $("panel-file");
  var textarea = $("text-input");
  var charCount = $("char-count");
  var sentCount = $("sent-count");
  var fileInput = $("file-input");
  var dropzone = $("dropzone");
  var dzMeta = $("dz-meta");
  var fileName = $("file-name");
  var fileClear = $("file-clear");
  var formError = $("form-error");
  var scanBtn = $("scan-btn");
  var progress = $("progress");
  var clearBtn = $("clear-btn");
  var toast = $("toast");

  if (!form) {
    return;
  }

  var MAX_BYTES = 16 * 1000 * 1000;
  var activeMode = "text";
  var stash = { text: "" };
  var toastTimer = null;
  var errorEl = formError;

  function prefersReduced() {
    return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function showToast(message) {
    if (!toast) {
      return;
    }
    toast.textContent = message;
    toast.hidden = false;
    if (toastTimer) {
      window.clearTimeout(toastTimer);
    }
    toastTimer = window.setTimeout(function () {
      toast.hidden = true;
    }, 2200);
  }

  function showError(message, field) {
    if (errorEl) {
      errorEl.textContent = message;
      errorEl.hidden = false;
    }
    if (field && typeof field.focus === "function") {
      field.focus();
    }
  }

  function clearError() {
    if (errorEl) {
      errorEl.hidden = true;
      errorEl.textContent = "";
    }
  }

  function updateCounters() {
    if (!textarea) {
      return;
    }
    var raw = textarea.value;
    var chars = raw.length;
    var sentences = raw.replace(/\n/g, " ").split(". ").filter(function (part) {
      return part.trim() !== "";
    }).length;
    if (charCount) {
      charCount.textContent = chars + (chars === 1 ? " character" : " characters");
    }
    if (sentCount) {
      sentCount.textContent = sentences + (sentences === 1 ? " sentence" : " sentences");
    }
  }

  function resetFileUI() {
    if (fileInput) {
      fileInput.value = "";
    }
    if (dzMeta) {
      dzMeta.hidden = true;
    }
    if (fileName) {
      fileName.textContent = "";
    }
  }

  function setTab(mode) {
    if (mode !== "text" && mode !== "file") {
      return;
    }
    if (mode === activeMode) {
      return;
    }
    if (mode === "file") {
      if (textarea) {
        stash.text = textarea.value;
        textarea.value = "";
      }
      updateCounters();
      if (panelText) {
        panelText.classList.add("is-hidden");
      }
      if (panelFile) {
        panelFile.classList.remove("is-hidden");
      }
    } else {
      if (fileInput) {
        fileInput.value = "";
      }
      if (dzMeta) {
        dzMeta.hidden = true;
      }
      if (textarea) {
        textarea.value = stash.text;
      }
      updateCounters();
      if (panelFile) {
        panelFile.classList.add("is-hidden");
      }
      if (panelText) {
        panelText.classList.remove("is-hidden");
      }
    }
    activeMode = mode;
    if (tabText && tabFile) {
      var textActive = mode === "text";
      tabText.classList.toggle("is-active", textActive);
      tabFile.classList.toggle("is-active", !textActive);
      tabText.setAttribute("aria-selected", textActive ? "true" : "false");
      tabFile.setAttribute("aria-selected", textActive ? "false" : "true");
    }
    clearError();
    try {
      window.localStorage.setItem("radarInputMode", mode);
    } catch (err) {
      void err;
    }
  }

  if (tabText) {
    tabText.addEventListener("click", function () {
      setTab("text");
    });
  }
  if (tabFile) {
    tabFile.addEventListener("click", function () {
      setTab("file");
    });
  }

  [tabText, tabFile].forEach(function (btn) {
    if (!btn) {
      return;
    }
    btn.addEventListener("keydown", function (event) {
      if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
        event.preventDefault();
        var next = activeMode === "text" ? tabFile : tabText;
        if (next) {
          next.focus();
          next.click();
        }
      }
    });
  });

  try {
    var savedMode = window.localStorage.getItem("radarInputMode");
    if (savedMode === "file") {
      setTab("file");
    }
  } catch (err) {
    void err;
  }

  if (textarea) {
    textarea.addEventListener("input", function () {
      updateCounters();
      clearError();
    });
  }
  updateCounters();

  function describeSize(bytes) {
    if (bytes >= 1000 * 1000) {
      return (bytes / (1000 * 1000)).toFixed(1) + " MB";
    }
    return Math.max(1, Math.round(bytes / 1000)) + " KB";
  }

  function acceptFile(file) {
    if (!file) {
      return false;
    }
    var name = file.name || "";
    if (name.toLowerCase().indexOf(".pdf") !== name.length - 4 || name.length < 5) {
      showError("“" + name + "” is not a PDF. Only PDF files can be uploaded.", fileInput);
      resetFileUI();
      return false;
    }
    if (file.size > MAX_BYTES) {
      showError("“" + name + "” is " + describeSize(file.size) + " — the server limit is 16 MB (16,000,000 bytes).", fileInput);
      resetFileUI();
      return false;
    }
    clearError();
    if (fileName) {
      fileName.textContent = name + " · " + describeSize(file.size);
    }
    if (dzMeta) {
      dzMeta.hidden = false;
    }
    return true;
  }

  if (fileInput) {
    fileInput.addEventListener("change", function () {
      var files = fileInput.files;
      if (!files || files.length === 0) {
        resetFileUI();
        return;
      }
      acceptFile(files[0]);
    });
  }

  if (fileClear) {
    fileClear.addEventListener("click", function () {
      resetFileUI();
      clearError();
      if (fileInput) {
        fileInput.focus();
      }
    });
  }

  if (dropzone) {
    ["dragenter", "dragover"].forEach(function (type) {
      dropzone.addEventListener(type, function (event) {
        event.preventDefault();
        event.stopPropagation();
        dropzone.classList.add("is-over");
      });
    });
    ["dragleave", "dragend"].forEach(function (type) {
      dropzone.addEventListener(type, function (event) {
        event.preventDefault();
        event.stopPropagation();
        dropzone.classList.remove("is-over");
      });
    });
    dropzone.addEventListener("drop", function (event) {
      event.preventDefault();
      event.stopPropagation();
      dropzone.classList.remove("is-over");
      var dropped = event.dataTransfer && event.dataTransfer.files;
      if (!dropped || dropped.length === 0) {
        return;
      }
      if (activeMode !== "file") {
        setTab("file");
      }
      try {
        fileInput.files = dropped;
      } catch (err) {
        showError("This browser will not accept a dropped file directly — click the zone and browse to it.", fileInput);
        return;
      }
      acceptFile(dropped[0]);
    });
  }

  function prepareScan() {
    clearError();
    if (activeMode === "file") {
      if (textarea) {
        textarea.value = "";
      }
      var files = fileInput ? fileInput.files : null;
      if (!files || files.length === 0) {
        showError("Choose a PDF first — drop it in the zone or click to browse.", fileInput);
        return false;
      }
      if (!acceptFile(files[0])) {
        return false;
      }
      return true;
    }
    if (fileInput && fileInput.files && fileInput.files.length > 0) {
      fileInput.value = "";
      if (dzMeta) {
        dzMeta.hidden = true;
      }
    }
    if (!textarea || textarea.value.trim() === "") {
      showError("Paste some text first — or switch to the Upload PDF tab.", textarea);
      return false;
    }
    return true;
  }

  function showProgress() {
    if (progress) {
      progress.hidden = false;
    }
  }

  function hideProgress() {
    if (progress) {
      progress.hidden = true;
    }
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    if (!prepareScan()) {
      return;
    }
    showProgress();
    form.submit();
  });

  window.addEventListener("pageshow", hideProgress);

  document.addEventListener("keydown", function (event) {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      if (typeof form.requestSubmit === "function") {
        event.preventDefault();
        form.requestSubmit();
      }
    }
  });

  if (clearBtn) {
    clearBtn.addEventListener("click", function () {
      form.reset();
      stash.text = "";
      resetFileUI();
      clearError();
      if (activeMode !== "text") {
        activeMode = "text";
        if (tabText && tabFile) {
          tabText.classList.add("is-active");
          tabFile.classList.remove("is-active");
          tabText.setAttribute("aria-selected", "true");
          tabFile.setAttribute("aria-selected", "false");
        }
        if (panelText) {
          panelText.classList.remove("is-hidden");
        }
        if (panelFile) {
          panelFile.classList.add("is-hidden");
        }
      }
      updateCounters();
      if (textarea) {
        textarea.focus();
      }
      showToast("Desk cleared");
    });
  }

  var gaugeValue = $("gauge-value");
  var gaugeArc = $("gauge-arc");
  var gaugeNeedle = $("gauge-needle");
  var statusWord = $("status-word");

  function statusFor(pct) {
    if (pct <= 0) {
      return "Original";
    }
    if (pct < 30) {
      return "Minor overlap";
    }
    return "High overlap";
  }

  function animateNumber(node, target, duration) {
    var start = null;
    function frame(ts) {
      if (start === null) {
        start = ts;
      }
      var t = Math.min(1, (ts - start) / duration);
      var eased = 1 - Math.pow(1 - t, 3);
      node.textContent = (target * eased).toFixed(1);
      if (t < 1) {
        window.requestAnimationFrame(frame);
      } else {
        node.textContent = target.toFixed(1);
      }
    }
    window.requestAnimationFrame(frame);
  }

  function initGauge() {
    if (!gaugeValue) {
      return;
    }
    var pct = parseFloat(gaugeValue.getAttribute("data-persen"));
    if (!isFinite(pct)) {
      return;
    }
    if (statusWord) {
      statusWord.textContent = statusFor(pct);
    }
    if (!gaugeArc || !gaugeNeedle || prefersReduced()) {
      return;
    }
    gaugeArc.style.transition = "none";
    gaugeNeedle.style.transition = "none";
    gaugeArc.style.strokeDashoffset = "100";
    gaugeNeedle.style.transform = "rotate(0deg)";
    gaugeValue.textContent = "0.0";
    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(function () {
        gaugeArc.style.transition = "";
        gaugeNeedle.style.transition = "";
        gaugeArc.style.strokeDashoffset = String(100 - pct);
        gaugeNeedle.style.transform = "rotate(" + pct * 3.6 + "deg)";
        animateNumber(gaugeValue, pct, 1500);
      });
    });
  }

  initGauge();

  var matchesToggle = $("matches-toggle");
  var matchesList = $("matches");

  if (matchesToggle && matchesList) {
    matchesToggle.addEventListener("click", function () {
      var collapsed = matchesList.classList.toggle("is-collapsed");
      matchesToggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
      matchesToggle.textContent = collapsed ? "Expand list" : "Collapse list";
    });
  }

  Array.prototype.forEach.call(document.querySelectorAll(".match-sentence"), function (sentence) {
    if (sentence.scrollHeight > sentence.clientHeight + 4) {
      var button = document.createElement("button");
      button.type = "button";
      button.className = "sentence-more";
      button.textContent = "Show full sentence";
      button.setAttribute("aria-expanded", "false");
      button.addEventListener("click", function () {
        var open = sentence.classList.toggle("is-open");
        button.textContent = open ? "Clamp sentence" : "Show full sentence";
        button.setAttribute("aria-expanded", open ? "true" : "false");
      });
      sentence.parentNode.insertBefore(button, sentence.nextSibling);
    }
  });

  function legacyCopy(text) {
    var helper = document.createElement("textarea");
    helper.value = text;
    helper.setAttribute("readonly", "");
    helper.style.position = "fixed";
    helper.style.opacity = "0";
    document.body.appendChild(helper);
    helper.select();
    var ok = false;
    try {
      ok = document.execCommand("copy");
    } catch (err) {
      ok = false;
    }
    document.body.removeChild(helper);
    return ok;
  }

  function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      if (legacyCopy(text)) {
        resolve();
      } else {
        reject(new Error("copy failed"));
      }
    });
  }

  Array.prototype.forEach.call(document.querySelectorAll(".copy-btn"), function (button) {
    button.addEventListener("click", function () {
      var card = button.closest ? button.closest(".match") : null;
      if (!card) {
        return;
      }
      var kind = button.getAttribute("data-copy");
      var target = kind === "link" ? card.querySelector(".source-link") : card.querySelector(".match-sentence");
      if (!target) {
        return;
      }
      var text = kind === "link" ? target.getAttribute("href") : target.textContent;
      copyToClipboard(String(text)).then(function () {
        var original = button.textContent;
        button.textContent = "Copied";
        button.classList.add("is-done");
        showToast(kind === "link" ? "Link copied" : "Sentence copied");
        window.setTimeout(function () {
          button.textContent = original;
          button.classList.remove("is-done");
        }, 1600);
      }).catch(function () {
        showToast("Copy failed — select the text manually");
      });
    });
  });
})();

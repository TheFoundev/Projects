/* ============================================================
   Note Sense — voice-first currency identifier
   Vanilla JS. No backend: recognition itself lives in detect.py.
   ============================================================ */

(function () {
  "use strict";

  var BASE = "Currency%20Detection%20using%20OpenCV%20in%20ML/";
  var FILES_DIR = BASE + "files/";
  var AUDIO_DIR = BASE + "audio/";

  var TRAINING = {
    "20.jpg": true, "50.jpg": true, "100.jpg": true,
    "200.jpg": true, "500.jpg": true, "test_20_6.jpg": true
  };
  var HARDCODED = "test_200_1.jpg";

  var FILES = [
    "10.jpg", "100.jpg", "100_2.jpg", "100_3.jpg", "10_2.jpg", "10_3.jpg",
    "20.jpg", "200.jpg", "2000.jpg", "20_2.jpg", "20_3.jpg", "50.jpg",
    "500.jpg", "50_2.jpg",
    "test_100_1.jpg", "test_100_2.jpg", "test_100_3.jpg", "test_100_4.jpg",
    "test_100_5 (2).jpg", "test_100_5.jpg",
    "test_10_1.jpg", "test_10_2.jpg", "test_10_3.jpg",
    "test_2000_1.jpg", "test_200_1.jpg", "test_200_2.jpg", "test_200_3.jpg",
    "test_20_1.jpg", "test_20_2.jpg", "test_20_3.jpg", "test_20_4.jpg",
    "test_20_5.jpg", "test_20_6.jpg", "test_20_7.jpg",
    "test_500_1.jpg", "test_500_2.jpg", "test_50_1.jpg", "test_50_2.jpg",
    "test_50_3.jpg", "test_50_4.jpg"
  ];

  var VOICE_KEY = "notesense:voice";

  function $(id) { return document.getElementById(id); }

  function prefersReducedMotion() {
    return window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function roleFor(name) {
    if (TRAINING[name]) return "Training reference (in detect.py)";
    if (name === HARDCODED) return "Hardcoded test image (read by detect.py)";
    if (name.indexOf("test_") === 0) return "Test photo";
    return "Reference photo";
  }

  /* ---------------- voice / Web Speech API ---------------- */

  var speechSupported = typeof window.speechSynthesis !== "undefined" &&
    typeof window.SpeechSynthesisUtterance !== "undefined";

  var voiceOn = true;
  try {
    var stored = window.localStorage.getItem(VOICE_KEY);
    if (stored === "off") voiceOn = false;
  } catch (e) { /* storage unavailable — stay with default */ }

  var voiceToggle = $("voice-toggle");
  var stopSpeech = $("stop-speech");
  var readResult = $("read-result");

  function syncVoiceUI() {
    if (!voiceToggle) return;
    if (!speechSupported) {
      voiceToggle.disabled = true;
      voiceToggle.setAttribute("aria-pressed", "false");
      voiceToggle.textContent = "Voice guidance: unavailable";
      voiceToggle.title = "Your browser does not expose the Web Speech API";
      if (stopSpeech) {
        stopSpeech.disabled = true;
        stopSpeech.title = "Your browser does not expose the Web Speech API";
      }
    } else {
      voiceToggle.setAttribute("aria-pressed", voiceOn ? "true" : "false");
      voiceToggle.textContent = "Voice guidance: " + (voiceOn ? "ON" : "OFF");
    }
    [readResult, $("lb-read")].forEach(function (btn) {
      if (!btn) return;
      btn.disabled = !voiceOn || !speechSupported;
      btn.title = voiceOn
        ? (speechSupported ? "Reads the visible text with your system voice"
          : "Your browser does not support the Web Speech API")
        : "Voice guidance is off — switch it on in the page header";
    });
  }

  function speak(text, statusEl) {
    if (!speechSupported || !voiceOn) return;
    try {
      window.speechSynthesis.cancel();
      var utter = new window.SpeechSynthesisUtterance(text);
      utter.rate = 0.95;
      utter.pitch = 1;
      if (statusEl) statusEl.dataset.speaking = "true";
      utter.onend = function () {
        if (statusEl) delete statusEl.dataset.speaking;
      };
      window.speechSynthesis.speak(utter);
    } catch (err) {
      if (statusEl) delete statusEl.dataset.speaking;
    }
  }

  function stopSpeaking() {
    if (!speechSupported) return;
    try { window.speechSynthesis.cancel(); } catch (err) { /* ignore */ }
  }

  if (voiceToggle) {
    voiceToggle.addEventListener("click", function () {
      voiceOn = !voiceOn;
      if (!voiceOn) stopSpeaking();
      try {
        window.localStorage.setItem(VOICE_KEY, voiceOn ? "on" : "off");
      } catch (e) { /* ignore */ }
      syncVoiceUI();
    });
  }
  if (stopSpeech) stopSpeech.addEventListener("click", stopSpeaking);

  var bannerActions = document.querySelector(".banner-actions");
  if (bannerActions) {
    var speechNote = document.createElement("p");
    speechNote.className = "fine";
    speechNote.style.flexBasis = "100%";
    speechNote.textContent = speechSupported
      ? "\u201CRead this aloud\u201D speaks exactly the text shown on screen \u2014 never a guessed denomination."
      : "Your browser does not expose the Web Speech API, so read-aloud buttons are disabled.";
    bannerActions.appendChild(speechNote);
  }

  /* ---------------- step 1: file selection & preview ---------------- */

  var fileInput = $("note-photo");
  var dropZone = $("drop-zone");
  var fileError = $("file-error");
  var previewWrap = $("preview-wrap");
  var previewImg = $("preview-img");
  var previewName = $("preview-name");
  var clearPhoto = $("clear-photo");
  var identifyBtn = $("identify-btn");
  var identifyHint = $("identify-hint");

  var objectUrl = null;
  var chosenName = "";
  var chosenFile = null;

  function showError(el, message) {
    if (!el) return;
    el.textContent = message;
    el.hidden = false;
  }

  function clearError(el) {
    if (!el) return;
    el.textContent = "";
    el.hidden = true;
  }

  function revokeUrl() {
    if (objectUrl) {
      try { URL.revokeObjectURL(objectUrl); } catch (e) { /* ignore */ }
      objectUrl = null;
    }
  }

  function resetPhoto() {
    revokeUrl();
    chosenName = "";
    chosenFile = null;
    if (previewWrap) previewWrap.hidden = true;
    if (previewImg) previewImg.removeAttribute("src");
    if (previewName) previewName.textContent = "\u2014";
    if (fileInput) fileInput.value = "";
    if (identifyBtn) identifyBtn.disabled = true;
    if (identifyHint) {
      identifyHint.textContent =
        "Choose a photo first \u2014 the button turns on when a preview is showing.";
    }
    clearError(fileError);
  }

  function acceptFile(file) {
    if (!file) return;
    if (!file.type || file.type.indexOf("image/") !== 0) {
      showError(fileError,
        "That file is not an image. Please choose a JPG or PNG photo of a note.");
      return;
    }
    if (typeof URL === "undefined" || !URL.createObjectURL) {
      showError(fileError,
        "This browser cannot preview local files. Try a current browser.");
      return;
    }
    clearError(fileError);
    revokeUrl();
    objectUrl = URL.createObjectURL(file);
    chosenName = file.name;
    chosenFile = file;

    if (previewImg && previewWrap) {
      previewImg.onload = function () {
        previewWrap.hidden = false;
        if (identifyBtn) identifyBtn.disabled = false;
        if (identifyHint) {
          identifyHint.textContent =
            "Photo ready: " + chosenName + ". Now go to Step 2.";
        }
      };
      previewImg.onerror = function () {
        showError(fileError,
          "The preview could not be opened. The file may be damaged \u2014 try another photo.");
        resetPhoto();
      };
      if (identifyHint) {
        identifyHint.textContent = "Loading a preview of " + chosenName + "\u2026";
      }
      previewImg.src = objectUrl;
      previewImg.alt = "Preview of the chosen currency note photo: " + chosenName;
      if (previewName) previewName.textContent = chosenName;
    }
  }

  if (fileInput) {
    fileInput.addEventListener("change", function () {
      acceptFile(fileInput.files && fileInput.files[0]);
    });
  }

  if (dropZone) {
    ["dragenter", "dragover"].forEach(function (type) {
      dropZone.addEventListener(type, function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        dropZone.classList.add("is-over");
      });
    });
    ["dragleave", "dragend"].forEach(function (type) {
      dropZone.addEventListener(type, function () {
        dropZone.classList.remove("is-over");
      });
    });
    dropZone.addEventListener("drop", function (ev) {
      ev.preventDefault();
      ev.stopPropagation();
      dropZone.classList.remove("is-over");
      if (ev.dataTransfer && ev.dataTransfer.files && ev.dataTransfer.files.length) {
        acceptFile(ev.dataTransfer.files[0]);
      }
    });
  }

  if (clearPhoto) clearPhoto.addEventListener("click", resetPhoto);

  /* ---------------- step 3: honest result state ---------------- */

  var banner = $("result-banner");
  var bannerKicker = $("banner-kicker");
  var bannerTitle = $("banner-title");
  var bannerBody = $("banner-body");

  var BACKEND_KICKER = "Requires backend";
  var BACKEND_TITLE = "Recognition needs the local OpenCV backend";
  var BACKEND_BODY =
    "This page is a desktop OpenCV project, so no recognition runs in the browser and no " +
    "denomination is shown here. detect.py reads the hardcoded image files/test_200_1.jpg, " +
    "matches ORB features against six reference notes with a brute-force matcher and Lowe’s " +
    "ratio 0.789, then prints “Detected denomination” for the winning file. Edit the test " +
    "image path, run the script, and this banner is where the printed result will be read aloud.";

  var BACKEND_ORIGIN = (window.location.protocol === "file:")
    ? "http://127.0.0.1:8000"
    : (window.location.protocol + "//" + window.location.hostname + ":8000");
  var DETECT_URL = "/api/detect";
  var HEALTH_URL = "/api/health";

  function setBanner(state, kicker, title, body) {
    if (banner) banner.setAttribute("data-state", state);
    if (bannerKicker) bannerKicker.textContent = kicker;
    if (bannerTitle) bannerTitle.textContent = title;
    if (bannerBody) bannerBody.textContent = body;
  }

  function rupeesToWords(amount) {
    var words = {
      "10": "ten rupees",
      "20": "twenty rupees",
      "50": "fifty rupees",
      "100": "one hundred rupees",
      "200": "two hundred rupees",
      "500": "five hundred rupees",
      "2000": "two thousand rupees"
    };
    return words[amount] || amount + " rupees";
  }


  function scrollIntoViewSafely(el) {
    if (!el || !el.scrollIntoView) return;
    try {
      el.scrollIntoView({
        behavior: prefersReducedMotion() ? "auto" : "smooth",
        block: "center"
      });
    } catch (e) {
      el.scrollIntoView();
    }
  }

  function postTo(url, file) {
    var form = new FormData();
    form.append("photo", file, file.name);
    return fetch(url, { method: "POST", body: form, cache: "no-store" })
      .then(function (response) {
        return response.json().then(function (data) {
          if (!response.ok) {
            var failure = new Error((data && data.message) || "HTTP " + response.status);
            failure.data = data;
            throw failure;
          }
          return data;
        });
      });
  }

  function detectWithBackend(file) {
    // The page may be served by this backend, by a plain static server, or
    // opened straight from disk - so fall back to the known backend address.
    return postTo(DETECT_URL, file).catch(function (error) {
      if (DETECT_URL !== BACKEND_ORIGIN + "/api/detect") {
        return postTo(BACKEND_ORIGIN + "/api/detect", file);
      }
      throw error;
    });
  }

  if (identifyBtn) {
    identifyBtn.addEventListener("click", function () {
      if (!chosenFile) {
        showError(fileError, "Choose a photo in Step 1 first.");
        return;
      }

      identifyBtn.disabled = true;
      if (identifyHint) {
        identifyHint.textContent = "Matching your photo against the reference notes\u2026";
      }
      setBanner("working", "Working", "Matching keypoints",
        "Your photo is being compared with the reference notes using ORB keypoints, " +
        "brute-force matching and Lowe\u2019s ratio test.");

      detectWithBackend(chosenFile).then(function (data) {
        if (data && data.ok) {
          var runnerUp = data.runner_up ? (" Next best: Rs. " + data.runner_up +
            " (" + data.runner_up_matches + " matches).") : "";
          setBanner("detected", "Detected", data.label,
            "Matched " + data.good_matches + " good keypoints against files/" +
            data.reference + " (" + data.method + ")." + runnerUp +
            " The winner is convincing when it is clearly ahead of the next best note.");
          if (identifyHint) {
            identifyHint.textContent = "Recognised as " + data.label + ".";
          }
          scrollIntoViewSafely(banner);
          speak("Detected. " + rupeesToWords(data.denomination) + ".", banner);
          var sample = new Audio(AUDIO_DIR + data.denomination + ".mp3");
          sample.play().catch(function () { /* no clip for this denomination */ });
        } else {
          setBanner("no-match", "Not recognised",
            (data && data.denomination ? data.label + " \u2014 low confidence" : "No match"),
            (data && data.message) ||
              "The photo did not match any reference note closely enough.");
          if (identifyHint) {
            identifyHint.textContent = "No confident match \u2014 try a sharper, well lit photo.";
          }
          scrollIntoViewSafely(banner);
          speak("Sorry, that note was not recognised. Please try another photo.", banner);
        }
      }).catch(function (error) {
        checkBackend().then(function (online) {
          if (online) {
            setBanner("backend-required", "Backend online",
              "This page is an old cached copy",
              "The detection backend is running and answered the request, but this page is " +
              "showing the old cached version of the interface. Reload it with " +
              "Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac) to get the version that " +
              "uploads the photo to the detector.");
            if (identifyHint) {
              identifyHint.textContent =
                "Reload the page (Ctrl+Shift+R) to load the version that recognises your photo.";
            }
          } else {
            setBanner("backend-required", BACKEND_KICKER, BACKEND_TITLE, BACKEND_BODY);
            if (identifyHint) {
              identifyHint.textContent =
                "The local backend is not running. Start it with \u201Cpython server.py\u201D, or use the command in \u201CHow to run the recogniser\u201D.";
            }
          }
        }).catch(function () {
          setBanner("backend-required", BACKEND_KICKER, BACKEND_TITLE, BACKEND_BODY);
        });
        stopSpeaking();
      }).then(function () {
        identifyBtn.disabled = false;
      });
    });
  }

  if (readResult) {
    readResult.addEventListener("click", function () {
      var text = [
        bannerKicker ? bannerKicker.textContent : "",
        bannerTitle ? bannerTitle.textContent : "",
        bannerBody ? bannerBody.textContent : ""
      ].join(". ").replace(/\s+/g, " ").trim();
      speak(text, banner);
    });
  }

  /* ---------------- copy command ---------------- */

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      try {
        var ta = document.createElement("textarea");
        ta.value = text;
        ta.setAttribute("readonly", "");
        ta.style.position = "fixed";
        ta.style.left = "-9999px";
        document.body.appendChild(ta);
        ta.select();
        var ok = document.execCommand("copy");
        document.body.removeChild(ta);
        ok ? resolve() : reject(new Error("copy failed"));
      } catch (err) {
        reject(err);
      }
    });
  }

  var copyCmd = $("copy-cmd");
  var runCmd = $("run-cmd");
  if (copyCmd && runCmd) {
    copyCmd.addEventListener("click", function () {
      var original = "Copy command";
      copyText(runCmd.textContent.trim()).then(function () {
        copyCmd.textContent = "Copied \u2713";
      }).catch(function () {
        copyCmd.textContent = "Select the text and copy it";
      }).then(function () {
        window.setTimeout(function () { copyCmd.textContent = original; }, 2400);
      });
    });
  }

  /* ---------------- voice samples (real mp3 files) ---------------- */

  var audio = $("sample-audio");
  var nowPlaying = $("now-playing");
  var audioError = $("audio-error");
  var playButtons = [
    $("play-20"), $("play-50"), $("play-100")
  ].filter(Boolean);
  var stopAudio = $("stop-audio");

  function setNowPlaying(html, idle) {
    if (!nowPlaying) return;
    nowPlaying.innerHTML = html;
    nowPlaying.classList.toggle("is-idle", !!idle);
  }

  function clearAudioError() { clearError(audioError); }

  function setPlayingState(denom) {
    setNowPlaying(
      '<span class="bars" aria-hidden="true"><i></i><i></i><i></i><i></i></span>' +
      "Now playing: \u20B9" + denom + " sample",
      false
    );
  }

  function stopSample(silent) {
    if (audio) {
      try { audio.pause(); audio.currentTime = 0; } catch (e) { /* ignore */ }
    }
    playButtons.forEach(function (b) { b.setAttribute("aria-pressed", "false"); });
    if (!silent) setNowPlaying("Nothing playing.", true);
  }

  playButtons.forEach(function (btn) {
    btn.setAttribute("aria-pressed", "false");
    btn.addEventListener("click", function () {
      if (!audio) return;
      var denom = btn.getAttribute("data-denom") || "";
      clearAudioError();
      stopSample(true);
      btn.setAttribute("aria-pressed", "true");
      setPlayingState(denom);
      audio.src = AUDIO_DIR + denom + ".mp3";
      var played = audio.play();
      if (played && typeof played.catch === "function") {
        played.catch(function () {
          /* play() rejection: the error event below reports details */
        });
      }
    });
  });

  if (stopAudio) stopAudio.addEventListener("click", function () { stopSample(false); });

  if (audio) {
    audio.addEventListener("ended", function () { stopSample(false); });
    audio.addEventListener("error", function () {
      stopSample(true);
      var expected = decodeURI(AUDIO_DIR + "20.mp3");
      showError(audioError,
        "Could not open the sample. Expected file: " + expected +
        " \u2014 open this page from inside the project folder so the relative path resolves.");
      setNowPlaying("Nothing playing.", true);
    });
  }

  /* ---------------- reference gallery ---------------- */

  var gallery = $("gallery-grid");
  var galleryEmpty = $("gallery-empty");
  var lastIndex = 0;

  function buildGallery() {
    if (!gallery) return;
    if (galleryEmpty && galleryEmpty.parentNode) {
      galleryEmpty.parentNode.removeChild(galleryEmpty);
    }
    var frag = document.createDocumentFragment();
    FILES.forEach(function (name, index) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "gallery-item";
      if (TRAINING[name]) btn.classList.add("is-training");
      if (name === HARDCODED) btn.classList.add("is-hardcoded");
      btn.setAttribute("data-index", String(index));
      btn.setAttribute("aria-label",
        "Open " + name + " full screen \u2014 " + roleFor(name));

      var img = document.createElement("img");
      img.src = FILES_DIR + encodeURI(name);
      img.alt = "Currency note image " + name;
      img.loading = "lazy";

      var cap = document.createElement("span");
      cap.className = "cap";
      cap.textContent = name;

      var role = document.createElement("span");
      role.className = "role";
      role.textContent = roleFor(name);

      btn.appendChild(img);
      btn.appendChild(cap);
      btn.appendChild(role);
      btn.addEventListener("click", function () {
        openLightbox(index, btn);
      });
      frag.appendChild(btn);
    });
    gallery.appendChild(frag);
  }

  /* ---------------- lightbox ---------------- */

  var lightbox = $("lightbox");
  var lbImg = $("lb-img");
  var lbCaption = $("lb-caption");
  var lbRole = $("lb-role");
  var lbPrev = $("lb-prev");
  var lbNext = $("lb-next");
  var lbClose = $("lb-close");
  var lbRead = $("lb-read");
  var lastFocused = null;

  function renderLightbox(index) {
    lastIndex = (index + FILES.length) % FILES.length;
    var name = FILES[lastIndex];
    if (lbImg) {
      lbImg.src = FILES_DIR + encodeURI(name);
      lbImg.alt = "Full screen view of " + name;
    }
    if (lbCaption) lbCaption.textContent = name;
    if (lbRole) lbRole.textContent = roleFor(name);
  }

  function openLightbox(index, trigger) {
    if (!lightbox) return;
    lastFocused = trigger || document.activeElement;
    renderLightbox(index);
    lightbox.hidden = false;
    document.body.style.overflow = "hidden";
    if (lbClose) lbClose.focus();
  }

  function closeLightbox() {
    if (!lightbox || lightbox.hidden) return;
    lightbox.hidden = true;
    document.body.style.overflow = "";
    stopSpeaking();
    if (lastFocused && lastFocused.focus) lastFocused.focus();
  }

  if (lbPrev) lbPrev.addEventListener("click", function () { renderLightbox(lastIndex - 1); });
  if (lbNext) lbNext.addEventListener("click", function () { renderLightbox(lastIndex + 1); });
  if (lbClose) lbClose.addEventListener("click", closeLightbox);

  if (lbRead) {
    lbRead.addEventListener("click", function () {
      if (!lbCaption) return;
      speak(lbCaption.textContent + ". " + (lbRole ? lbRole.textContent : ""),
        lightbox);
    });
  }

  if (lightbox) {
    lightbox.addEventListener("click", function (ev) {
      if (ev.target === lightbox) closeLightbox();
    });
  }

  document.addEventListener("keydown", function (ev) {
    if (!lightbox || lightbox.hidden) return;
    if (ev.key === "Escape") {
      ev.preventDefault();
      closeLightbox();
    } else if (ev.key === "ArrowLeft") {
      ev.preventDefault();
      renderLightbox(lastIndex - 1);
    } else if (ev.key === "ArrowRight") {
      ev.preventDefault();
      renderLightbox(lastIndex + 1);
    } else if (ev.key === "Tab") {
      var focusable = lightbox.querySelectorAll("button:not([disabled])");
      if (!focusable.length) return;
      var first = focusable[0];
      var last = focusable[focusable.length - 1];
      if (ev.shiftKey && document.activeElement === first) {
        ev.preventDefault();
        last.focus();
      } else if (!ev.shiftKey && document.activeElement === last) {
        ev.preventDefault();
        first.focus();
      }
    }
  });

  /* ---------------- backend status ---------------- */

  function checkBackend() {
    return fetch(HEALTH_URL, { cache: "no-store" })
      .then(function (response) { return response.ok; })
      .catch(function () {
        if (HEALTH_URL !== BACKEND_ORIGIN + "/api/health") {
          return fetch(BACKEND_ORIGIN + "/api/health", { cache: "no-store" })
            .then(function (response) { return response.ok; })
            .catch(function () { return false; });
        }
        return false;
      });
  }

  function showBackendChip(online) {
    var chips = document.querySelectorAll(".chip");
    for (var i = 0; i < chips.length; i++) {
      if (chips[i].getAttribute("data-backend-chip") === "1") {
        chips[i].textContent = online
          ? "Backend online — recognition is available"
          : "Backend offline — start it with \u201Cpython server.py\u201D";
        chips[i].classList.toggle("chip-alert", !online);
      }
    }
  }

  /* ---------------- init ---------------- */

  syncVoiceUI();
  buildGallery();
  setNowPlaying("Nothing playing.", true);
  checkBackend().then(showBackendChip);
})();

(function () {
  "use strict";

  var $ = function (id) {
    return document.getElementById(id);
  };

  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var navToggle = $("nav-toggle");
  var navMenu = $("nav-menu");

  if (navToggle && navMenu) {
    navToggle.addEventListener("click", function () {
      var open = navMenu.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
      navToggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    });

    navMenu.addEventListener("click", function (event) {
      if (event.target && event.target.closest && event.target.closest("a")) {
        navMenu.classList.remove("is-open");
        navToggle.setAttribute("aria-expanded", "false");
        navToggle.setAttribute("aria-label", "Open menu");
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && navMenu.classList.contains("is-open")) {
        navMenu.classList.remove("is-open");
        navToggle.setAttribute("aria-expanded", "false");
        navToggle.setAttribute("aria-label", "Open menu");
        navToggle.focus();
      }
    });
  }

  var dropZone = $("leaf-drop");
  var fileInput = $("leaf-input");
  var fileError = $("file-error");
  var preview = $("preview");
  var previewImg = $("preview-img");
  var fileMeta = $("file-meta");
  var rotateLeft = $("rotate-left");
  var rotateRight = $("rotate-right");
  var zoomIn = $("zoom-in");
  var zoomOut = $("zoom-out");
  var zoomReset = $("zoom-reset");
  var removeFile = $("remove-file");
  var analyzeBtn = $("analyze-btn");
  var analyzeStatus = $("analyze-status");
  var backendPanel = $("backend-panel");
  var mockFrame = $("mock-frame");

  if (!dropZone || !fileInput || !analyzeBtn) {
    return;
  }

  var MAX_BYTES = 10 * 1000 * 1000;
  var OK_EXT = ["jpg", "jpeg", "png", "webp", "gif", "bmp"];
  var objectUrl = null;
  var rotation = 0;
  var zoom = 1;
  var statusTimer = null;

  function setStatus(message) {
    if (analyzeStatus) {
      analyzeStatus.textContent = message;
    }
  }

  function showError(message) {
    if (fileError) {
      fileError.textContent = message;
      fileError.hidden = false;
    }
    setStatus("Fix the highlighted problem, then the bench can continue.");
  }

  function clearError() {
    if (fileError) {
      fileError.hidden = true;
      fileError.textContent = "";
    }
  }

  function describeSize(bytes) {
    if (bytes >= 1000 * 1000) {
      return (bytes / (1000 * 1000)).toFixed(1) + " MB";
    }
    return Math.max(1, Math.round(bytes / 1000)) + " KB";
  }

  function extensionOf(name) {
    var parts = String(name).toLowerCase().split(".");
    return parts.length > 1 ? parts.pop() : "";
  }

  function applyTransform() {
    if (previewImg) {
      previewImg.style.transform = "rotate(" + rotation + "deg) scale(" + zoom + ")";
    }
    if (zoomOut) {
      zoomOut.disabled = zoom <= 0.5;
    }
    if (zoomIn) {
      zoomIn.disabled = zoom >= 3;
    }
  }

  function resetView() {
    rotation = 0;
    zoom = 1;
    applyTransform();
  }

  function clearFile() {
    if (objectUrl) {
      try {
        URL.revokeObjectURL(objectUrl);
      } catch (err) {
        void err;
      }
      objectUrl = null;
    }
    fileInput.value = "";
    if (preview) {
      preview.hidden = true;
    }
    if (previewImg) {
      previewImg.removeAttribute("src");
      previewImg.style.transform = "";
    }
    if (fileMeta) {
      fileMeta.textContent = "";
    }
    resetView();
    clearError();
    analyzeBtn.disabled = true;
    if (statusTimer) {
      window.clearTimeout(statusTimer);
    }
    if (backendPanel) {
      backendPanel.hidden = true;
    }
    if (mockFrame) {
      mockFrame.classList.remove("is-flagged");
    }
    setStatus("Load an image to enable the bench. The button checks your file locally, then explains what the real diagnosis needs.");
  }

  function showPreview(file) {
    if (!previewImg) {
      return;
    }
    var loaded = function () {
      if (preview) {
        preview.hidden = false;
      }
      resetView();
    };
    if (window.URL && window.URL.createObjectURL) {
      if (objectUrl) {
        try {
          URL.revokeObjectURL(objectUrl);
        } catch (err) {
          void err;
        }
      }
      objectUrl = URL.createObjectURL(file);
      previewImg.onload = loaded;
      previewImg.onerror = function () {
        clearFile();
        showError("That file could not be decoded as an image. Try another photo.");
      };
      previewImg.src = objectUrl;
    } else {
      var reader = new FileReader();
      reader.onload = function () {
        previewImg.src = String(reader.result);
        loaded();
      };
      reader.onerror = function () {
        clearFile();
        showError("That file could not be read. Try another photo.");
      };
      reader.readAsDataURL(file);
    }
  }

  function acceptFile(file) {
    if (!file) {
      return false;
    }
    var ext = extensionOf(file.name);
    var typeOk = typeof file.type === "string" && file.type.indexOf("image/") === 0;
    if (!typeOk && OK_EXT.indexOf(ext) === -1) {
      clearFile();
      showError("“" + file.name + "” is not an image the bench can read. Use JPG, PNG, WEBP, GIF or BMP.");
      return false;
    }
    if (file.size > MAX_BYTES) {
      clearFile();
      showError("“" + file.name + "” is " + describeSize(file.size) + " — the bench limit is 10 MB. This is a browser-side check only.");
      return false;
    }
    clearError();
    showPreview(file);
    if (fileMeta) {
      fileMeta.textContent = file.name + " · " + describeSize(file.size);
    }
    analyzeBtn.disabled = false;
    if (backendPanel) {
      backendPanel.hidden = true;
    }
    if (mockFrame) {
      mockFrame.classList.remove("is-flagged");
    }
    if (statusTimer) {
      window.clearTimeout(statusTimer);
    }
    setStatus("Image loaded: " + file.name + ". Press Analyze leaf — it runs local file checks only, then explains what a real diagnosis needs.");
    return true;
  }

  fileInput.addEventListener("change", function () {
    var files = fileInput.files;
    if (!files || files.length === 0) {
      return;
    }
    acceptFile(files[0]);
  });

  ["dragenter", "dragover"].forEach(function (type) {
    dropZone.addEventListener(type, function (event) {
      event.preventDefault();
      event.stopPropagation();
      dropZone.classList.add("is-over");
    });
  });

  ["dragleave", "dragend"].forEach(function (type) {
    dropZone.addEventListener(type, function (event) {
      event.preventDefault();
      event.stopPropagation();
      dropZone.classList.remove("is-over");
    });
  });

  dropZone.addEventListener("drop", function (event) {
    event.preventDefault();
    event.stopPropagation();
    dropZone.classList.remove("is-over");
    var dropped = event.dataTransfer && event.dataTransfer.files;
    if (!dropped || dropped.length === 0) {
      return;
    }
    try {
      fileInput.files = dropped;
    } catch (err) {
      void err;
    }
    acceptFile(dropped[0]);
  });

  if (rotateLeft) {
    rotateLeft.addEventListener("click", function () {
      rotation -= 90;
      applyTransform();
    });
  }

  if (rotateRight) {
    rotateRight.addEventListener("click", function () {
      rotation += 90;
      applyTransform();
    });
  }

  if (zoomIn) {
    zoomIn.addEventListener("click", function () {
      zoom = Math.min(3, Math.round((zoom + 0.25) * 100) / 100);
      applyTransform();
    });
  }

  if (zoomOut) {
    zoomOut.addEventListener("click", function () {
      zoom = Math.max(0.5, Math.round((zoom - 0.25) * 100) / 100);
      applyTransform();
    });
  }

  if (zoomReset) {
    zoomReset.addEventListener("click", function () {
      resetView();
    });
  }

  if (removeFile) {
    removeFile.addEventListener("click", function () {
      clearFile();
      fileInput.focus();
    });
  }

  function escapeHtml(text) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(String(text)));
    return div.innerHTML;
  }

  function fillRow(dd, value) {
    var span = dd.querySelector(".skel");
    if (span) {
      span.textContent = value;
      span.className = "";
    } else {
      dd.textContent = value;
    }
  }

  function renderResult(data) {
    if (backendPanel) {
      backendPanel.hidden = true;
    }
    var rows = mockFrame ? mockFrame.querySelectorAll(".mock-row dd") : [];
    if (rows.length >= 1) {
      fillRow(rows[0], data.disease);
    }
    if (rows.length >= 2) {
      fillRow(rows[1], data.healthy ? "Healthy" : "Diseased");
    }
    if (rows.length >= 3) {
      fillRow(rows[2], (data.confidence * 100).toFixed(1) + "%");
      var bar = mockFrame ? mockFrame.querySelector(".mock-bar span") : null;
      if (bar) {
        bar.style.width = (data.confidence * 100) + "%";
      }
    }
    if (mockFrame) {
      mockFrame.classList.remove("is-flagged");
      mockFrame.classList.add("is-result");
    }
    setStatus("Diagnosis complete: " + data.disease + " — " + (data.confidence * 100).toFixed(1) + "% confidence.");
  }

  function showBackendPanel(message) {
    if (backendPanel) {
      backendPanel.hidden = false;
      backendPanel.setAttribute("tabindex", "-1");
      try {
        backendPanel.focus({ preventScroll: true });
      } catch (err) {
        void err;
      }
      backendPanel.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "center" });
    }
    if (mockFrame) {
      mockFrame.classList.remove("is-flagged");
      void mockFrame.offsetWidth;
      mockFrame.classList.add("is-flagged");
    }
    setStatus(message);
  }

  analyzeBtn.addEventListener("click", function () {
    var files = fileInput.files;
    if (!files || files.length === 0) {
      showError("Load a leaf photo first — drop it in the zone or click to browse.");
      return;
    }
    if (!acceptFile(files[0])) {
      return;
    }
    clearError();
    analyzeBtn.disabled = true;
    setStatus("Local check passed. Sending your leaf to the CNN backend…");
    if (statusTimer) {
      window.clearTimeout(statusTimer);
    }
    if (backendPanel) {
      backendPanel.hidden = true;
    }

    var formData = new FormData();
    formData.append("leaf_image", files[0]);

    fetch("/predict", { method: "POST", body: formData })
      .then(function (response) {
        if (!response.ok) {
          return response.json().then(function (err) {
            return { ok: false, message: err.error || "Backend unavailable" };
          });
        }
        return response.json().then(function (data) {
          return { ok: true, data: data };
        });
      })
      .then(function (wrapper) {
        analyzeBtn.disabled = false;
        if (!wrapper.ok) {
          showBackendPanel("Local check passed. Diagnosis needs the CNN backend — POST /predict is wired, but the trained weights are not available on this server right now. The facts are in the amber panel.");
          return;
        }
        renderResult(wrapper.data);
      })
      .catch(function () {
        analyzeBtn.disabled = false;
        showBackendPanel("Local check passed. Diagnosis needs the CNN backend — POST /predict is wired, but the trained weights are not available on this server right now. The facts are in the amber panel.");
      });
  });

  applyTransform();
})();

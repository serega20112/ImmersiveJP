/* ============================================
   ImmersiveJP — Client-side JS
   ============================================ */
(function () {
  "use strict";

  /* --- Flash Messages --- */
  function initFlashMessages() {
    var container = document.getElementById("flash-container");
    if (!container) return;
    container.querySelectorAll(".flash").forEach(function (el) {
      setTimeout(function () { dismissFlash(el); }, 5000);
      var btn = el.querySelector(".flash-close");
      if (btn) btn.addEventListener("click", function () { dismissFlash(el); });
    });
  }

  function dismissFlash(el) {
    el.classList.add("removing");
    setTimeout(function () { el.remove(); }, 300);
  }

  /* --- Mobile Nav --- */
  function initMobileNav() {
    var toggle = document.querySelector(".nav-mobile-toggle");
    var links = document.querySelector(".nav-links");
    if (!toggle || !links) return;
    toggle.addEventListener("click", function () {
      links.classList.toggle("open");
      toggle.textContent = links.classList.contains("open") ? "\u2715" : "\u2630";
    });
    document.addEventListener("click", function (e) {
      if (!toggle.contains(e.target) && !links.contains(e.target)) {
        links.classList.remove("open");
        toggle.textContent = "\u2630";
      }
    });
  }

  /* --- Auto-resize Textarea --- */
  function initAutoResize() {
    document.querySelectorAll("textarea[data-auto-resize]").forEach(function (ta) {
      function resize() {
        ta.style.height = "auto";
        ta.style.height = Math.min(ta.scrollHeight, 200) + "px";
      }
      ta.addEventListener("input", resize);
      resize();
    });
  }

  /* --- Onboarding Steps --- */
  function initOnboarding() {
    var form = document.getElementById("onboarding-form");
    if (!form) return;
    var steps = form.querySelectorAll(".onboarding-step");
    var dots = document.querySelectorAll(".step-dot");
    var lines = document.querySelectorAll(".step-line");
    var prevBtn = document.getElementById("onboarding-prev");
    var nextBtn = document.getElementById("onboarding-next");
    var current = 0;

    function showStep(idx) {
      steps.forEach(function (s, i) { s.classList.toggle("active", i === idx); });
      dots.forEach(function (d, i) {
        d.classList.remove("active", "done");
        if (i < idx) d.classList.add("done");
        else if (i === idx) d.classList.add("active");
      });
      lines.forEach(function (l, i) { l.classList.toggle("done", i < idx); });
      if (prevBtn) prevBtn.style.display = idx === 0 ? "none" : "";
      if (nextBtn) nextBtn.textContent = idx === steps.length - 1 ? "\u0417\u0430\u0432\u0435\u0440\u0448\u0438\u0442\u044c" : "\u0414\u0430\u043b\u0435\u0435";
    }

    if (prevBtn) prevBtn.addEventListener("click", function () { if (current > 0) { current--; showStep(current); } });
    if (nextBtn) nextBtn.addEventListener("click", function (e) {
      e.preventDefault();
      if (current < steps.length - 1) { current++; showStep(current); }
      else form.submit();
    });
    showStep(0);
  }

  /* --- Quiz Hints Toggle --- */
  function initHints() {
    document.querySelectorAll("[data-toggle-hints]").forEach(function (btn) {
      var target = btn.closest(".quiz-question, .question-card");
      if (!target) return;
      var hints = target.querySelectorAll(".quiz-hint");
      hints.forEach(function (h) { h.style.display = "none"; });
      btn.addEventListener("click", function () {
        var hidden = hints[0] && hints[0].style.display === "none";
        hints.forEach(function (h) { h.style.display = hidden ? "" : "none"; });
        btn.textContent = hidden ? "\u0421\u043a\u0440\u044b\u0442\u044c \u043f\u043e\u0434\u0441\u043a\u0430\u0437\u043a\u0438" : "\u041f\u043e\u043a\u0430\u0437\u0430\u0442\u044c \u043f\u043e\u0434\u0441\u043a\u0430\u0437\u043a\u0438";
      });
    });
  }

  /* --- Mentor Chat --- */
  function initChat() {
    var form = document.getElementById("chat-form");
    var textarea = document.getElementById("chat-input");
    var messages = document.getElementById("chat-messages");
    if (!form || !textarea || !messages) return;

    form.addEventListener("submit", function (e) {
      if (!textarea.value.trim()) { e.preventDefault(); return; }
      var msg = document.createElement("div");
      msg.className = "chat-message user";
      msg.innerHTML = '<div class="chat-avatar">\u0422\u042b</div><div class="chat-bubble">' + escapeHtml(textarea.value.trim()) + '</div>';
      messages.appendChild(msg);
      messages.scrollTop = messages.scrollHeight;
    });

    document.querySelectorAll(".suggested-prompt").forEach(function (btn) {
      btn.addEventListener("click", function () {
        textarea.value = btn.textContent;
        textarea.dispatchEvent(new Event("input"));
        form.submit();
      });
    });

    messages.scrollTop = messages.scrollHeight;
  }

  function escapeHtml(str) {
    var div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  /* --- Voice Input --- */
  function initVoiceInput() {
    var btn = document.getElementById("voice-input-btn");
    var textarea = document.getElementById("chat-input");
    if (!btn || !textarea) return;

    btn.addEventListener("click", function () {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert("\u0413\u043e\u043b\u043e\u0441\u043e\u0432\u043e\u0439 \u0432\u0432\u043e\u0434 \u043d\u0435 \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u0438\u0432\u0430\u0435\u0442\u0441\u044f \u0432 \u044d\u0442\u043e\u043c \u0431\u0440\u0430\u0443\u0437\u0435\u0440\u0435.");
        return;
      }
      navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
        var mediaRecorder = new MediaRecorder(stream);
        var chunks = [];
        btn.textContent = "\u23F9";
        btn.classList.add("recording");
        mediaRecorder.ondataavailable = function (e) { if (e.data.size > 0) chunks.push(e.data); };
        mediaRecorder.onstop = function () {
          stream.getTracks().forEach(function (t) { t.stop(); });
          btn.textContent = "\u{1F3A4}";
          btn.classList.remove("recording");
          var blob = new Blob(chunks, { type: "audio/webm" });
          var fd = new FormData();
          fd.append("audio", blob, "voice.webm");
          textarea.placeholder = "\u041e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0430 \u0433\u043e\u043b\u043e\u0441\u0430...";
          textarea.disabled = true;
          fetch("/tutor/voice-input", { method: "POST", body: fd })
            .then(function (r) { return r.json(); })
            .then(function (d) { textarea.value = d.text || ""; textarea.placeholder = "\u041d\u0430\u043f\u0438\u0448\u0438\u0442\u0435 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435..."; textarea.disabled = false; textarea.focus(); })
            .catch(function () { textarea.placeholder = "\u041d\u0430\u043f\u0438\u0448\u0438\u0442\u0435 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435..."; textarea.disabled = false; });
        };
        mediaRecorder.start();
        setTimeout(function () { mediaRecorder.stop(); }, 15000);
      }).catch(function () {
        alert("\u0414\u043e\u0441\u0442\u0443\u043f \u043a \u043c\u0438\u043a\u0440\u043e\u0444\u043e\u043d\u0443 \u0437\u0430\u043a\u0440\u044b\u0442.");
      });
    });
  }

  /* --- Confirm Actions --- */
  function initConfirmActions() {
    document.querySelectorAll("[data-confirm]").forEach(function (el) {
      el.addEventListener("click", function (e) {
        if (!confirm(el.getAttribute("data-confirm"))) e.preventDefault();
      });
    });
  }

  /* --- Init --- */
  document.addEventListener("DOMContentLoaded", function () {
    initFlashMessages();
    initMobileNav();
    initAutoResize();
    initOnboarding();
    initHints();
    initChat();
    initVoiceInput();
    initConfirmActions();
  });
})();

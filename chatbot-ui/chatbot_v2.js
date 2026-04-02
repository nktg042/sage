const API_BASE = window.location.hostname || "127.0.0.1";
const API_URL = `http://${API_BASE}:8000/chat`;
const SESSIONS_API_URL = `http://${API_BASE}:8000/sessions`;

/* ── CONTEXTUAL CHIP SETS ───────────────────────────────── */
const CHIP_SETS = {
  default: [
    "Feeling stressed 😟",
    "Exam anxiety 📚",
    "Can't sleep 🌙",
    "Feeling lonely 💭",
    "Just want to talk 💬",
  ],

  stress: [
    "Tell me a breathing exercise",
    "How do I stop overthinking?",
    "I feel overwhelmed",
    "Give me a grounding technique",
  ],

  sleep: [
    "I keep waking up at night",
    "My mind won't stop racing",
    "How do I wind down?",
    "I'm exhausted but can't sleep",
  ],

  anxiety: [
    "What is the 5-4-3-2-1 method?",
    "I feel like something bad will happen",
    "How do I calm down fast?",
    "Is anxiety normal?",
  ],

  study: [
    "I have an exam tomorrow",
    "How do I focus better?",
    "I keep procrastinating",
    "I feel like I'm not good enough",
  ],

  sadness: [
    "I feel lonely",
    "I feel low today",
    "I want to talk about it",
    "Nothing feels good anymore",
  ],

  anger: [
    "How to control anger?",
    "I keep losing my temper",
    "I snapped at someone",
    "How do I calm down?",
  ],

  relationships: [
    "I had a fight with someone",
    "My parents don't understand me",
    "I feel ignored",
    "How to deal with toxic people?",
  ],

  motivation: [
    "I can't focus on anything",
    "Help me stop procrastinating",
    "I feel stuck in life",
    "Give me a 5-minute focus plan",
  ],

  crisis: [
    "I need help right now",
    "Show me calming steps",
    "I want to talk to someone",
    "Stay with me",
  ],

  positive: [
    "What else can I try?",
    "Any more tips?",
    "I'd like another exercise",
    "Tell me about mindfulness",
  ],
};

/* ── STATE ─────────────────────────────────────────────── */
let isLoading = false;
let moodChartInstance = null;
let currentSessionId = localStorage.getItem("mindEaseSession");
let currentOpenHistoryId = null;

if (!currentSessionId) {
  currentSessionId = crypto.randomUUID();
  localStorage.setItem("mindEaseSession", currentSessionId);
}

/* ── INIT ───────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  initScrollReveal();
  initNavbarScroll();
  initParticles();
  setChips("default");
  showWelcomeMessage();
  loadLatestMood();
  renderMoodHistory();
  renderMoodChart();
  loadSessions();
});

/* ── WELCOME MESSAGE ───────────────────────────────────── */
function showWelcomeMessage() {
  const user = localStorage.getItem("mindease_user");
  const name = user && user !== "anonymous" ? user : "friend";
  appendMessage(
    "bot",
    `Hi **${name}**! 🌿 I'm **Sage**, your mental wellness companion.<br><br>This is a safe, judgment-free space. You can talk to me about **stress, anxiety, sleep, sadness, relationships, motivation** — or anything on your mind.<br><br>How are you feeling today?`
  );
}

/* ── MARKDOWN → HTML RENDERER ─────────────────────────── */
function renderMarkdown(text) {
  if (!text) return "";

  let html = text;

  // Escape HTML entities first (but preserve existing HTML from welcome msg)
  html = html.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  // Bold: **text** or __text__
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/__(.+?)__/g, "<strong>$1</strong>");

  // Italic: *text* or _text_ (but not inside words)
  html = html.replace(/(?<!\w)\*([^*]+?)\*(?!\w)/g, "<em>$1</em>");
  html = html.replace(/(?<!\w)_([^_]+?)_(?!\w)/g, "<em>$1</em>");

  // Headings: ### text, ## text, # text (at line start)
  html = html.replace(/^### (.+)$/gm, '<h4 class="md-h4">$1</h4>');
  html = html.replace(/^## (.+)$/gm, '<h3 class="md-h3">$1</h3>');
  html = html.replace(/^# (.+)$/gm, '<h3 class="md-h3">$1</h3>');

  // Numbered lists: 1. text, 2. text, etc.
  html = html.replace(/^(\d+)\.\s+(.+)$/gm, '<li class="md-li numbered"><span class="li-num">$1.</span> $2</li>');

  // Bullet lists: - text or * text
  html = html.replace(/^[-*]\s+(.+)$/gm, '<li class="md-li">$1</li>');

  // Wrap consecutive <li> elements in <ul>
  html = html.replace(/((?:<li class="md-li[^"]*">.*?<\/li>\n?)+)/g, '<ul class="md-list">$1</ul>');

  // Inline code: `code`
  html = html.replace(/`([^`]+)`/g, '<code class="md-code">$1</code>');

  // Links: [text](url)
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener" class="md-link">$1</a>');

  // Phone links: make numbers like 9152987821 clickable
  html = html.replace(/(\d{10,})/g, '<a href="tel:$1" class="md-phone">$1</a>');

  // Line breaks: double newline → paragraph break, single newline → <br>
  html = html.replace(/\n\n/g, '</p><p class="md-p">');
  html = html.replace(/\n/g, "<br>");

  // Wrap in paragraph
  html = '<p class="md-p">' + html + "</p>";

  // Clean up empty paragraphs
  html = html.replace(/<p class="md-p"><\/p>/g, "");

  // Fix lists inside paragraphs
  html = html.replace(/<p class="md-p">(<ul)/g, "$1");
  html = html.replace(/(<\/ul>)<\/p>/g, "$1");

  // Fix headings inside paragraphs
  html = html.replace(/<p class="md-p">(<h[34])/g, "$1");
  html = html.replace(/(<\/h[34]>)<\/p>/g, "$1");

  return html;
}

/* ── SIDEBAR CHAT HISTORY ─────────────────────────────── */
async function loadSessions() {
  const list = document.getElementById("chatHistoryList");
  if (!list) return;

  try {
    const token = localStorage.getItem("mindease_token");
    const headers = {};
    if (token) headers["Authorization"] = "Bearer " + token;
    const res = await fetch(SESSIONS_API_URL, { headers });
    const data = await res.json();

    if (!Array.isArray(data) || data.length === 0) {
      list.innerHTML = `<div class="empty-history">No chat history yet.</div>`;
      return;
    }

    list.innerHTML = data
      .map(session => {
        const title = escapeHtml(session.title || "New Chat");
        const time = escapeHtml(session.created_at || "");
        const activeClass = session.session_id === currentSessionId ? "active" : "";

        return `
          <button class="history-item ${activeClass}" onclick="loadSession('${session.session_id}')">
            <div class="history-title">${title}</div>
            <div class="history-time">${time}</div>
          </button>
        `;
      })
      .join("");
  } catch (err) {
    console.error("Failed to load sessions:", err);
    list.innerHTML = `<div class="empty-history">Unable to load chat history.</div>`;
  }
}

async function loadSession(sessionId) {
  const chatBody = document.getElementById("chatBody");
  if (!chatBody) return;

  currentSessionId = sessionId;
  currentOpenHistoryId = sessionId;
  localStorage.setItem("mindEaseSession", currentSessionId);

  try {
    const token = localStorage.getItem("mindease_token");
    const headers = {};
    if (token) headers["Authorization"] = "Bearer " + token;
    const res = await fetch(`${SESSIONS_API_URL}/${sessionId}`, { headers });
    const messages = await res.json();

    chatBody.innerHTML = "";

    const breathingBox = document.getElementById("breathingBox");
    if (breathingBox) {
      chatBody.appendChild(breathingBox);
      breathingBox.classList.remove("show");
    }

    if (Array.isArray(messages) && messages.length > 0) {
      messages.forEach(item => {
        const role = item.role === "user" ? "user" : "bot";
        const content = role === "bot" ? renderMarkdown(item.message || "") : escapeHtml(item.message || "");
        appendMessage(role, content);
      });
    } else {
      showWelcomeMessage();
    }

    loadSessions();
    openChat();
  } catch (err) {
    console.error("Failed to load session messages:", err);
  }
}

function startNewChat() {
  currentSessionId = crypto.randomUUID();
  currentOpenHistoryId = currentSessionId;
  localStorage.setItem("mindEaseSession", currentSessionId);
  clearChat();
  loadSessions();
  openChat();
}

/* ── OPEN / CLOSE CHAT ─────────────────────────────────── */
function openChat() {
  const widget = document.getElementById("chatWidget");
  const overlay = document.getElementById("chatOverlay");
  const fab = document.getElementById("chatFab");

  if (widget) widget.classList.add("open");
  if (overlay) overlay.classList.add("open");

  if (fab) {
    fab.style.transform = "scale(0)";
    fab.style.opacity = "0";
    fab.style.pointerEvents = "none";
  }

  setTimeout(() => {
    const input = document.getElementById("userInput");
    if (input) input.focus();
  }, 350);
}

function closeChat() {
  const widget = document.getElementById("chatWidget");
  const overlay = document.getElementById("chatOverlay");
  const fab = document.getElementById("chatFab");

  if (widget) widget.classList.remove("open");
  if (overlay) overlay.classList.remove("open");

  if (fab) {
    fab.style.transform = "";
    fab.style.opacity = "";
    fab.style.pointerEvents = "";
  }
}

/* ── CLEAR CHAT ───────────────────────────────────────── */
function clearChat() {
  const chatBody = document.getElementById("chatBody");
  if (!chatBody) return;

  const breathingBox = document.getElementById("breathingBox");
  chatBody.innerHTML = "";

  if (breathingBox) {
    chatBody.appendChild(breathingBox);
    breathingBox.classList.remove("show");
  }

  const circle = document.getElementById("breathingCircle");
  const text = document.getElementById("breathingText");

  if (circle) circle.classList.remove("expand");
  if (text) text.innerText = "Tap the button and relax for a few seconds 🌿";

  setChips("default");
  showWelcomeMessage();
}

/* ── MESSAGE RENDERING ────────────────────────────────── */
function appendMessage(role, html) {
  const chatBody = document.getElementById("chatBody");
  if (!chatBody) return;

  const wrapper = document.createElement("div");
  wrapper.className = `message ${role === "bot" ? "bot" : "user"}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  if (
    role === "bot" &&
    /helpline|immediate danger|hurt yourself|harm yourself|suicide|reach out|trusted person|emergency|crisis/i.test(html)
  ) {
    bubble.classList.add("crisis-bubble");
  }

  bubble.innerHTML = html;
  wrapper.appendChild(bubble);
  chatBody.appendChild(wrapper);

  scrollToBottom();
}

function showTyping() {
  const chatBody = document.getElementById("chatBody");
  if (!chatBody) return;

  const typing = document.createElement("div");
  typing.className = "typing-indicator";
  typing.id = "typingIndicator";
  typing.innerHTML = `
    <div class="typing-dot-wrap">
      <span></span><span></span><span></span>
    </div>
    <span class="typing-label">Sage is thinking...</span>
  `;

  chatBody.appendChild(typing);
  scrollToBottom();
}

function hideTyping() {
  const el = document.getElementById("typingIndicator");
  if (el) el.remove();
}

/* ── CHIP CLICK ───────────────────────────────────────── */
function sendChip(btn) {
  const text = btn.textContent.trim();

  if (/breathing exercise/i.test(text)) {
    startBreathing();
    return;
  }

  const chips = document.getElementById("chatChips");
  if (chips) chips.style.display = "none";

  sendText(text);
}

/* ── MOOD DETECTION FROM CHAT ─────────────────────────── */
function detectMoodFromText(text) {
  const t = text.toLowerCase();

  if (/\b(happy|great|amazing|wonderful|excited|joyful|fantastic|glad)\b/.test(t)) return "Happy";
  if (/\b(calm|relaxed|peaceful|okay|chill|serene|content)\b/.test(t)) return "Calm";
  if (/\b(sad|low|lonely|down|depressed|unhappy|empty|heartbroken|grief)\b/.test(t)) return "Sad";
  if (/\b(anxious|anxiety|panic|nervous|worried|stress|stressed|overwhelmed|scared|fear)\b/.test(t)) return "Anxious";
  if (/\b(angry|angry|frustrated|furious|irritated|mad|rage)\b/.test(t)) return "Angry";

  return null;
}

/* ── SEND MESSAGE ─────────────────────────────────────── */
async function sendMessage() {
  const input = document.getElementById("userInput");
  if (!input) return;

  const text = input.value.trim();
  if (!text || isLoading) return;

  input.value = "";
  input.style.height = "auto";

  sendText(text);
}

async function sendText(text) {
  if (!text || isLoading) return;

  isLoading = true;
  toggleSendBtn(false);

  appendMessage("user", escapeHtml(text));

  const detectedMood = detectMoodFromText(text);
  if (detectedMood) {
    saveMood(detectedMood);
  }

  showTyping();

  try {
    const token = localStorage.getItem("mindease_token");
    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = "Bearer " + token;

    const res = await fetch(API_URL, {
      method: "POST",
      headers: headers,
      body: JSON.stringify({
        query: text,
        session_id: currentSessionId,
      }),
    });

    // Small delay for natural feel
    await delay(300);

    hideTyping();

    if (!res.ok) {
      const errText = await res.text();
      console.error("API error:", res.status, errText);
      appendMessage("bot", "I'm having trouble connecting right now. Please try again in a moment 💚");
      afterBotReply(text.toLowerCase());
      return;
    }

    const data = await res.json();

    // Sync session ID from backend
    if (data.session_id) {
      currentSessionId = data.session_id;
      localStorage.setItem("mindEaseSession", currentSessionId);
    }

    const reply = data.response || "I'm having trouble thinking right now. Please try again 💚";

    // Render markdown for bot responses
    appendMessage("bot", renderMarkdown(reply));

    const contextForChips = `${reply} ${text}`.toLowerCase();
    afterBotReply(contextForChips, data.is_crisis);

    loadSessions();

  } catch (err) {
    console.error("MindEase Error:", err);
    hideTyping();
    appendMessage(
      "bot",
      "I'm having trouble connecting right now. Please check if the server is running and try again 💚"
    );
    afterBotReply(text.toLowerCase());
  } finally {
    isLoading = false;
    toggleSendBtn(true);
  }
}

/* ── AFTER BOT REPLY ─────────────────────────────────── */
function afterBotReply(context, isCrisis = false) {
  const chipsEl = document.getElementById("chatChips");
  if (!chipsEl) return;

  chipsEl.style.display = "flex";

  if (isCrisis || /helpline|suicide|reach out|self.?harm|crisis/i.test(context)) {
    setChips("crisis");
  } else if (/thank|helped|better|glad|progress/i.test(context)) {
    setChips("positive");
  } else if (/stress|overwhelm|pressure|tension|burnout/i.test(context)) {
    setChips("stress");
  } else if (/sleep|tired|exhausted|rest|insomnia|wak/i.test(context)) {
    setChips("sleep");
  } else if (/anxi|panic|nervous|fear|worr/i.test(context)) {
    setChips("anxiety");
  } else if (/sad|lonely|low|empty|unhappy|depress|grief|loss/i.test(context)) {
    setChips("sadness");
  } else if (/angry|anger|frustrat|irritat|mad|rage/i.test(context)) {
    setChips("anger");
  } else if (/relationship|partner|family|parent|friend|fight|argument|toxic/i.test(context)) {
    setChips("relationships");
  } else if (/exam|study|school|college|focus|procrastin|homework/i.test(context)) {
    setChips("study");
  } else if (/motivat|stuck|lazy|energy|purpose|goal/i.test(context)) {
    setChips("motivation");
  } else {
    setChips("default");
  }
}

/* ── CHIP RENDERING ───────────────────────────────────── */
function setChips(key) {
  const chipsEl = document.getElementById("chatChips");
  if (!chipsEl) return;

  const chips = [...(CHIP_SETS[key] || CHIP_SETS.default), "Breathing exercise 🧘"];

  chipsEl.innerHTML = chips
    .map(c => `<button class="chip" onclick="sendChip(this)">${c}</button>`)
    .join("");
}

/* ── BREATHING EXERCISE ───────────────────────────────── */
function startBreathing() {
  const box = document.getElementById("breathingBox");
  const chatBody = document.getElementById("chatBody");
  const circle = document.getElementById("breathingCircle");
  const text = document.getElementById("breathingText");

  if (box) box.classList.add("show");
  if (circle) circle.classList.remove("expand");
  if (text) text.innerText = "Tap the button and relax for a few seconds 🌿";

  if (chatBody) {
    requestAnimationFrame(() => {
      chatBody.scrollTop = 0;
    });
  }
}

function closeBreathing() {
  const box = document.getElementById("breathingBox");
  const circle = document.getElementById("breathingCircle");
  const text = document.getElementById("breathingText");

  if (box) box.classList.remove("show");
  if (circle) circle.classList.remove("expand");
  if (text) text.innerText = "Tap the button and relax for a few seconds 🌿";
}

function runBreathingCycle() {
  const circle = document.getElementById("breathingCircle");
  const text = document.getElementById("breathingText");

  if (!circle || !text) return;

  circle.classList.remove("expand");
  text.innerText = "Get ready...";

  setTimeout(() => {
    text.innerText = "Inhale... 4 sec";
    circle.classList.add("expand");
  }, 300);

  setTimeout(() => {
    text.innerText = "Hold... 4 sec";
  }, 4300);

  setTimeout(() => {
    text.innerText = "Exhale... 6 sec";
    circle.classList.remove("expand");
  }, 8300);

  setTimeout(() => {
    text.innerText = "Great job 🌿 You can do another round or close this.";
  }, 14300);
}

/* ── MOOD TRACKER + GRAPH ───────────────────────────── */
function moodToValue(mood) {
  const map = { Happy: 5, Calm: 4, Angry: 3, Sad: 2, Anxious: 1 };
  return map[mood] || 0;
}

function getMoodEmoji(mood) {
  const map = { Happy: "😊", Calm: "😌", Sad: "😔", Anxious: "😟", Angry: "😤" };
  return map[mood] || "💚";
}

function saveMood(mood) {
  const now = new Date();
  const dateLabel = now.toLocaleDateString() + " " + now.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  let moodData = JSON.parse(localStorage.getItem("mindEaseMood")) || [];

  if (moodData.length > 0) {
    const latest = moodData[moodData.length - 1];
    if (latest.mood === mood) {
      return;
    }
  }

  moodData.push({
    mood: mood,
    value: moodToValue(mood),
    date: dateLabel,
  });

  // Keep last 50 entries
  if (moodData.length > 50) {
    moodData = moodData.slice(-50);
  }

  localStorage.setItem("mindEaseMood", JSON.stringify(moodData));

  const status = document.getElementById("mood-status");
  if (status) {
    status.innerText = `Latest mood: ${getMoodEmoji(mood)} ${mood} — ${dateLabel}`;
  }

  renderMoodHistory();
  renderMoodChart();
}

function loadLatestMood() {
  const status = document.getElementById("mood-status");
  if (!status) return;

  const moodData = JSON.parse(localStorage.getItem("mindEaseMood")) || [];

  if (moodData.length === 0) {
    status.innerText = "No mood saved yet. Start chatting to track your mood automatically.";
    return;
  }

  const latest = moodData[moodData.length - 1];
  status.innerText = `Latest mood: ${getMoodEmoji(latest.mood)} ${latest.mood} — ${latest.date}`;
}

function renderMoodHistory() {
  const list = document.getElementById("mood-history-list");
  if (!list) return;

  list.innerHTML = "";

  const moodData = JSON.parse(localStorage.getItem("mindEaseMood")) || [];

  if (moodData.length === 0) {
    list.innerHTML = "<li>No mood history available yet.</li>";
    return;
  }

  const recent = moodData.slice(-7).reverse();

  recent.forEach(item => {
    const li = document.createElement("li");
    li.innerText = `${getMoodEmoji(item.mood)} ${item.mood} — ${item.date}`;
    list.appendChild(li);
  });
}

function renderMoodChart() {
  const canvas = document.getElementById("moodChart");
  if (!canvas || typeof Chart === "undefined") return;

  const moodData = JSON.parse(localStorage.getItem("mindEaseMood")) || [];
  const labels = moodData.map(item => item.date);
  const values = moodData.map(item => item.value);

  if (moodChartInstance) {
    moodChartInstance.destroy();
  }

  moodChartInstance = new Chart(canvas, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Mood Trend",
          data: values,
          borderColor: "#4ade80",
          backgroundColor: "rgba(74, 222, 128, 0.1)",
          borderWidth: 2.5,
          tension: 0.4,
          fill: true,
          pointBackgroundColor: "#4ade80",
          pointBorderColor: "#0c1410",
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: "#f0ede8",
            font: { family: "'Plus Jakarta Sans', sans-serif" },
          },
        },
      },
      scales: {
        y: {
          min: 1,
          max: 5,
          ticks: {
            stepSize: 1,
            color: "#9aab9e",
            font: { family: "'Plus Jakarta Sans', sans-serif", size: 11 },
            callback: function (value) {
              if (value === 5) return "😊 Happy";
              if (value === 4) return "😌 Calm";
              if (value === 3) return "😤 Angry";
              if (value === 2) return "😔 Sad";
              if (value === 1) return "😟 Anxious";
              return value;
            },
          },
          grid: {
            color: "rgba(255,255,255,0.06)",
          },
        },
        x: {
          ticks: {
            color: "#9aab9e",
            maxRotation: 45,
            font: { size: 10 },
          },
          grid: {
            color: "rgba(255,255,255,0.04)",
          },
        },
      },
    },
  });
}

function clearMoodData() {
  localStorage.removeItem("mindEaseMood");

  const status = document.getElementById("mood-status");
  if (status) {
    status.innerText = "No mood saved yet. Start chatting to track your mood automatically.";
  }

  renderMoodHistory();
  renderMoodChart();
}

/* ── HELPERS ─────────────────────────────────────────── */
function scrollToBottom() {
  const chatBody = document.getElementById("chatBody");
  if (!chatBody) return;

  requestAnimationFrame(() => {
    chatBody.scrollTop = chatBody.scrollHeight;
  });
}

function toggleSendBtn(enabled) {
  const btn = document.getElementById("sendBtn");
  if (btn) btn.disabled = !enabled;
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 120) + "px";
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

/* ── ENTER KEY SEND ─────────────────────────────────── */
document.addEventListener("keydown", function (e) {
  const input = document.getElementById("userInput");

  if (document.activeElement === input && e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

/* ── NAVBAR SCROLL EFFECT ───────────────────────────── */
function initNavbarScroll() {
  const navbar = document.getElementById("navbar");
  if (!navbar) return;

  window.addEventListener(
    "scroll",
    () => {
      if (window.scrollY > 30) {
        navbar.classList.add("scrolled");
      } else {
        navbar.classList.remove("scrolled");
      }
    },
    { passive: true }
  );
}

/* ── SCROLL REVEAL ─────────────────────────────────── */
function initScrollReveal() {
  const revealEls = document.querySelectorAll(".reveal");
  if (!revealEls.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
  );

  revealEls.forEach(el => observer.observe(el));
}

/* ── PARTICLES BACKGROUND ─────────────────────────── */
function initParticles() {
  const canvas = document.getElementById("bgCanvas");
  if (!canvas) return;

  for (let i = 0; i < 18; i++) {
    const p = document.createElement("div");
    const size = Math.random() * 3 + 1;

    p.style.cssText = `
      position:absolute;
      width:${size}px;
      height:${size}px;
      border-radius:50%;
      background:rgba(74,222,128,0.3);
      left:${Math.random() * 100}%;
      top:${Math.random() * 100}%;
      animation:floatParticle ${Math.random() * 20 + 10}s infinite alternate;
      pointer-events:none;
    `;

    canvas.appendChild(p);
  }

  if (!document.getElementById("particleFloatStyle")) {
    const style = document.createElement("style");
    style.id = "particleFloatStyle";
    style.textContent = `
      @keyframes floatParticle {
        0%   { transform: translateY(0px) translateX(0px); opacity: 0.25; }
        100% { transform: translateY(-20px) translateX(10px); opacity: 0.65; }
      }

      .crisis-bubble {
        border: 1px solid rgba(255, 107, 107, 0.55) !important;
        background: rgba(255, 107, 107, 0.14) !important;
        box-shadow: 0 0 0 1px rgba(255, 107, 107, 0.08);
      }
    `;
    document.head.appendChild(style);
  }
}

/* ── AUTHENTICATION ───────────────────────────────────── */
let isLoginMode = true;

function openAuthModal() {
  document.getElementById("authOverlay").style.display = "block";
  document.getElementById("authModal").style.display = "block";
  document.getElementById("authErrorMsg").style.display = "none";
}

function closeAuthModal() {
  document.getElementById("authOverlay").style.display = "none";
  document.getElementById("authModal").style.display = "none";
}

function toggleAuthMode() {
  isLoginMode = !isLoginMode;
  document.getElementById("authTitle").innerText = isLoginMode ? "Welcome Back" : "Create Account";
  document.getElementById("authSubmitBtn").innerText = isLoginMode ? "Log In" : "Register";
  document.getElementById("authSwitchBtn").innerText = isLoginMode ? "Need an account? Register" : "Already have an account? Log In";
  document.getElementById("authErrorMsg").style.display = "none";
}

async function submitAuth() {
  const u = document.getElementById("authUsername").value.trim();
  const p = document.getElementById("authPassword").value.trim();
  const err = document.getElementById("authErrorMsg");
  
  if(u.length < 3 || p.length < 6) {
    err.innerText = "Username min 3 chars, Password min 6 chars.";
    err.style.display = "block";
    return;
  }
  
  const endpoint = `http://${API_BASE}:8000/${isLoginMode ? 'login' : 'register'}`;
  document.getElementById("authSubmitBtn").innerText = "Please wait...";
  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({username: u, password: p})
    });
    
    const data = await res.json();
    if(res.ok) {
      if(isLoginMode) {
        localStorage.setItem("mindease_token", data.access_token);
        localStorage.setItem("mindease_user", data.username);
        // Change nav text
        const navBtn = document.getElementById("authNavBtn");
        if(navBtn) {
          navBtn.innerText = `Logout (${data.username})`;
          navBtn.classList.add("logged-in");
        }
        closeAuthModal();
        loadSessions(); // Sync chat logs
      } else {
        err.innerText = "Registered! Logging you in...";
        err.style.color = "#4ade80";
        err.style.display = "block";
        // Auto trigger login
        setTimeout(() => { 
          isLoginMode = true; 
          submitAuth(); 
        }, 800);
      }
    } else {
      err.innerText = data.detail || "Credentials failed";
      err.style.color = "#f87171";
      err.style.display = "block";
    }
  } catch(e) {
    err.innerText = "Server unreachable. Try again.";
    err.style.display = "block";
  } finally {
    document.getElementById("authSubmitBtn").innerText = isLoginMode ? "Log In" : "Register";
  }
}

function logout() {
  localStorage.removeItem("mindease_token");
  localStorage.removeItem("mindease_user");
  const navBtn = document.getElementById("authNavBtn");
  if(navBtn) {
    navBtn.innerText = "Login / Register";
    navBtn.classList.remove("logged-in");
    navBtn.onclick = openAuthModal;
  }
  document.getElementById("chatHistoryList").innerHTML = `<div class="empty-history">Log in to see history.</div>`;
  clearChat();
}

// Restore auth & SW
window.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("mindease_token");
  const user = localStorage.getItem("mindease_user");
  if(token && user) {
    const navBtn = document.getElementById("authNavBtn");
    if(navBtn) {
      navBtn.innerText = "Logout (" + user + ")";
      navBtn.onclick = logout;
    }
    loadSessions(); // Load history on startup
  }
  
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('./sw.js').catch(e => console.log("SW error:", e));
  }
});

/* ── WEB SPEECH API ───────────────────────────────────── */
let recognition = null;
let isRecording = false;

if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-IN";
  
  recognition.onresult = (event) => {
    document.getElementById("userInput").value = event.results[0][0].transcript;
    sendMessage();
  };
  
  recognition.onend = () => {
    isRecording = false;
    const mb = document.getElementById("micBtn");
    if(mb) { mb.style.background="var(--surface-2)"; mb.style.boxShadow="none"; }
  };
}

function toggleVoiceInput() {
  if (!recognition) return alert("Voice input not supported here.");
  const mb = document.getElementById("micBtn");
  if (isRecording) {
    recognition.stop();
  } else {
    recognition.start();
    isRecording = true;
    mb.style.background = "#ef4444";
    mb.style.boxShadow = "0 0 12px rgba(239, 68, 68, 0.4)";
  }
}

/* ── PDF EXPORT ───────────────────────────────────────── */
function exportChatToPDF() {
  const box = document.getElementById("chatBody");
  if (!box || !window.html2pdf) return alert("Export not ready.");
  
  const el = box.cloneNode(true);
  el.style.background = "#fff"; el.style.color = "#000"; el.style.padding = "20px";
  el.style.height="auto"; el.style.overflow="visible";
  
  const b1 = el.querySelector("#breathingBox"); if(b1) b1.remove();
  const b2 = el.querySelector("#typingIndicator"); if(b2) b2.remove();
  
  el.querySelectorAll(".bubble").forEach(b => {
    b.style.color="#000"; b.style.border="1px solid #ddd"; 
    b.style.background="#fafafa"; b.style.boxShadow="none";
  });
  
  html2pdf().set({
    margin:0.5, filename:`MindEase_${Date.now()}.pdf`,
    image:{type:'jpeg',quality:0.98}, html2canvas:{scale:2},
    jsPDF:{unit:'in',format:'letter',orientation:'portrait'}
  }).from(el).save();
}
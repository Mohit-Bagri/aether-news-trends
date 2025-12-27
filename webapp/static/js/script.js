// ✅ Aether Frontend Script — Resume + Event-logging + Briefing-suppress fix
document.addEventListener("DOMContentLoaded", () => {
  const chatForm = document.getElementById("chatForm");
  const userInput = document.getElementById("userInput");
  const chatBox = document.getElementById("chatBox");
  const sendBtn = document.getElementById("sendBtn");
  const micBtn = document.getElementById("micBtn");

  // === ICONS ===
  const sendIcon = `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M2 21l21-9L2 3v7l15 2-15 2z"/></svg>`;
  const stopSquareIcon = `<svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>`;
  const micIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
stroke-linecap="round" stroke-linejoin="round"><path d="M12 1v10"></path><rect x="9" y="1" width="6" height="12" rx="3"></rect><path d="M19 10a7 7 0 0 1-14 0"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>`;


  sendBtn.innerHTML = sendIcon;
  micBtn.innerHTML = micIcon;

  // === STATE ===
  let currentAbort = null;
  let chatInProgress = false;
  let lastUserMessage = "";
  let paused = false;
  let queue = Promise.resolve();
  let pauseOverlay = null;
  let isPaused = false;
  let autoScrollLocked = false;
  let isTyping = false;
  let userScrolledUp = false;
  // 🔥 REQUIRED for Pause → Resume (Option B continuation)
let lastPartial = { prefix: "", remaining: "" };


function autoScrollToBottom() {
  if (userScrolledUp) return;
  if (autoScrollLocked) return;

  chatBox.scrollTo({
    top: chatBox.scrollHeight,
    behavior: "smooth"
  });
}




function scrollToBottom(force = false) {
  const distanceFromBottom = chatBox.scrollHeight - chatBox.scrollTop - chatBox.clientHeight;

  // Only scroll if user is close to bottom or forced
  if (force || distanceFromBottom < 150) {
    chatBox.scrollTo({
      top: chatBox.scrollHeight,
      behavior: "smooth",
    });
    autoScrollLocked = false; // reset lock if user is at bottom
  }
}

  console.log("🚀 Aether JS — resume+events patch loaded");

  function handlePause() {
  if (!currentAbort) return;

  isPaused = true;
  paused = true;

  try { currentAbort.abort(); } catch (e) {}
  currentAbort = null;

  document.querySelectorAll(".typing-bubble, .typing-indicator, .bot-msg.typing").forEach(n => n.remove());
  userInput.disabled = true;
  micBtn.disabled = true;

  sendBtn.dataset.role = "resume";
  sendBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"></polygon></svg>`;
  sendBtn.classList.remove("stop-active");
  sendBtn.classList.add("resume-active");

  if (pauseOverlay) pauseOverlay.remove();
  pauseOverlay = document.createElement("div");
  pauseOverlay.className = "pause-overlay fade-in";
  pauseOverlay.innerHTML = `
    <div class="pause-text">Response paused.</div>
    <button class="continue-btn shimmer">▶ Continue generating</button>
  `;
  chatBox.appendChild(pauseOverlay);

  pauseOverlay.querySelector(".continue-btn").addEventListener("click", handleResume);
  postEvent("user_paused", { message: lastUserMessage });
}

function handleResume() {
  console.log("▶ Resuming generation...");
  isPaused = false;
  paused = false;

  // clear any leftover controller safely
  if (currentAbort) {
    try { currentAbort.abort(); } catch (e) {}
    currentAbort = null;
  }

  if (pauseOverlay) {
    pauseOverlay.remove();
    pauseOverlay = null;
  }

  stopBotThinking();
  chatInProgress = false;
  queue = Promise.resolve();

  sendBtn.dataset.role = "pause";
  sendBtn.innerHTML = stopSquareIcon;
  sendBtn.classList.remove("resume-active");
  sendBtn.classList.add("stop-active");
  userInput.disabled = true;
  micBtn.disabled = true;

  // Small delay to let any old abort settle
  setTimeout(() => {
    console.log("⏩ Resuming fetch for:", lastUserMessage, lastPartial);
    // pass prefix & remaining in opts to handleSend
    handleSend(lastUserMessage, { resume: true, prefix: lastPartial.prefix || "", remaining: lastPartial.remaining || "" });
    postEvent("user_resumed", { message: lastUserMessage, partial: lastPartial });
    // reset partial only when request initiated
    // lastPartial = { prefix: "", remaining: "" }; <-- keep until backend returns full continuation
  }, 350);
}

  // === EVENT LOGGING ===
  function postEvent(eventType, payload = {}) {
    try {
      fetch("/chat_event", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event: eventType, ts: Date.now(), payload }),
      }).catch((e) => console.debug("event POST failed:", eventType, e?.message || e));
    } catch (e) {
      console.debug("event POST exception:", e);
    }
  }

  // === INITIAL GREETING ===
  setTimeout(() => {
    renderBotMessage("Hey, I'm Aether, your AI companion! Ask me anything.", { mode: "fade" });
  }, 400);

  // === SCROLL HANDLING ===
  const observer = new MutationObserver(() => {
  if (isTyping || userScrolledUp || autoScrollLocked) return;
setTimeout(() => autoScrollToBottom(), 120);


});

  observer.observe(chatBox, { childList: true, subtree: true });
  // === Detect manual scroll to temporarily disable auto-scroll ===
let lastScrollTop = 0;
chatBox.addEventListener("scroll", () => {
  const distanceFromBottom = chatBox.scrollHeight - chatBox.scrollTop - chatBox.clientHeight;
  const userAtBottom = distanceFromBottom < 80;
  const scrollingUp = chatBox.scrollTop < lastScrollTop;
  lastScrollTop = chatBox.scrollTop;

  if (!userAtBottom) {
    userScrolledUp = true;
    autoScrollLocked = true;
    isTyping = false;      // 🔥 prevents auto-scroll override during typing
  } else {
    userScrolledUp = false;
    autoScrollLocked = false;
  }
});
  // === SEND HANDLERS ===
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    if (!userInput.value.trim() || chatInProgress) return;
    handleSend();
  });

  sendBtn.addEventListener("click", (e) => {
    e.preventDefault();
    const role = sendBtn.dataset.role || "send";
    if (role === "pause") {
      handlePause();
    } else {
      if (!userInput.value.trim()) return;
      sendBtn.classList.add("launching");
      setTimeout(() => sendBtn.classList.remove("launching"), 700);
      handleSend();
    }
  });
micBtn.addEventListener("click", () => {
  if (micBtn.disabled) return;

  if (!("webkitSpeechRecognition" in window || "SpeechRecognition" in window)) {
    alert("Your browser doesn't support speech recognition. Try Chrome or Edge.");
    return;
  }

  const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
  recognition.lang = "en-US";
  recognition.interimResults = false;

  // 🔴 Visual feedback (red glow)
  micBtn.classList.add("listening");
  userInput.placeholder = "Listening...";

  recognition.start();

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript.trim();
    // 🧠 Append instead of overwrite
    if (userInput.value.trim().length > 0) {
      userInput.value = (userInput.value + " " + transcript).trim();
    } else {
      userInput.value = transcript;
    }
  };

  recognition.onerror = () => {
    console.warn("Speech recognition error");
  };

  recognition.onend = () => {
    micBtn.classList.remove("listening");
    userInput.placeholder = "Ask about any topic...";
  };
});




async function handleSend(customMessage = null, opts = {}) {
  const message = customMessage || userInput.value.trim();
  if (!message) return;
  // 🔥 Reset partial buffer for fresh messages
if (!opts.resume) {
  lastPartial = { prefix: "", remaining: "" };
}


  lastUserMessage = message;

  // 🧹 Reset scroll lock when new message is sent
userScrolledUp = false;
autoScrollLocked = false;

  userInput.value = "";
  chatInProgress = true;
  paused = false;

  if (pauseOverlay) {
    pauseOverlay.remove();
    pauseOverlay = null;
  }

  if (!opts.resume) renderUserMessage(message);
  const typingNode = renderBotThinking();

  enterGeneratingState();
  postEvent("send_started", { message, resume: !!opts.resume });

  try {
    queue = Promise.resolve().then(async () => {
      // delay controller init to prevent race with abort
      await new Promise(r => setTimeout(r, opts.resume ? 150 : 0));
      const controller = new AbortController();
      currentAbort = controller;

      const payload = { message, resume: !!opts.resume };

      // attach prefix/remaining when resuming (Option B)
      if (opts.resume) {
        payload.prefix = opts.prefix || "";
        payload.remaining = opts.remaining || "";
      }
      // 🔥 Missing fetch — add this back
const res = await fetch("/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload),
  signal: controller.signal,
});



      if (!res.ok) {
        console.warn("⚠️ Chat fetch failed:", res.status);
        renderBotMessage("Couldn't get a response, please retry.");
        return;
      }

      const data = await res.json();
      stopBotThinking(typingNode);
      await renderResponseData({ ...data, resume: opts.resume });
      exitGeneratingState();
      chatInProgress = false;
    });

    await queue;
  } catch (err) {
    stopBotThinking(typingNode);
    exitGeneratingState();
    chatInProgress = false;

    if (err.name === "AbortError") {
      postEvent("fetch_aborted", { message: lastUserMessage });
      console.log("Fetch aborted by user.");
    } else {
      console.error(err);
      renderBotMessage("Something went wrong, please retry.");
      postEvent("send_error", { error: err.message || err });
    }
  } finally {
    currentAbort = null;
    chatInProgress = false;
  }
}

  // === MESSAGE RENDERING ===
  function renderUserMessage(text) {
    const msg = document.createElement("div");
    msg.className = "user-msg";
    msg.textContent = text;
    chatBox.appendChild(msg);
    requestAnimationFrame(() => msg.classList.add("show"));
    autoScrollToBottom();
  }

  function renderBotMessage(text, { mode = "fade", delay = 200, typewriterSpeed = 20 } = {}) {
    return new Promise(async (resolve) => {
      const msg = document.createElement("div");
      msg.className = "bot-msg aether-reply";
      const content = document.createElement("div");
      content.className = "reveal";
      msg.appendChild(content);
      chatBox.appendChild(msg);
      

      await new Promise((r) => setTimeout(r, delay));
      requestAnimationFrame(() => msg.classList.add("show"));

      text = text.replace(/^(\s*AETHER[:：]\s*)+/i, "").trim();
      const prefixHTML = `<strong class="aether-prefix">AETHER:</strong> `;

      if (mode === "typewriter") {
  content.innerHTML = prefixHTML;
  // if backend returned a prefix to render immediately (we may get prefix back), append characters
  // If we're resuming, server will return a full string; server should return only continuation text.
  await typewriterEffect(content, " " + text, typewriterSpeed);
} else {
  content.innerHTML = `${prefixHTML}${text}`;
}


      autoScrollToBottom();

      resolve();
    });
  }

  function renderBotThinking() {
  document.querySelectorAll(".typing-bubble, .typing-indicator, .bot-msg.typing").forEach((n) => n.remove());
  const node = document.createElement("div");
  node.className = "bot-msg typing-bubble show";
  node.innerHTML = `<div class="typing-dots"><span></span><span></span><span></span></div>`;
  chatBox.appendChild(node);
  requestAnimationFrame(() => node.classList.add("show"));
  autoScrollToBottom();
  return node;
}


  function stopBotThinking(node) {
    if (!node) return;
    node.classList.add("fade-out");
    setTimeout(() => node.remove(), 250);
  }

    async function typewriterEffect(container, text, speed = 18) {
    isTyping = true;
    let i = 0;

    // If we were resuming, the container may already have prefix text.
    const existingTextLength = Array.from(container.querySelectorAll(".type-char")).length;
    if (existingTextLength > 0) {
      i = existingTextLength;
    }

    while (i < text.length) {
      if (paused) {
        // store remaining for resume
        const remaining = text.slice(i);
        lastPartial.remaining = remaining;
        // store what has been rendered so far (prefix)
        const rendered = text.slice(0, i);
        lastPartial.prefix = rendered;
        break;
      }

      const span = document.createElement("span");
      span.className = "type-char";
      span.textContent = text[i];
      container.appendChild(span);
      await new Promise((r) => setTimeout(r, speed));
      span.classList.add("visible");
      i++;

      // update live partial state occasionally (helps resume accuracy)
      if (i % 6 === 0) {
        lastPartial.prefix = text.slice(0, i);
        lastPartial.remaining = text.slice(i);
      }

      // smooth follow scroll unless user manually scrolled away
      // only auto-scroll if user is at bottom AND not scrolling manually
if (!userScrolledUp && !autoScrollLocked) {
  chatBox.scrollTop = chatBox.scrollHeight;
}


    }

    // if finished naturally, clear remaining and persist final prefix
    if (i >= text.length) {
      lastPartial.prefix = text;
      lastPartial.remaining = "";
    }

    isTyping = false;
  }



  // === SECTION RENDERER (news/youtube/reddit) ===
  async function renderSection(title, items = [], type = "") {
    if (!items || !items.length) return;

    const section = document.createElement("div");
    section.className = "bot-msg show section-block";

    const header = document.createElement("div");
    header.className = `section-header ${type}`;

    let iconHTML = "";
    if (type === "news") iconHTML = `<img src="/static/icons/news.svg" class="section-icon news-icon" alt="News" />`;
    else if (type === "youtube") iconHTML = `<img src="/static/icons/youtube.svg" class="section-icon youtube-icon" alt="YouTube" />`;
    else if (type === "reddit") iconHTML = `<img src="/static/icons/reddit.svg" class="section-icon reddit-icon" alt="Reddit" />`;

    header.innerHTML = `${iconHTML}<strong>${title}</strong>`;
    section.appendChild(header);

    const results = document.createElement("div");
    results.className = "results-container";

    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      const a = document.createElement("a");
      a.className = `result-card ${type}`;
      a.href = item.url || "#";
      a.target = "_blank";

      if (item.source_type === "youtube" && item.url?.includes("v=")) {
        const id = item.url.split("v=")[1]?.split("&")[0];
        if (id) {
          const thumb = document.createElement("img");
          thumb.src = `https://img.youtube.com/vi/${id}/hqdefault.jpg`;
          thumb.className = "yt-thumb";
          a.appendChild(thumb);
        }
      }

      const body = document.createElement("div");
      body.className = "result-body";
      body.innerHTML = `
        <div class="result-title">${item.title || "Untitled"}</div>
        <div class="result-meta">${buildMeta(item)}</div>
      `;
      a.appendChild(body);
      results.appendChild(a);
      setTimeout(() => a.classList.add("show"), i * 140 + 160);
    }

    section.appendChild(results);
    chatBox.appendChild(section);
    autoScrollToBottom();

    setTimeout(() => scrollToBottom(true), 300);


    // === Show More Button ===
    const showMoreBtn = document.createElement("button");
    showMoreBtn.className = "show-more-btn";
    showMoreBtn.textContent = `+ Show more ${type}`;
    section.appendChild(showMoreBtn);

    showMoreBtn.addEventListener("click", async () => {
  showMoreBtn.disabled = true;
  showMoreBtn.textContent = "Loading...";

  // 🚫 Temporarily stop auto-scroll from triggering
  autoScrollLocked = true;
  observer.disconnect();

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: lastUserMessage, append: true, type }),
    });
    const data = await res.json();

    if (data.status === "success") {
      for (const item of data.results.slice(0, 3)) {
        const newCard = document.createElement("a");
        newCard.className = `result-card ${type}`;
        newCard.href = item.url || "#";
        newCard.target = "_blank";

        // Preserve thumbnails for YouTube
        if (type === "youtube" && item.url?.includes("v=")) {
          const id = item.url.split("v=")[1]?.split("&")[0];
          if (id) {
            const thumb = document.createElement("img");
            thumb.src = `https://img.youtube.com/vi/${id}/hqdefault.jpg`;
            thumb.className = "yt-thumb";
            newCard.appendChild(thumb);
          }
        }

        const body = document.createElement("div");
        body.className = "result-body";
        body.innerHTML = `
          <div class="result-title">${item.title || "Untitled"}</div>
          <div class="result-meta">${buildMeta(item)}</div>
        `;
        newCard.appendChild(body);
        results.appendChild(newCard);
        requestAnimationFrame(() => newCard.classList.add("show"));
      }

      // ✅ Maintain visual stability — prevent weird jumps
const previousScroll = chatBox.scrollTop; // where user was
const previousHeight = chatBox.scrollHeight;

await new Promise((r) => setTimeout(r, 300)); // give new cards time to render

const newHeight = chatBox.scrollHeight;
const addedHeight = newHeight - previousHeight;

// only scroll by the added height (so screen feels still)
chatBox.scrollTo({
  top: previousScroll + Math.min(addedHeight, 250),
  behavior: "smooth",
});

    }
  } catch (err) {
    console.error("⚠️ Error appending more:", err);
  } finally {
    // 🕓 Wait a bit, then re-enable auto-scroll watching
    setTimeout(() => {
      autoScrollLocked = false;
      observer.observe(chatBox, { childList: true, subtree: true });
    }, 1200);

    showMoreBtn.disabled = false;
    showMoreBtn.textContent = `+ Show more ${type}`;
  }
});

  }
  // === UI STATE CONTROL ===
function enterGeneratingState() {
  sendBtn.dataset.role = "pause";
  sendBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>`;
  sendBtn.classList.add("stop-active");

  userInput.disabled = true;
  micBtn.disabled = true;
  micBtn.classList.add("mic-disabled");

  sendBtn.setAttribute("aria-pressed", "true");
}


function exitGeneratingState() {
  sendBtn.dataset.role = "send";
  sendBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M2 21l21-9L2 3v7l15 2-15 2z"/></svg>`;
  sendBtn.classList.remove("stop-active");

  // ✅ Re-enable input + mic after generation completes
  userInput.disabled = false;
  micBtn.disabled = false;
  micBtn.classList.remove("mic-disabled");

  sendBtn.setAttribute("aria-pressed", "false");
}



  // === META BUILDER ===
  function buildMeta(i) {
    if (i.source_type === "news") return `${i.author || "News Desk"} • ${i.published || ""}`;
    if (i.source_type === "youtube")
      return `${i.channel || "Channel"} • ${i.views ? i.views.toLocaleString() + " views" : ""} • ${i.published || ""}`;
    if (i.source_type === "reddit")
      return `r/${i.subreddit || "unknown"} • ${i.upvotes ? i.upvotes.toLocaleString() + " upvotes" : ""} • ${i.published || ""}`;
    return i.published || "";
  }

async function renderBriefingCard(item) {
  if (!item) return;

  const desc = item.description || "";

  // Extract bullets
  const bullets = desc
    .split("\n")
    .filter(line => line.replace(/^\s+/,"").startsWith("•"))
    .map(line => line.replace("•", "").trim());

  // Extract Aether's Take
  let take = "";
  const takeIndex = desc.indexOf("✨ **Aether’s Take:**");
  if (takeIndex !== -1) {
    take = desc.slice(takeIndex).replace("✨ **Aether’s Take:**", "").trim();
  }

  // Create the card element
  const card = document.createElement("div");
  card.className = "bot-msg summary-card show";

  card.innerHTML = `
    <div class="summary-inner">
      <div class="summary-header-bubble">
        <span class="summary-icon"></span>
        <span class="summary-title">Aether’s Briefing</span>
        <button class="summary-toggle" aria-expanded="true">▲ Hide</button>
      </div>

      <div class="summary-body open">
        <ul class="briefing-list">
          ${bullets.map(b => `<li>${b}</li>`).join("")}
        </ul>

        <div class="summary-take">${take}</div>
      </div>
    </div>
  `;

  // Toggle logic
  const toggle = card.querySelector(".summary-toggle");
  const body = card.querySelector(".summary-body");

  toggle.addEventListener("click", () => {
    const expanded = toggle.getAttribute("aria-expanded") === "true";
    toggle.setAttribute("aria-expanded", !expanded);
    toggle.textContent = expanded ? "▼ Show" : "▲ Hide";
    body.classList.toggle("open", !expanded);
  });

  chatBox.appendChild(card);
  scrollToBottom(true);
}


  // === RESPONSE HANDLER ===
  async function renderResponseData(data) {
    // 🚀 Always unlock auto-scroll before rendering heavy content (fixes YT freeze)
userScrolledUp = false;
autoScrollLocked = false;

    if (!data || data.status !== "success") return;
    const grouped = { news: [], youtube: [], reddit: [], summary: [], aether_reply: [] };

// ✅ FIX: extract the summary/briefing item FIRST
const summaryItem = (data.results || []).find(
  (i) => i.source_type === "summary" || i.source_type === "briefing"
);

(data.results || []).forEach((i) => {
  const st = i.source_type || "aether_reply";
  if (!grouped[st]) grouped[st] = [];
  grouped[st].push(i);
});

if (grouped.news.length) await renderSection("News", grouped.news, "news");
if (grouped.youtube.length) await renderSection("YouTube", grouped.youtube, "youtube");
if (grouped.reddit.length) await renderSection("Reddit", grouped.reddit, "reddit");

// 🎉 FINALLY WORKS
if (summaryItem) renderBriefingCard(summaryItem);

// === Render Aether replies (resume-aware continuation)
const aetherReplies = (data.results || []).filter(
  i => i.source_type === "aether_reply"
);
const hasBriefing = !!summaryItem;

for (const reply of aetherReplies) {
  if (!reply.title) continue;

  // 🔥 NEW: If backend indicates continuation, append to SAME bubble
  if (data.resume) {
    const lastBubble = chatBox.querySelector(".bot-msg.aether-reply:last-child .reveal");
    if (lastBubble) {
      await typewriterEffect(lastBubble, reply.title, 18);
      autoScrollToBottom();
      continue;
    }
  }

  // Normal flow → create new bubble
  await renderBotMessage(reply.title, {
    mode: "typewriter",
    delay: 150,
    typewriterSpeed: 18,
  });
}
  }
});

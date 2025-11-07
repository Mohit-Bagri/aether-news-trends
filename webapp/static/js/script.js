document.addEventListener("DOMContentLoaded", () => {
  const chatForm = document.getElementById("chatForm");
  const userInput = document.getElementById("userInput");
  const chatBox = document.getElementById("chatBox");
  const sendBtn = document.getElementById("sendBtn");
  const micBtn = document.getElementById("micBtn");

  let currentAbort = null;
  let isPaused = false;
  let isGenerating = false;
  let lastUserMessage = "";

  const smoothScroll = () => chatBox.scrollTo({ top: chatBox.scrollHeight + 200, behavior: "smooth" });

  console.log("✅ Aether JS loaded");
  renderBotMessage("👋 Hey, I'm Aether — your AI companion! Ask me anything.", { mode: "fade", delay: 300 });

  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    handleSend();
  });

  async function handleSend() {
    const message = userInput.value.trim();
    if (!message) return;
    lastUserMessage = message; // ✅ store for resume

    renderUserMessage(message);
    userInput.value = "";

    const typingNode = renderBotThinking();
    enterGeneratingState(); // disable input, turn send → stop

    try {
      const controller = new AbortController();
      currentAbort = controller;
      isPaused = false;
      isGenerating = true;

      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
        signal: controller.signal,
      });

      const data = await res.json();
      stopBotThinking(typingNode);
      exitGeneratingState();

      if (!data || data.status !== "success") {
        if (data?.status === "cancelled" || isPaused) {
          await renderBotMessage("⏸ Response paused.", { mode: "fade" });
          chatBox.lastChild.classList.add("paused");
          renderResumeButton();
        } else {
          await renderBotMessage("⚠️ I couldn’t find anything for that.", { mode: "fade" });
        }
        return;
      }

      if (data.reply && !isPaused) {
        const isLong = data.reply.length > 250;
        await renderBotMessage(data.reply, { mode: isLong ? "typewriter" : "fade" });
      }

      const grouped = { news: [], youtube: [], reddit: [] };
      (data.results || []).forEach(i => grouped[i.source_type]?.push(i));
      await renderSection("News", grouped.news, "news");
      await renderSection("YouTube", grouped.youtube, "youtube");
      await renderSection("Reddit", grouped.reddit, "reddit");
    } catch (err) {
      stopBotThinking(typingNode);
      exitGeneratingState();

      if (isPaused) {
        await renderBotMessage("⏸ Response paused.", { mode: "fade" });
        chatBox.lastChild.classList.add("paused");
        renderResumeButton();
      } else {
        await renderBotMessage("⚠️ Server not responding.", { mode: "fade" });
      }
    }
  }

  // 🧠 Resume same query logic
  async function handleSendResume() {
  if (!lastUserMessage) return;

  document.querySelectorAll(".bot-msg.paused").forEach(el => {
  el.classList.add("slide-up-fade");
  setTimeout(() => el.remove(), 600);
});

  const typingNode = renderBotThinking();
  enterGeneratingState();


    try {
      const controller = new AbortController();
      currentAbort = controller;
      isPaused = false;
      isGenerating = true;

      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: lastUserMessage }),
        signal: controller.signal,
      });

      const data = await res.json();
      stopBotThinking(typingNode);
      exitGeneratingState();

      if (!data || data.status !== "success") {
        if (!isPaused) await renderBotMessage("⚠️ I couldn’t find anything for that.", { mode: "fade" });
        return;
      }

      if (data.reply && !isPaused) {
        const isLong = data.reply.length > 250;
        await renderBotMessage(data.reply, { mode: isLong ? "typewriter" : "fade" });
      }

      const grouped = { news: [], youtube: [], reddit: [] };
      (data.results || []).forEach(i => grouped[i.source_type]?.push(i));
      await renderSection("News", grouped.news, "news");
      await renderSection("YouTube", grouped.youtube, "youtube");
      await renderSection("Reddit", grouped.reddit, "reddit");

    } catch (err) {
      stopBotThinking(typingNode);
      exitGeneratingState();
      if (!isPaused) await renderBotMessage("⚠️ Server not responding.", { mode: "fade" });
    }
  }

  // 🪄 Continue generating button
  function renderResumeButton() {
    document.querySelectorAll(".resume-btn").forEach(b => b.remove());

    const btn = document.createElement("button");
    btn.className = "resume-btn fade-in";
    btn.textContent = "Continue generating";

    btn.onclick = async () => {
      btn.disabled = true;
      btn.textContent = "⏳ Resuming...";
      await handleSendResume();
      btn.remove();
    };

    chatBox.appendChild(btn);
    smoothScroll();
  }

  function enterGeneratingState() {
    userInput.disabled = true;
    micBtn.disabled = true;
    micBtn.style.opacity = "0.4";
    userInput.style.opacity = "0.6";

    sendBtn.innerHTML = `
      <svg viewBox="0 0 24 24" fill="#ff6b6b">
        <rect x="6" y="6" width="12" height="12" rx="2" ry="2"/>
      </svg>`;
    sendBtn.classList.add("stop-active");
    sendBtn.disabled = false; // only this stays clickable
    sendBtn.onclick = stopGeneration;

    // 🧹 Remove resume button if exists
    document.querySelectorAll(".resume-btn").forEach(b => b.remove());
  }

  function exitGeneratingState() {
    userInput.disabled = false;
    micBtn.disabled = false;
    micBtn.style.opacity = "1";
    userInput.style.opacity = "1";

    sendBtn.innerHTML = sendIcon;
    sendBtn.classList.remove("stop-active");
    sendBtn.onclick = () => {
      if (!userInput.value.trim()) return;
      sendBtn.classList.add("launching");
      setTimeout(() => sendBtn.classList.remove("launching"), 700);
      handleSend();
    };

    // 🧠 remove resume buttons once new generation starts
    document.querySelectorAll(".resume-btn").forEach(b => b.remove());
  }

  function stopGeneration() {
    isPaused = true;
    if (currentAbort) currentAbort.abort();

    // ✅ Instantly remove typing dots
    document.querySelectorAll(".typing-bubble").forEach(el => el.remove());

    exitGeneratingState();
  }

  // === Message Rendering ===
  function renderUserMessage(text) {
    const msg = document.createElement("div");
    msg.className = "user-msg";
    msg.textContent = text;
    chatBox.appendChild(msg);
    requestAnimationFrame(() => msg.classList.add("show"));
    smoothScroll();
  }

  function renderBotThinking() {
    const node = document.createElement("div");
    node.className = "bot-msg typing-bubble";
    node.innerHTML = `<div class="typing-dots"><span></span><span></span><span></span></div>`;
    chatBox.appendChild(node);
    requestAnimationFrame(() => node.classList.add("show"));
    smoothScroll();
    return node;
  }

  function stopBotThinking(node) { if (node) node.remove(); }

  async function renderBotMessage(text, { mode = "fade", delay = 200, typewriterSpeed = 18 } = {}) {
    const msg = document.createElement("div");
    msg.className = "bot-msg";
    const content = document.createElement("div");
    content.className = "reveal";
    msg.appendChild(content);
    chatBox.appendChild(msg);
    smoothScroll();

    await new Promise(r => setTimeout(r, delay));
    msg.classList.add("show");

    if (mode === "typewriter") {
      await typewriterEffect(content, text, typewriterSpeed);
    } else {
      content.textContent = text;
      requestAnimationFrame(() => content.classList.add("visible"));
    }
    smoothScroll();
  }

  async function typewriterEffect(container, text, speed = 20) {
    container.textContent = "";
    for (let char of text) {
      if (isPaused) break;
      const span = document.createElement("span");
      span.className = "type-char";
      span.textContent = char;
      container.appendChild(span);
      await new Promise(r => setTimeout(r, speed));
      span.classList.add("visible");
    }
  }

  async function renderSection(title, items = [], type = "") {
    if (!items.length) return;
    const wrapper = document.createElement("div");
    wrapper.className = "bot-msg show";

    const header = document.createElement("div");
    header.className = `section-header ${type}`;

    const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    icon.setAttribute("viewBox", "0 0 24 24");
    icon.classList.add("section-icon");

    icon.innerHTML = {
      news: `<path fill="#4CA8FF" d="M3 5h18v14H3zM5 7v10h14V7z"/>`,
      youtube: `<path fill="#FF0000" d="M23.498 6.186a2.994 2.994 0 0 0-2.111-2.118C19.228 3.5 12 3.5 12 3.5s-7.228 0-9.387.568A2.994 2.994 0 0 0 .502 6.186A31.056 31.056 0 0 0 0 12a31.056 31.056 0 0 0 .502 5.814a2.994 2.994 0 0 0 2.111 2.118C4.772 20.5 12 20.5 12 20.5s7.228 0 9.387-.568a2.994 2.994 0 0 0 2.111-2.118A31.056 31.056 0 0 0 24 12a31.056 31.056 0 0 0-.502-5.814zM9.75 15.02V8.98L15.5 12z"/>`,
      reddit: `<path fill="#FF4500" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.95 9.68a.83.83 0 110 1.67.83.83 0 010-1.67zM7.05 9.68a.83.83 0 110 1.67.83.83 0 010-1.67zM12 17.3c-1.86 0-3.44-1.06-3.44-2.36h6.88c0 1.3-1.58 2.36-3.44 2.36zm5.37-3.64a5.55 5.55 0 01-10.74 0 3.92 3.92 0 01-.63-2.08c0-2.32 2.57-4.2 5.73-4.2s5.73 1.88 5.73 4.2c0 .75-.23 1.46-.63 2.08z"/>`
    }[type] || "";

    header.appendChild(icon);
    const span = document.createElement("span");
    span.textContent = { news: "News", youtube: "YouTube", reddit: "Reddit" }[type] || title;
    header.appendChild(span);
    wrapper.appendChild(header);

    const results = document.createElement("div");
    results.className = "results-container";
    wrapper.appendChild(results);
    chatBox.appendChild(wrapper);
    smoothScroll();

    for (let i = 0; i < items.length; i++) {
      const card = makeCard(items[i], type);
      results.appendChild(card);
      setTimeout(() => card.classList.add("show"), i * 220 + 180);
      await new Promise(r => setTimeout(r, 120));
    }
    smoothScroll();
  }

  function makeCard(i, type) {
    const a = document.createElement("a");
    a.className = `result-card ${type}`;
    a.href = i.url || "#";
    a.target = "_blank";
    if (i.source_type === "youtube" && i.url.includes("youtu")) {
      const thumb = document.createElement("img");
      const id = i.url.split("v=")[1]?.split("&")[0];
      if (id) thumb.src = `https://img.youtube.com/vi/${id}/hqdefault.jpg`;
      thumb.className = "yt-thumb";
      a.appendChild(thumb);
    }
    const body = document.createElement("div");
    body.className = "result-body";
    const title = document.createElement("div");
    title.className = "result-title";
    title.textContent = i.title || "Untitled";
    const meta = document.createElement("div");
    meta.className = "result-meta";
    meta.textContent = buildMeta(i);
    body.appendChild(title);
    body.appendChild(meta);
    a.appendChild(body);
    return a;
  }

  function buildMeta(i) {
    if (i.source_type === "news")
      return `${i.author || "News Desk"} • ${i.published || ""}`;
    if (i.source_type === "youtube")
      return `${i.channel || "Channel"} • ${i.views?.toLocaleString()} views • ${i.published}`;
    if (i.source_type === "reddit")
      return `r/${i.subreddit || "unknown"} • ${i.upvotes?.toLocaleString()} upvotes • ${i.published}`;
    return i.published || "";
  }

  const sendIcon = `
    <svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M2 21l21-9L2 3v7l15 2-15 2z"/>
    </svg>`;

  const micIcon = `
    <svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 14a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3z"/>
      <path d="M19 11a1 1 0 0 0-1 1 6 6 0 0 1-12 0 1 1 0 0 0-2 0 8 8 0 0 0 7 7.93V22h2v-2.07a8 8 0 0 0 7-7.93 1 1 0 0 0-1-1z"/>
    </svg>`;

  micBtn.innerHTML = micIcon;
  sendBtn.innerHTML = sendIcon;

  // 🎙️ Mic speech recognition
  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;

    micBtn.addEventListener("click", () => {
      if (micBtn.classList.contains("listening")) {
        recognition.stop();
        micBtn.classList.remove("listening");
      } else {
        recognition.start();
        micBtn.classList.add("listening");
      }
    });

    recognition.addEventListener("result", (event) => {
      const transcript = event.results[0][0].transcript;
      userInput.value = transcript;
    });

    recognition.addEventListener("end", () => micBtn.classList.remove("listening"));
  } else {
    micBtn.style.display = "none";
  }
});

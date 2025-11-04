const chatForm = document.getElementById("chatForm");
const chatBox = document.getElementById("chatBox");
const userInput = document.getElementById("userInput");

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = userInput.value.trim();
  if (!message) return;

  appendMessage("user", message);
  userInput.value = "";

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    const data = await res.json();
    console.log("Response:", data);

    if (data.status === "error") {
      appendMessage("bot", `⚠️ ${data.error}`, "error");
      return;
    }

    displayResults(data);
  } catch (err) {
    console.error(err);
    appendMessage("bot", `❌ Server error: ${err}`, "error");
  }

  chatBox.scrollTop = chatBox.scrollHeight;
});

function appendMessage(sender, text, type = "") {
  const msgDiv = document.createElement("div");
  msgDiv.className = `${sender}-msg ${type}`;
  msgDiv.textContent = sender === "user" ? `🧑‍💻 ${text}` : text;
  chatBox.appendChild(msgDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function displayResults(data) {
  const container = document.createElement("div");
  container.className = "bot-msg fade-in";

  let html = `<h3 style="color:#2563eb;">🧩 ${data.topic}</h3>`;

  if (data.summary) {
    html += `<p style="margin-bottom:0.5rem;">${data.summary}</p>`;
  }

  const results = Array.isArray(data.results) ? data.results : [];

  // Group results by type
  const news = results.filter(r => r.source_type === "news");
  const youtube = results.filter(r => r.source_type === "youtube");
  const reddit = results.filter(r => r.source_type === "reddit");

  if (news.length) {
    html += `
      <div class="section-card">
        <h4>📰 Top News Articles</h4>
        <ul>
          ${news.slice(0, 4)
            .map(n => `<li><a href="${n.url}" target="_blank">${n.title}</a></li>`)
            .join("")}
        </ul>
      </div>`;
  }

  if (youtube.length) {
    html += `
      <div class="section-card">
        <h4>🎥 YouTube Highlights</h4>
        <ul>
          ${youtube.slice(0, 3)
            .map(v => `<li><a href="${v.url}" target="_blank">${v.title}</a></li>`)
            .join("")}
        </ul>
      </div>`;
  }

  if (reddit.length) {
    html += `
      <div class="section-card">
        <h4>💬 Reddit Discussions</h4>
        <ul>
          ${reddit.slice(0, 3)
            .map(p => `<li><a href="${p.url}" target="_blank">${p.title}</a></li>`)
            .join("")}
        </ul>
      </div>`;
  }

  if (!news.length && !youtube.length && !reddit.length) {
    html += `<p>No detailed results found.</p>`;
  }

  container.innerHTML = html;
  chatBox.appendChild(container);
  chatBox.scrollTop = chatBox.scrollHeight;
}

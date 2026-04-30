/**
 * Chat UI — POST JSON to /api/chat (same origin on Vercel or uvicorn).
 */

const API_URL = "/api/chat";

const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("msg");
const sendBtn = document.getElementById("send");
const errorEl = document.getElementById("error");

/** @type {Array<{role: string, content: string}>} */
let history = [];

function showError(text) {
  errorEl.textContent = text;
  errorEl.hidden = !text;
}

function appendMessage(role, content) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  const label = document.createElement("span");
  label.className = "role";
  label.textContent = role === "user" ? "You" : "Assistant";
  const body = document.createElement("div");
  body.textContent = content;
  div.append(label, body);
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function setLoading(loading) {
  sendBtn.disabled = loading;
  inputEl.disabled = loading;
}

formEl.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = inputEl.value.trim();
  if (!message) return;

  showError("");
  appendMessage("user", message);
  inputEl.value = "";
  setLoading(true);

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      const detail = data.detail ?? data.message ?? res.statusText;
      showError(typeof detail === "string" ? detail : "Request failed.");
      setLoading(false);
      return;
    }

    history = data.history ?? history;
    const reply = data.reply ?? "";
    if (reply) {
      appendMessage("assistant", reply);
    }
  } catch {
    showError("Network error — check your connection and try again.");
  } finally {
    setLoading(false);
    inputEl.focus();
  }
});

inputEl.focus();

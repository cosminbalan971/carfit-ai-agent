const $ = (id) => document.getElementById(id);

const state = { session_id: null };

function setStatus(msg) {
  const el = $("status");
  if (el) el.textContent = msg || "";
}

function setSession(id) {
  state.session_id = id || null;
  const el = $("sessionId");
  if (el) el.textContent = id || "—";
}

function addBubble(text, who) {
  const chat = $("chat");
  if (!chat) return;

  const row = document.createElement("div");
  row.className = `message-row ${who === "user" ? "user-row" : "bot-row"}`;

  const bubble = document.createElement("div");
  bubble.className = `bubble ${who}`;
  bubble.textContent = text;

  row.appendChild(bubble);
  chat.appendChild(row);
  chat.scrollTop = chat.scrollHeight;
}

async function apiPost(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const text = await res.text();

  let data = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { raw: text };
  }

  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }

  return data;
}

async function sendMessage() {
  const input = $("msg");
  const sendBtn = $("sendBtn");

  if (!input) return;

  const message = input.value.trim();
  if (!message) return;

  addBubble(message, "user");
  input.value = "";

  try {
    if (sendBtn) sendBtn.disabled = true;
    setStatus("Thinking...");

    const data = await apiPost("/chat", {
      session_id: state.session_id,
      message: message
    });

    setSession(data.session_id || null);

    if (data.final_answer) {
      addBubble(data.final_answer, "bot");
    } else if (Array.isArray(data.clarifying_questions) && data.clarifying_questions.length > 0) {
      const questions =
        "I need a bit more info first:\n- " +
        data.clarifying_questions.join("\n- ");
      addBubble(questions, "bot");
    } else if (data.message) {
      addBubble(data.message, "bot");
    } else if (data.raw) {
      addBubble(data.raw, "bot");
    } else {
      addBubble("I received a response, but it did not contain final_answer or clarifying_questions.", "bot");
    }

    setStatus("");
  } catch (e) {
    addBubble(`Error: ${e.message}`, "bot");
    setStatus("Something went wrong.");
  } finally {
    if (sendBtn) sendBtn.disabled = false;
    if (input) input.focus();
  }
}

async function resetSession() {
  const resetBtn = $("resetBtn");
  const chat = $("chat");

  try {
    if (resetBtn) resetBtn.disabled = true;
    setStatus("Resetting session...");

    const data = await apiPost("/session/reset", {
      session_id: state.session_id
    });

    setSession(data.session_id || null);

    if (chat) {
      chat.innerHTML = `
        <div class="welcome">
          <div class="welcome-title">Find your car fit</div>
          <div class="welcome-subtitle">
            Describe what you want naturally — for example:
            “quiet hybrid SUV, comfy, 2018+, budget 18k”
          </div>
        </div>
      `;
    }

    setStatus("Session reset.");
  } catch (e) {
    addBubble(`Error: ${e.message}`, "bot");
    setStatus("Reset failed.");
  } finally {
    if (resetBtn) resetBtn.disabled = false;
  }
}

window.addEventListener("DOMContentLoaded", () => {
  const sendBtn = $("sendBtn");
  const msg = $("msg");
  const resetBtn = $("resetBtn");

  if (sendBtn) {
    sendBtn.addEventListener("click", sendMessage);
  }

  if (msg) {
    msg.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        sendMessage();
      }
    });
  }

  if (resetBtn) {
    resetBtn.addEventListener("click", resetSession);
  }
});
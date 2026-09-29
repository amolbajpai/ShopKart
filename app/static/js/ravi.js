(() => {
  const launcher = document.getElementById("ravi-launcher");
  const panel = document.getElementById("ravi-panel");
  const thread = document.getElementById("ravi-thread");
  const form = document.getElementById("ravi-form");
  const input = document.getElementById("ravi-input");
  const history = [];

  function linkify(text) {
    const escaped = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
    return escaped
      .replace(/\/product\/(\d+)/g, '<a href="/product/$1">/product/$1</a>')
      .replace(/\n/g, "<br>");
  }

  function addBubble(role, text) {
    const el = document.createElement("div");
    el.className = "ravi-msg " + role;
    el.innerHTML = linkify(text);
    thread.appendChild(el);
    thread.scrollTop = thread.scrollHeight;
  }

  function greet() {
    if (thread.childElementCount) return;
    addBubble(
      "assistant",
      "Hi, I am Ravi — ShopKart's shopping assistant. Ask me to find products, compare options, or explain the store."
    );
  }

  launcher.addEventListener("click", () => {
    panel.classList.toggle("hidden");
    if (!panel.classList.contains("hidden")) {
      greet();
      input.focus();
    }
  });
  document.getElementById("ravi-close").addEventListener("click", () => {
    panel.classList.add("hidden");
  });

  document.getElementById("ravi-chips").addEventListener("click", (e) => {
    const btn = e.target.closest("button[data-q]");
    if (!btn) return;
    input.value = btn.dataset.q;
    form.requestSubmit();
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    input.value = "";
    addBubble("user", message);
    const pending = document.createElement("div");
    pending.className = "ravi-msg assistant";
    pending.textContent = "Ravi is thinking…";
    thread.appendChild(pending);
    thread.scrollTop = thread.scrollHeight;
    try {
      const data = await api.post("/api/ravi/chat", { message, history });
      pending.remove();
      addBubble("assistant", data.reply);
      history.push({ role: "user", content: message });
      history.push({ role: "assistant", content: data.reply });
      if (history.length > 16) history.splice(0, history.length - 16);
    } catch (err) {
      pending.textContent = err.message || "Ravi could not answer right now.";
    }
  });
})();

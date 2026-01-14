const statusPill = document.getElementById("status-pill");
const logConsole = document.getElementById("log-console");
const chatInput = document.getElementById("chat-input");
const chatOutput = document.getElementById("chat-output");
const chatSend = document.getElementById("chat-send");
const taskAppInput = document.getElementById("task-app");
const taskYoutubeInput = document.getElementById("task-youtube");
const taskResult = document.getElementById("task-result");

function setStatus(label, state) {
  statusPill.textContent = label;
  statusPill.classList.remove("connected", "busy");
  if (state) {
    statusPill.classList.add(state);
  }
}

function appendLog(entry) {
  const line = document.createElement("div");
  line.className = "log-entry";
  line.innerHTML = `<span>[${entry.timestamp}]</span> ${entry.event} ${
    entry.data ? JSON.stringify(entry.data) : ""
  }`;
  logConsole.appendChild(line);
  logConsole.scrollTop = logConsole.scrollHeight;
}

function appendChat(speaker, message) {
  const paragraph = document.createElement("p");
  paragraph.innerHTML = `<strong>${speaker}:</strong> ${message}`;
  chatOutput.appendChild(paragraph);
  chatOutput.scrollTop = chatOutput.scrollHeight;
}

function handleLogEvent(entry) {
  appendLog(entry);
  if (entry.event === "llm_start") {
    setStatus("LLM responding…", "busy");
  }
  if (entry.event === "task_start") {
    setStatus("Running task…", "busy");
  }
  if (entry.event === "llm_done" || entry.event === "task_done") {
    setStatus("Connected", "connected");
  }
}

function connectWebSocket() {
  const ws = new WebSocket(`ws://${window.location.host}/ws/logs`);

  ws.addEventListener("open", () => {
    setStatus("Connected", "connected");
    ws.send("hello");
  });

  ws.addEventListener("message", (event) => {
    const entry = JSON.parse(event.data);
    handleLogEvent(entry);
  });

  ws.addEventListener("close", () => {
    setStatus("Disconnected", "");
    connectSSE();
  });

  return ws;
}

function connectSSE() {
  const source = new EventSource("/api/logs/stream");
  source.onmessage = (event) => {
    const entry = JSON.parse(event.data);
    handleLogEvent(entry);
  };
  source.onerror = () => {
    setStatus("Disconnected", "");
  };
}

async function sendChat() {
  const message = chatInput.value.trim();
  if (!message) {
    return;
  }
  chatSend.disabled = true;
  appendChat("You", message);
  chatInput.value = "";

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const payload = await response.json();
    if (!response.ok) {
      appendChat("Victus", payload.detail || "Error retrieving response.");
    } else {
      appendChat("Victus", payload.reply);
    }
  } catch (error) {
    appendChat("Victus", "Network error while contacting server.");
  } finally {
    chatSend.disabled = false;
  }
}

async function runTask(action, args) {
  taskResult.textContent = "Running task...";
  try {
    const response = await fetch("/api/task", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, args }),
    });
    const payload = await response.json();
    if (!response.ok) {
      taskResult.textContent = payload.detail || "Task failed.";
    } else {
      taskResult.textContent = `Task complete: ${JSON.stringify(payload.result)}`;
    }
  } catch (error) {
    taskResult.textContent = "Network error while running task.";
  }
}

chatSend.addEventListener("click", sendChat);
chatInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendChat();
  }
});

document.querySelectorAll("button[data-task]").forEach((button) => {
  button.addEventListener("click", () => {
    const task = button.dataset.task;
    if (task === "open_app") {
      runTask(task, { name: taskAppInput.value });
    }
    if (task === "open_youtube") {
      runTask(task, { query: taskYoutubeInput.value });
    }
  });
});

connectWebSocket();

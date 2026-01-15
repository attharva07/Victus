const statusPill = document.getElementById("status-pill");
const chatInput = document.getElementById("chat-input");
const chatOutput = document.getElementById("chat-output");
const logsOutput = document.getElementById("logs-output");
const chatSend = document.getElementById("chat-send");
const chatStop = document.getElementById("chat-stop");

let activeController = null;
let streamingMessage = null;
let streamingText = null;
let logsSource = null;
let reconnectTimeout = null;

function setStatus(label, state) {
  statusPill.textContent = label;
  statusPill.classList.remove("connected", "busy", "error");
  if (state) {
    statusPill.classList.add(state);
  }
}

function setStatusFromServer(status) {
  if (status === "thinking") {
    setStatus("Thinking", "busy");
    return;
  }
  if (status === "executing") {
    setStatus("Executing", "busy");
    return;
  }
  if (status === "done") {
    setStatus("Done", "connected");
    return;
  }
  if (status === "error") {
    setStatus("Error", "error");
  }
}

function appendMessage(role, message) {
  const paragraph = document.createElement("p");
  const strong = document.createElement("strong");
  strong.textContent = `${role}: `;
  const span = document.createElement("span");
  span.textContent = message;
  paragraph.appendChild(strong);
  paragraph.appendChild(span);
  chatOutput.appendChild(paragraph);
  chatOutput.scrollTop = chatOutput.scrollHeight;
}

function beginStreamMessage() {
  streamingMessage = document.createElement("p");
  const strong = document.createElement("strong");
  strong.textContent = "Victus: ";
  streamingText = document.createElement("span");
  streamingMessage.appendChild(strong);
  streamingMessage.appendChild(streamingText);
  chatOutput.appendChild(streamingMessage);
}

function appendStreamChunk(chunk) {
  if (!streamingMessage) {
    beginStreamMessage();
  }
  streamingText.textContent += chunk;
  chatOutput.scrollTop = chatOutput.scrollHeight;
}

function endStreamMessage() {
  streamingMessage = null;
  streamingText = null;
}

function addLogEntry(event, data = {}) {
  const item = document.createElement("div");
  item.className = "log-entry";
  const timestamp = new Date().toLocaleTimeString();
  const label = document.createElement("span");
  label.textContent = `${timestamp} · ${event}`;
  const detail = document.createElement("div");
  detail.textContent = JSON.stringify(data);
  item.appendChild(label);
  item.appendChild(detail);
  logsOutput.appendChild(item);
  logsOutput.scrollTop = logsOutput.scrollHeight;
}

function setStreamingUI(isStreaming) {
  chatSend.disabled = isStreaming;
  chatStop.disabled = !isStreaming;
}

function stopStreaming() {
  if (activeController) {
    activeController.abort();
    activeController = null;
    addLogEntry("client_stop", { reason: "user" });
  }
  setStreamingUI(false);
  setStatus("Connected", "connected");
  endStreamMessage();
}

function parseSseBuffer(buffer) {
  const segments = buffer.split("\n\n");
  const remainder = segments.pop() || "";
  segments.forEach((segment) => {
    if (!segment.trim()) {
      return;
    }
    const lines = segment.split("\n");
    let eventType = null;
    const dataLines = [];
    lines.forEach((line) => {
      if (line.startsWith("event:")) {
        eventType = line.replace(/^event:\s?/, "").trim();
      }
      if (line.startsWith("data:")) {
        dataLines.push(line.replace(/^data:\s?/, ""));
      }
    });
    if (!dataLines.length) {
      return;
    }
    const data = dataLines.join("\n");
    try {
      const payload = JSON.parse(data);
      handleTurnEvent(eventType || payload.event, payload);
    } catch (error) {
      addLogEntry("error", { message: "Malformed SSE payload" });
      setStatus("Error", "error");
    }
  });
  return remainder;
}

function handleTurnEvent(eventType, payload) {
  if (!eventType) {
    return;
  }
  if (eventType === "status") {
    setStatusFromServer(payload.status);
    addLogEntry("status", { status: payload.status });
    return;
  }
  if (eventType === "token") {
    const textChunk = payload.text ?? payload.token ?? "";
    if (textChunk) {
      appendStreamChunk(textChunk);
    }
    return;
  }
  if (eventType === "tool_start") {
    addLogEntry("tool_start", {
      tool: payload.tool,
      action: payload.action,
      args: payload.args,
    });
    return;
  }
  if (eventType === "tool_done") {
    addLogEntry("tool_done", {
      tool: payload.tool,
      action: payload.action,
      result: payload.result,
    });
    return;
  }
  if (eventType === "error") {
    const message = payload.message || "Request failed.";
    addLogEntry("error", { message });
    appendMessage("Victus", message);
    setStatus("Error", "error");
  }
}

async function readTurnStream(response) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    buffer = parseSseBuffer(buffer);
  }

  if (buffer.trim()) {
    parseSseBuffer(`${buffer}\n\n`);
  }
  endStreamMessage();
  if (!statusPill.classList.contains("error")) {
    setStatus("Done", "connected");
  }
}

async function sendChat() {
  const message = chatInput.value.trim();
  if (!message) {
    return;
  }

  appendMessage("You", message);
  chatInput.value = "";
  setStatus("Thinking", "busy");
  setStreamingUI(true);
  endStreamMessage();

  activeController = new AbortController();

  try {
    const response = await fetch("/api/turn", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
      signal: activeController.signal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      appendMessage("Victus", errorText || "Error retrieving response.");
      setStatus("Error", "error");
      return;
    }

    await readTurnStream(response);
  } catch (error) {
    if (error.name === "AbortError") {
      addLogEntry("client_stop", { reason: "aborted" });
      return;
    }
    appendMessage("Victus", "Network error while contacting server.");
    setStatus("Error", "error");
  } finally {
    activeController = null;
    setStreamingUI(false);
  }
}

function connectLogsStream() {
  if (logsSource) {
    logsSource.close();
  }
  logsSource = new EventSource("/api/logs/stream");

  logsSource.onopen = () => {
    setStatus("Connected", "connected");
  };

  logsSource.onmessage = (event) => {
    try {
      const entry = JSON.parse(event.data);
      if (["status_update", "tool_start", "tool_done", "turn_error"].includes(entry.event)) {
        addLogEntry(entry.event, entry.data || {});
      }
      if (entry.event === "status_update") {
        setStatusFromServer(entry.data.status);
      }
    } catch (error) {
      addLogEntry("error", { message: "Malformed log payload" });
    }
  };

  logsSource.onerror = () => {
    setStatus("Disconnected", "");
    if (logsSource) {
      logsSource.close();
    }
    if (!reconnectTimeout) {
      reconnectTimeout = setTimeout(() => {
        reconnectTimeout = null;
        connectLogsStream();
      }, 1500);
    }
  };
}

chatSend.addEventListener("click", sendChat);
chatStop.addEventListener("click", stopStreaming);
chatInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendChat();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    stopStreaming();
  }
});

setStreamingUI(false);
connectLogsStream();

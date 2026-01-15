const statusPill = document.getElementById("status-pill");
const chatInput = document.getElementById("chat-input");
const chatOutput = document.getElementById("chat-output");
const chatSend = document.getElementById("chat-send");
const timeline = document.getElementById("activity-timeline");
const toolLog = document.getElementById("tool-log");
const memoryUsed = document.getElementById("memory-used");
const memoryRecent = document.getElementById("memory-recent");
const financeSummary = document.getElementById("finance-summary");
const financeForm = document.getElementById("finance-form");
const financePreview = document.getElementById("finance-preview");
const financeExport = document.getElementById("finance-export");
const financeExportOutput = document.getElementById("finance-export-output");

let streamingMessage = null;
let streamingText = null;

function setStatus(label, state) {
  statusPill.textContent = label;
  statusPill.classList.remove("connected", "busy", "error", "denied");
  if (state) {
    statusPill.classList.add(state);
  }
}

function addTimelineEntry(title, detail) {
  const item = document.createElement("div");
  item.className = "timeline-item";
  const timestamp = new Date().toLocaleTimeString();
  item.innerHTML = `<span>${timestamp}</span><strong>${title}</strong><div>${detail || ""}</div>`;
  timeline.appendChild(item);
  timeline.scrollTop = timeline.scrollHeight;
}

function addToolEntry(title, detail) {
  const item = document.createElement("div");
  item.className = "tool-item";
  const timestamp = new Date().toLocaleTimeString();
  item.innerHTML = `<span>${timestamp}</span><strong>${title}</strong><div>${detail || ""}</div>`;
  toolLog.appendChild(item);
  toolLog.scrollTop = toolLog.scrollHeight;
}

function addMemoryItem(container, record) {
  const item = document.createElement("div");
  item.className = "memory-item";
  item.innerHTML = `
    <span>${record.scope || "memory"} · ${record.kind || "context"}</span>
    <strong>${record.text}</strong>
  `;
  container.appendChild(item);
  container.scrollTop = container.scrollHeight;
}

function resetMemoryUsed() {
  memoryUsed.innerHTML = "";
}

function appendChat(speaker, message) {
  const paragraph = document.createElement("p");
  paragraph.innerHTML = `<strong>${speaker}:</strong> ${message}`;
  chatOutput.appendChild(paragraph);
  chatOutput.scrollTop = chatOutput.scrollHeight;
}

function beginStreamMessage() {
  streamingMessage = document.createElement("p");
  streamingText = document.createElement("span");
  streamingMessage.innerHTML = "<strong>Victus:</strong> ";
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

async function sendChat() {
  const message = chatInput.value.trim();
  if (!message) {
    return;
  }
  resetMemoryUsed();
  chatSend.disabled = true;
  appendChat("You", message);
  chatInput.value = "";
  addTimelineEntry("turn_start", message);

  try {
    const response = await fetch("/api/turn", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    if (!response.ok) {
      const payload = await response.json();
      appendChat("Victus", payload.detail || "Error retrieving response.");
      endStreamMessage();
      return;
    }
    await readTurnStream(response);
  } catch (error) {
    appendChat("Victus", "Network error while contacting server.");
    endStreamMessage();
  } finally {
    chatSend.disabled = false;
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
    const segments = buffer.split("\n\n");
    buffer = segments.pop();
    segments.forEach((segment) => {
      const dataLine = segment
        .split("\n")
        .find((line) => line.startsWith("data: "));
      if (!dataLine) {
        return;
      }
      const payload = JSON.parse(dataLine.replace("data: ", ""));
      handleTurnEvent(payload);
    });
  }

  if (buffer.trim()) {
    const dataLine = buffer
      .split("\n")
      .find((line) => line.startsWith("data: "));
    if (dataLine) {
      const payload = JSON.parse(dataLine.replace("data: ", ""));
      handleTurnEvent(payload);
    }
  }
}

function handleTurnEvent(payload) {
  if (payload.event === "status") {
    updateStatus(payload.status);
    addTimelineEntry("status", payload.status || "");
    return;
  }
  if (payload.event === "token") {
    appendStreamChunk(payload.token);
    return;
  }
  if (payload.event === "tool_start") {
    addToolEntry(
      `${payload.tool}.${payload.action}`,
      `args: ${JSON.stringify(payload.args || {})}`
    );
    addTimelineEntry("tool_start", `${payload.tool}.${payload.action}`);
    return;
  }
  if (payload.event === "tool_done") {
    addToolEntry(
      `${payload.tool}.${payload.action} complete`,
      JSON.stringify(payload.result || {})
    );
    addTimelineEntry("tool_done", `${payload.tool}.${payload.action}`);
    appendChat("Victus", formatToolResult(payload));
    return;
  }
  if (payload.event === "memory_used") {
    const items = payload.result?.items || [];
    items.forEach((record) => addMemoryItem(memoryUsed, record));
    addTimelineEntry("memory_used", `${payload.result?.count || 0} memories`);
    return;
  }
  if (payload.event === "memory_written") {
    if (payload.result) {
      addMemoryItem(memoryRecent, payload.result);
    }
    addTimelineEntry("memory_written", payload.result?.text || "");
    return;
  }
  if (payload.event === "clarify") {
    appendChat("Victus", payload.message || "Can you clarify?");
    endStreamMessage();
    return;
  }
  if (payload.event === "error") {
    appendChat("Victus", payload.message || "Request failed.");
    addTimelineEntry("error", payload.message || "");
    endStreamMessage();
  }
}

function updateStatus(status) {
  if (status === "thinking") {
    setStatus("Thinking…", "busy");
    return;
  }
  if (status === "executing") {
    setStatus("Executing…", "busy");
    return;
  }
  if (status === "done") {
    setStatus("Connected", "connected");
    endStreamMessage();
    refreshMemoryRecent();
    refreshFinanceSummary();
    return;
  }
  if (status === "denied") {
    setStatus("Denied", "denied");
    endStreamMessage();
    return;
  }
  if (status === "error") {
    setStatus("Error", "error");
    endStreamMessage();
    return;
  }
}

function formatToolResult(payload) {
  if (payload?.result?.opened) {
    return `Task complete: opened ${payload.result.opened}.`;
  }
  if (payload?.result) {
    return `Task complete: ${JSON.stringify(payload.result)}.`;
  }
  return "Task complete.";
}

function connectLogsStream() {
  const source = new EventSource("/api/logs/stream");
  source.onmessage = (event) => {
    const entry = JSON.parse(event.data);
    if (entry.event === "status_update") {
      updateStatus(entry.data.status);
    }
    addTimelineEntry(entry.event, JSON.stringify(entry.data || {}));
  };
  source.onerror = () => {
    setStatus("Disconnected", "");
  };
}

function setActiveTab(tabName) {
  document.querySelectorAll(".tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === tabName);
  });
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.panel === tabName);
  });
}

async function refreshMemoryRecent() {
  const response = await fetch("/api/memory/recent?limit=6");
  if (!response.ok) {
    return;
  }
  const payload = await response.json();
  memoryRecent.innerHTML = "";
  payload.items.forEach((record) => addMemoryItem(memoryRecent, record));
}

async function refreshFinanceSummary() {
  const response = await fetch("/api/finance/summary");
  if (!response.ok) {
    return;
  }
  const summary = await response.json();
  financeSummary.innerHTML = `
    <strong>${summary.month}</strong>
    <ul>
      <li>Total income: ${summary.total_income}</li>
      <li>Total expense: ${summary.total_expense}</li>
      <li>Net: ${summary.net}</li>
      <li>Transactions: ${summary.count}</li>
    </ul>
  `;
}

async function handleFinanceSubmit(event) {
  event.preventDefault();
  const formData = new FormData(financeForm);
  const payload = Object.fromEntries(formData.entries());
  payload.amount = parseFloat(payload.amount);
  const response = await fetch("/api/finance/transaction", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    financePreview.textContent = "Unable to save transaction.";
    return;
  }
  const result = await response.json();
  financePreview.textContent = `Saved: ${result.preview}`;
  financeForm.reset();
  refreshFinanceSummary();
}

async function handleFinanceExport() {
  const response = await fetch("/api/finance/export?range=month");
  if (!response.ok) {
    financeExportOutput.textContent = "Export failed.";
    return;
  }
  const payload = await response.json();
  financeExportOutput.textContent = payload.markdown || "";
}

chatSend.addEventListener("click", sendChat);
chatInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendChat();
  }
});

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => setActiveTab(button.dataset.tab));
});

financeForm.addEventListener("submit", handleFinanceSubmit);
financeExport.addEventListener("click", handleFinanceExport);

connectLogsStream();
refreshMemoryRecent();
refreshFinanceSummary();

"use strict";

const API_URL = "http://127.0.0.1:5000/api/tasks";
const statusLabels = {
  todo: "To do",
  in_progress: "In progress",
  done: "Completed"
};

const taskList = document.querySelector("#task-list");
const taskForm = document.querySelector("#task-form");
const statusFilter = document.querySelector("#status-filter");
const notice = document.querySelector("#notice");
let tasks = [];
let noticeTimeout;

document.querySelector("#today-date").textContent = new Intl.DateTimeFormat(undefined, {
  weekday: "short",
  month: "short",
  day: "numeric",
  year: "numeric"
}).format(new Date());

function showNotice(message, type) {
  window.clearTimeout(noticeTimeout);
  notice.textContent = message;
  notice.className = `notice ${type}`;
  notice.hidden = false;
  noticeTimeout = window.setTimeout(() => {
    notice.hidden = true;
  }, 4500);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[character]);
}

function updateSummary() {
  document.querySelector("#total-count").textContent =
    tasks.filter((task) => task.status === "todo").length;
  document.querySelector("#progress-count").textContent =
    tasks.filter((task) => task.status === "in_progress").length;
  document.querySelector("#done-count").textContent =
    tasks.filter((task) => task.status === "done").length;
}

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Date unavailable";
  return `Created ${new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(date)}`;
}

function renderTasks() {
  const filter = statusFilter.value;
  const visibleTasks = filter === "all" ? tasks : tasks.filter((task) => task.status === filter);
  updateSummary();

  if (visibleTasks.length === 0) {
    const message = tasks.length === 0
      ? "No tasks yet. Add your first task below and get started."
      : `No ${statusLabels[filter].toLowerCase()} tasks. Try another filter.`;
    taskList.innerHTML = `<div class="state-message"><span class="empty-icon" aria-hidden="true">✦</span><span>${escapeHtml(message)}</span></div>`;
    return;
  }

  taskList.innerHTML = visibleTasks.map((task) => `
    <article class="task-row" data-task-id="${task.id}">
      <div class="task-main">
        <h3 class="task-title">${escapeHtml(task.title)}</h3>
        ${task.description ? `<p class="task-description">${escapeHtml(task.description)}</p>` : ""}
        <div class="task-created">${escapeHtml(formatDate(task.created_at))}</div>
      </div>
      <label>
        <span class="visually-hidden">Status for ${escapeHtml(task.title)}</span>
        <select class="task-status" data-action="status" aria-label="Status for ${escapeHtml(task.title)}">
          ${Object.entries(statusLabels).map(([value, label]) =>
            `<option value="${value}" ${task.status === value ? "selected" : ""}>${label}</option>`
          ).join("")}
        </select>
      </label>
      <button class="delete-button" type="button" data-action="delete" aria-label="Delete ${escapeHtml(task.title)}">Delete&nbsp; ×</button>
    </article>
  `).join("");
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers
    }
  });
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("The server returned an unreadable response.");
  }
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status}).`);
  return data;
}

async function loadTasks() {
  taskList.innerHTML = '<div class="state-message"><span class="spinner" aria-hidden="true"></span><span>Loading your tasks…</span></div>';
  try {
    const data = await requestJson(API_URL);
    tasks = data.tasks;
    renderTasks();
  } catch (error) {
    taskList.innerHTML = `<div class="state-message">${escapeHtml(error.message)} Check that the backend is running, then refresh.</div>`;
    showNotice(error.message, "error");
  }
}

taskForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submitButton = taskForm.querySelector('button[type="submit"]');
  const titleInput = document.querySelector("#task-title");
  const descriptionInput = document.querySelector("#task-description");
  const title = titleInput.value.trim();
  if (!title) {
    titleInput.setCustomValidity("Please enter a task title.");
    titleInput.reportValidity();
    titleInput.setCustomValidity("");
    return;
  }

  submitButton.disabled = true;
  try {
    const data = await requestJson(`${API_URL}/create`, {
      method: "POST",
      body: JSON.stringify({ title, description: descriptionInput.value.trim() })
    });
    tasks.unshift(data.task);
    taskForm.reset();
    statusFilter.value = "all";
    renderTasks();
    showNotice("Task created successfully.", "success");
  } catch (error) {
    showNotice(error.message, "error");
  } finally {
    submitButton.disabled = false;
  }
});

taskList.addEventListener("change", async (event) => {
  const control = event.target.closest('[data-action="status"]');
  if (!control) return;
  const row = control.closest("[data-task-id]");
  const task = tasks.find((item) => item.id === Number(row.dataset.taskId));
  if (!task) return;

  const previousStatus = task.status;
  control.disabled = true;
  try {
    const data = await requestJson(`${API_URL}/${task.id}`, {
      method: "PUT",
      body: JSON.stringify({ status: control.value })
    });
    Object.assign(task, data.task);
    renderTasks();
    showNotice("Task status updated.", "success");
  } catch (error) {
    control.value = previousStatus;
    showNotice(error.message, "error");
  } finally {
    control.disabled = false;
  }
});

taskList.addEventListener("click", async (event) => {
  const button = event.target.closest('[data-action="delete"]');
  if (!button) return;
  const row = button.closest("[data-task-id]");
  const taskId = Number(row.dataset.taskId);
  const task = tasks.find((item) => item.id === taskId);
  if (!task || !window.confirm(`Delete "${task.title}"? This cannot be undone.`)) return;

  button.disabled = true;
  try {
    await requestJson(`${API_URL}/${taskId}`, { method: "DELETE" });
    tasks = tasks.filter((item) => item.id !== taskId);
    renderTasks();
    showNotice("Task deleted.", "success");
  } catch (error) {
    button.disabled = false;
    showNotice(error.message, "error");
  }
});

statusFilter.addEventListener("change", renderTasks);
loadTasks();

const STORAGE_KEY = "taskflow_frontend_state";

const defaultState = {
  user: {
    name: "Guest User",
    email: "guest@example.com",
    reminderPreference: "Daily summary",
    premiumStatus: "Free Plan",
  },
  tasks: [],
  notes: [],
  files: [],
};

let state = structuredClone(defaultState);

function loadState() {
  const saved = localStorage.getItem(STORAGE_KEY);

  if (!saved) {
    return structuredClone(defaultState);
  }

  try {
    const parsed = JSON.parse(saved);
    return {
      ...structuredClone(defaultState),
      ...parsed,
      user: {
        ...structuredClone(defaultState).user,
        ...(parsed.user || {}),
      },
      tasks: Array.isArray(parsed.tasks) ? parsed.tasks : [],
      notes: Array.isArray(parsed.notes) ? parsed.notes : [],
      files: Array.isArray(parsed.files) ? parsed.files : [],
    };
  } catch (error) {
    console.error("Could not load app state.", error);
    return structuredClone(defaultState);
  }
}

function saveState() {
  if (syncOn()) {
    try {
      localStorage.setItem(
        STORAGE_KEY + "_prefs",
        JSON.stringify({ user: { reminderPreference: state.user.reminderPreference } }),
      );
    } catch (_) {}
    return;
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function syncOn() {
  return document.body?.dataset?.sync === "true";
}

function apiHeaders() {
  const h = { "Content-Type": "application/json" };
  const t = document.body?.dataset?.csrf;
  if (t) {
    h["X-CSRFToken"] = t;
  }
  return h;
}

function apiJson(method, url, body) {
  const o = { method, headers: apiHeaders(), credentials: "same-origin" };
  if (body !== undefined) {
    o.body = JSON.stringify(body);
  }
  return fetch(url, o);
}

async function pullState() {
  const r = await fetch("/api/state", { credentials: "same-origin" });
  if (!r.ok) {
    return;
  }
  const d = await r.json();
  state.tasks = d.tasks || [];
  state.notes = d.notes || [];
  state.files = d.files || [];
  const rem = state.user.reminderPreference;
  state.user = { ...state.user, ...(d.user || {}), reminderPreference: rem };
}

function createId() {
  return crypto.randomUUID();
}

function formatDate(dateString) {
  if (!dateString) {
    return "No date";
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(`${dateString}T00:00:00`));
}

function formatDateTime(dateString) {
  if (!dateString) {
    return "—";
  }
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(dateString));
}

function formatFileSize(size) {
  if (size < 1024) {
    return `${size} B`;
  }

  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }

  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function offsetDate(days) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().split("T")[0];
}

function isDueSoon(dateString) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const dueDate = new Date(`${dateString}T00:00:00`);
  const days = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24));
  return days >= 0 && days <= 3;
}

function isOverdue(dateString) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return new Date(`${dateString}T00:00:00`) < today;
}

function priorityLabel(task) {
  if (isOverdue(task.dueDate)) {
    return { text: "Overdue", className: "warning" };
  }

  if (isDueSoon(task.dueDate)) {
    return { text: "Due Soon", className: "" };
  }

  return { text: "On Track", className: "success" };
}

function sortTasks(tasks) {
  return [...tasks].sort((a, b) => new Date(a.dueDate) - new Date(b.dueDate));
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => {
    const replacements = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    };
    return replacements[character];
  });
}

function ensureDemoData() {
  if (syncOn()) {
    return;
  }
  if (state.tasks.length || state.notes.length || state.files.length) {
    return;
  }

  const firstTaskId = createId();
  const secondTaskId = createId();
  const noteId = createId();
  const fileId = createId();

  state.user = {
    ...state.user,
    name: "Alex Student",
    email: "alex@example.com",
  };

  state.tasks = [
    {
      id: firstTaskId,
      name: "Finish project slides",
      dueDate: offsetDate(1),
      tag: "School",
      reminder: "Daily",
      description: "Wrap up the presentation and review speaker notes.",
      completed: false,
      createdAt: new Date().toISOString(),
    },
    {
      id: secondTaskId,
      name: "Submit weekly report",
      dueDate: offsetDate(3),
      tag: "Work",
      reminder: "Weekly",
      description: "Send a short progress update before Friday afternoon.",
      completed: false,
      createdAt: new Date().toISOString(),
    },
  ];

  state.notes = [
    {
      id: noteId,
      title: "Presentation ideas",
      contents: "Talk about task tracking, notes, reminders, and simple design.",
      taskId: firstTaskId,
      createdAt: new Date().toISOString(),
      fileIds: [fileId],
    },
  ];

  state.files = [
    {
      id: fileId,
      name: "outline.pdf",
      sizeLabel: "1.1 MB",
      type: "PDF",
      taskId: firstTaskId,
      noteId,
      createdAt: new Date().toISOString(),
    },
  ];

  saveState();
}

function fillTaskSelect(select) {
  if (!select) {
    return;
  }

  const currentValue = select.value;
  select.innerHTML = `<option value="">No linked task</option>`;

  sortTasks(state.tasks).forEach((task) => {
    const option = document.createElement("option");
    option.value = task.id;
    option.textContent = task.name;
    if (currentValue === task.id) {
      option.selected = true;
    }
    select.append(option);
  });
}

function fillLinkSelects() {
  fillTaskSelect(document.querySelector("#noteTaskLink"));
  fillTaskSelect(document.querySelector("#fileTaskLink"));
  fillNoteSelect();
}

function fillNoteSelect() {
  const select = document.querySelector("#fileNoteLink");
  if (!select) {
    return;
  }

  const currentValue = select.value;
  select.innerHTML = `<option value="">No linked note</option>`;

  state.notes.forEach((note) => {
    const option = document.createElement("option");
    option.value = note.id;
    option.textContent = note.title;
    if (currentValue === note.id) {
      option.selected = true;
    }
    select.append(option);
  });
}

function renderPreview() {
  const container = document.querySelector("#homePreviewList");
  if (!container) {
    return;
  }

  const tasks = sortTasks(state.tasks).slice(0, 3);
  container.innerHTML = "";

  if (!tasks.length) {
    container.innerHTML = `<div class="empty-state">Use the dashboard or tasks page to add your first to-do item.</div>`;
    return;
  }

  tasks.forEach((task) => {
    const badge = priorityLabel(task);
    const item = document.createElement("div");
    item.className = "list-item";
    item.innerHTML = `
      <div class="mini-head">
        <div>
          <strong>${escapeHtml(task.name)}</strong>
          <div class="list-meta">${formatDate(task.dueDate)} • ${escapeHtml(task.reminder)}</div>
        </div>
        <span class="badge ${badge.className}">${badge.text}</span>
      </div>
    `;
    container.append(item);
  });
}

function renderHomeTasks() {
  const container = document.querySelector("#homeTasksList");
  if (!container) {
    return;
  }

  const tasks = sortTasks(state.tasks).slice(0, 4);
  container.innerHTML = "";

  if (!tasks.length) {
    container.innerHTML = `<div class="empty-state">No tasks yet.</div>`;
    return;
  }

  tasks.forEach((task) => {
    const badge = priorityLabel(task);
    const item = document.createElement("div");
    item.className = "list-item";
    item.innerHTML = `
      <div class="mini-head">
        <div>
          <strong>${escapeHtml(task.name)}</strong>
          <div class="list-meta">${formatDate(task.dueDate)} • ${escapeHtml(task.tag || "General")}</div>
        </div>
        <span class="badge ${badge.className}">${badge.text}</span>
      </div>
    `;
    container.append(item);
  });
}

function renderHomeNotes() {
  const container = document.querySelector("#homeNotesList");
  if (!container) {
    return;
  }

  const notes = [...state.notes]
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    .slice(0, 3);

  container.innerHTML = "";

  if (!notes.length) {
    container.innerHTML = `<div class="empty-state">No notes yet.</div>`;
    return;
  }

  notes.forEach((note) => {
    const linkedTask = state.tasks.find((task) => task.id === note.taskId);
    const item = document.createElement("div");
    item.className = "list-item";
    item.innerHTML = `
      <strong>${escapeHtml(note.title)}</strong>
      <div class="list-meta">${linkedTask ? `Linked to ${escapeHtml(linkedTask.name)}` : "No linked task"}</div>
      <div class="list-meta">${formatDateTime(note.createdAt)}</div>
    `;
    container.append(item);
  });
}

function renderHomeFiles() {
  const container = document.querySelector("#homeFilesList");
  if (!container) {
    return;
  }

  const files = [...state.files]
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    .slice(0, 4);

  container.innerHTML = "";

  if (!files.length) {
    container.innerHTML = `<div class="empty-state">No files yet.</div>`;
    return;
  }

  files.forEach((file) => {
    const task = state.tasks.find((item) => item.id === file.taskId);
    const note = state.notes.find((item) => item.id === file.noteId);
    const card = document.createElement("article");
    card.className = "upload-card";
    card.innerHTML = `
      <div class="upload-head">
        <div>
          <strong>${escapeHtml(file.name)}</strong>
          <div class="list-meta">${escapeHtml(file.type)} • ${escapeHtml(file.sizeLabel)}</div>
          <div class="list-meta">
            ${task ? `Task: ${escapeHtml(task.name)}` : "No task linked"}${note ? ` • Note: ${escapeHtml(note.title)}` : ""}
          </div>
        </div>
      </div>
    `;
    container.append(card);
  });
}

function renderStats() {
  const totalTasks = document.querySelector("#totalTasks");
  const dueSoonTasks = document.querySelector("#dueSoonTasks");
  const completedTasks = document.querySelector("#completedTasks");
  const totalNotes = document.querySelector("#totalNotes");

  if (!totalTasks || !dueSoonTasks || !completedTasks || !totalNotes) {
    return;
  }

  totalTasks.textContent = String(state.tasks.length);
  dueSoonTasks.textContent = String(state.tasks.filter((task) => !task.completed && isDueSoon(task.dueDate)).length);
  completedTasks.textContent = String(state.tasks.filter((task) => task.completed).length);
  totalNotes.textContent = String(state.notes.length);
}

function renderPriorityList() {
  const container = document.querySelector("#priorityList");
  if (!container) {
    return;
  }

  const tasks = sortTasks(state.tasks).filter((task) => !task.completed);
  container.innerHTML = "";

  if (!tasks.length) {
    container.innerHTML = `<div class="empty-state">Priority items will appear here after you add tasks.</div>`;
    return;
  }

  tasks.slice(0, 5).forEach((task) => {
    const badge = priorityLabel(task);
    const item = document.createElement("div");
    item.className = "list-item";
    item.innerHTML = `
      <div class="mini-head">
        <div>
          <strong>${escapeHtml(task.name)}</strong>
          <div class="list-meta">${formatDate(task.dueDate)} • ${escapeHtml(task.tag || "General")}</div>
        </div>
        <span class="badge ${badge.className}">${badge.text}</span>
      </div>
    `;
    container.append(item);
  });
}

function renderReminderList() {
  const container = document.querySelector("#reminderList");
  if (!container) {
    return;
  }

  const tasks = sortTasks(state.tasks).filter((task) => !task.completed);
  container.innerHTML = "";

  if (!tasks.length) {
    container.innerHTML = `<div class="empty-state">Reminder previews will appear here.</div>`;
    return;
  }

  tasks.slice(0, 4).forEach((task) => {
    const item = document.createElement("div");
    item.className = "list-item";
    item.innerHTML = `
      <strong>${escapeHtml(task.name)}</strong>
      <div class="list-meta">${escapeHtml(task.reminder)} reminder • Due ${formatDate(task.dueDate)}</div>
    `;
    container.append(item);
  });
}

function renderWelcome() {
  const nameTarget = document.querySelector("[data-user-name]");
  const emailTarget = document.querySelector("[data-user-email]");

  if (nameTarget) {
    nameTarget.textContent = state.user.name;
  }

  if (emailTarget) {
    emailTarget.textContent = state.user.email;
  }
}

function renderTasks() {
  const container = document.querySelector("#taskList");
  if (!container) {
    return;
  }

  const filter = document.querySelector("#taskFilter")?.value || "all";
  let tasks = [...state.tasks];

  if (filter === "active") {
    tasks = tasks.filter((task) => !task.completed);
  } else if (filter === "completed") {
    tasks = tasks.filter((task) => task.completed);
  } else if (filter === "dueSoon") {
    tasks = tasks.filter((task) => !task.completed && isDueSoon(task.dueDate));
  }

  tasks = sortTasks(tasks);
  container.innerHTML = "";

  if (!tasks.length) {
    container.innerHTML = `<div class="empty-state">No tasks match this filter yet.</div>`;
    return;
  }

  tasks.forEach((task) => {
    const badge = priorityLabel(task);
    const tid = String(task.id);
    const titleHtml = /^\d+$/.test(tid)
      ? `<a href="/tasks/${tid}">${escapeHtml(task.name)}</a>`
      : escapeHtml(task.name);
    const card = document.createElement("article");
    card.className = `task-card${task.completed ? " completed" : ""}`;
    card.innerHTML = `
      <div class="task-head">
        <div>
          <h3 class="task-title">${titleHtml}</h3>
          <div class="inline-actions">
            <span class="tag">${escapeHtml(task.tag || "General")}</span>
            <span class="badge ${badge.className}">${badge.text}</span>
          </div>
        </div>
        <div class="list-meta">Due ${formatDate(task.dueDate)} • ${escapeHtml(task.reminder)}</div>
      </div>
      <p class="task-text">${escapeHtml(task.description || "No description yet.")}</p>
      <div class="task-actions">
        <button class="secondary-button" type="button" data-toggle-task="${task.id}">Mark ${task.completed ? "Active" : "Complete"}</button>
        <button class="ghost-button" type="button" data-delete-task="${task.id}">Delete</button>
      </div>
    `;
    container.append(card);
  });
}

function renderNotes() {
  const container = document.querySelector("#notesList");
  if (!container) {
    return;
  }

  container.innerHTML = "";

  if (!state.notes.length) {
    container.innerHTML = `<div class="empty-state">Notes you save will show up here.</div>`;
    return;
  }

  [...state.notes]
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    .forEach((note) => {
      const linkedTask = state.tasks.find((task) => task.id === note.taskId);
      const fileNames = state.files.filter((file) => (note.fileIds || []).includes(file.id));
      const nid = String(note.id);
      const titleHtml = /^\d+$/.test(nid)
        ? `<a href="/notes/${nid}">${escapeHtml(note.title)}</a>`
        : escapeHtml(note.title);
      const card = document.createElement("article");
      card.className = "note-card";
      card.innerHTML = `
        <div class="note-head">
          <div>
            <h3 class="note-title">${titleHtml}</h3>
            <div class="list-meta">${linkedTask ? `Linked to ${escapeHtml(linkedTask.name)}` : "No linked task"}</div>
          </div>
          <div class="list-meta">${formatDateTime(note.createdAt)}</div>
        </div>
        <p class="note-text">${escapeHtml(note.contents)}</p>
        <div class="file-chips">
          ${
            fileNames.length
              ? fileNames.map((file) => `<span class="chip">${escapeHtml(file.name)}</span>`).join("")
              : `<span class="chip">No attached files</span>`
          }
        </div>
      `;
      container.append(card);
    });
}

function renderFiles() {
  const container = document.querySelector("#uploadsList");
  if (!container) {
    return;
  }

  container.innerHTML = "";

  if (!state.files.length) {
    container.innerHTML = `<div class="empty-state">Uploaded files will appear here.</div>`;
    return;
  }

  state.files.forEach((file) => {
    const task = state.tasks.find((item) => item.id === file.taskId);
    const note = state.notes.find((item) => item.id === file.noteId);
    const card = document.createElement("article");
    card.className = "upload-card";
    card.innerHTML = `
      <div class="upload-head">
        <div>
          <strong>${escapeHtml(file.name)}</strong>
          <div class="list-meta">${escapeHtml(file.type)} • ${escapeHtml(file.sizeLabel)}</div>
          <div class="list-meta">
            ${task ? `Task: ${escapeHtml(task.name)}` : "No task linked"}${note ? ` • Note: ${escapeHtml(note.title)}` : ""}
          </div>
        </div>
        <div class="upload-actions">
          <button class="secondary-button" type="button" data-download-file="${file.id}">Download</button>
          <button class="ghost-button" type="button" data-delete-file="${file.id}">Remove</button>
        </div>
      </div>
    `;
    container.append(card);
  });
}

function renderProfile() {
  const nameInput = document.querySelector("#profileName");
  const emailInput = document.querySelector("#profileEmail");
  const reminderSelect = document.querySelector("#profileReminderPreference");
  const statusTarget = document.querySelector("#profileStatus");

  if (nameInput) {
    nameInput.value = state.user.name;
  }

  if (emailInput) {
    emailInput.value = state.user.email;
  }

  if (reminderSelect) {
    reminderSelect.value = state.user.reminderPreference;
  }

  if (statusTarget) {
    statusTarget.textContent = state.user.premiumStatus;
  }
}

function showSelectedFiles() {
  const preview = document.querySelector("#filePreview");
  const input = document.querySelector("#noteFiles");
  if (!preview || !input) {
    return;
  }

  const files = Array.from(input.files || []);
  preview.innerHTML = files.length
    ? files.map((file) => `<span class="chip">${escapeHtml(file.name)} (${formatFileSize(file.size)})</span>`).join("")
    : "";
}

async function addTask(form) {
  const formData = new FormData(form);
  if (syncOn()) {
    const r = await apiJson("POST", "/api/task", {
      name: formData.get("taskName").trim(),
      dueDate: formData.get("taskDueDate"),
      tag: formData.get("taskTag").trim(),
      reminder: formData.get("taskReminder"),
      completed: false,
    });
    if (!r.ok) {
      return;
    }
    await pullState();
  } else {
    state.tasks.push({
      id: createId(),
      name: formData.get("taskName").trim(),
      dueDate: formData.get("taskDueDate"),
      tag: formData.get("taskTag").trim(),
      reminder: formData.get("taskReminder"),
      description: formData.get("taskDescription").trim(),
      completed: false,
      createdAt: new Date().toISOString(),
    });
    saveState();
  }
  renderTasks();
  renderStats();
  renderPriorityList();
  renderReminderList();
  renderPreview();
  renderHomeTasks();
  fillLinkSelects();
}

async function addNote(form) {
  const formData = new FormData(form);
  const files = Array.from(document.querySelector("#noteFiles")?.files || []);
  const taskLink = formData.get("noteTaskLink") || "";

  if (syncOn()) {
    const r = await apiJson("POST", "/api/note", {
      title: formData.get("noteTitle").trim(),
      contents: formData.get("noteContents").trim(),
      task_id: taskLink || null,
    });
    if (!r.ok) {
      return;
    }
    const created = await r.json();
    const nid = created.id;
    if (nid != null && files.length) {
      for (const file of files) {
        const fr = await apiJson("POST", "/api/file", {
          link: file.name,
          local_file_address: "",
          task_id: taskLink || null,
          note_id: nid,
        });
        if (!fr.ok) {
          return;
        }
      }
    }
    await pullState();
  } else {
    const noteId = createId();
    const fileIds = [];
    files.forEach((file) => {
      const fileId = createId();
      fileIds.push(fileId);
      state.files.push({
        id: fileId,
        name: file.name,
        sizeLabel: formatFileSize(file.size),
        type: file.type || "File",
        taskId: taskLink,
        noteId,
        createdAt: new Date().toISOString(),
      });
    });
    state.notes.push({
      id: noteId,
      title: formData.get("noteTitle").trim(),
      contents: formData.get("noteContents").trim(),
      taskId: taskLink,
      createdAt: new Date().toISOString(),
      fileIds,
    });
    saveState();
  }
  renderNotes();
  renderFiles();
  renderStats();
  renderHomeNotes();
  renderHomeFiles();
  fillLinkSelects();
  showSelectedFiles();
}

async function addFile(form) {
  const formData = new FormData(form);
  const pickedFiles = Array.from(document.querySelector("#uploadFiles")?.files || []);
  const taskId = formData.get("fileTaskLink") || "";
  const noteId = formData.get("fileNoteLink") || "";

  if (syncOn()) {
    for (const file of pickedFiles) {
      const r = await apiJson("POST", "/api/file", {
        link: file.name,
        local_file_address: "",
        task_id: taskId || null,
        note_id: noteId || null,
      });
      if (!r.ok) {
        return;
      }
    }
    await pullState();
  } else {
    pickedFiles.forEach((file) => {
      state.files.push({
        id: createId(),
        name: file.name,
        sizeLabel: formatFileSize(file.size),
        type: file.type || "File",
        taskId,
        noteId,
        createdAt: new Date().toISOString(),
      });
    });
    saveState();
  }
  renderFiles();
  renderNotes();
  renderHomeFiles();
  renderHomeNotes();
}

async function toggleTask(taskId) {
  const cur = state.tasks.find((t) => t.id === taskId);
  if (!cur) {
    return;
  }
  if (syncOn()) {
    const r = await apiJson("PUT", `/api/task/${taskId}`, { completed: !cur.completed });
    if (!r.ok) {
      return;
    }
    await pullState();
  } else {
    state.tasks = state.tasks.map((task) =>
      task.id === taskId ? { ...task, completed: !task.completed } : task,
    );
    saveState();
  }
  renderTasks();
  renderStats();
  renderPriorityList();
  renderReminderList();
  renderPreview();
  renderHomeTasks();
}

async function deleteTask(taskId) {
  if (syncOn()) {
    const r = await apiJson("DELETE", `/api/task/${taskId}`);
    if (!r.ok) {
      return;
    }
    await pullState();
  } else {
    state.tasks = state.tasks.filter((task) => task.id !== taskId);
    state.notes = state.notes.map((note) =>
      note.taskId === taskId ? { ...note, taskId: "" } : note,
    );
    state.files = state.files.map((file) =>
      file.taskId === taskId ? { ...file, taskId: "" } : file,
    );
    saveState();
  }
  renderTasks();
  renderNotes();
  renderFiles();
  renderStats();
  renderPriorityList();
  renderReminderList();
  renderPreview();
  renderHomeTasks();
  renderHomeNotes();
  renderHomeFiles();
  fillLinkSelects();
}

async function deleteFile(fileId) {
  if (syncOn()) {
    const r = await apiJson("DELETE", `/api/file/${fileId}`);
    if (!r.ok) {
      return;
    }
    await pullState();
  } else {
    state.files = state.files.filter((file) => file.id !== fileId);
    state.notes = state.notes.map((note) => ({
      ...note,
      fileIds: (note.fileIds || []).filter((id) => id !== fileId),
    }));
    saveState();
  }
  renderFiles();
  renderNotes();
  renderHomeFiles();
  renderHomeNotes();
}

async function saveProfile(form) {
  const formData = new FormData(form);
  const rem = formData.get("profileReminderPreference");
  if (syncOn()) {
    const r = await apiJson("POST", "/api/profile", {
      name: formData.get("profileName").toString().trim(),
      email: formData.get("profileEmail").toString().trim(),
      password: formData.get("profilePassword")?.toString().trim() || "",
    });
    if (r.ok) {
      await pullState();
    }
    state.user.reminderPreference = rem?.toString() || state.user.reminderPreference;
    saveState();
  } else {
    state.user = {
      ...state.user,
      name: formData.get("profileName").trim(),
      email: formData.get("profileEmail").trim(),
      reminderPreference: rem,
    };
    saveState();
  }
  renderWelcome();
  renderProfile();
}

function handleDownload() {
  window.alert("This is a frontend-only demo. Real file downloads can be added later.");
}

function setupHomePage() {
  const demoButton = document.querySelector("#loadDemoButton");
  if (demoButton) {
    demoButton.addEventListener("click", () => {
      ensureDemoData();
      renderPreview();
    });
  }
}

function setupAuthPages() {
  /* login/signup handled server-side (Flask-WTF + Flask-Login) */
}

function setupDashboardPage() {
  /* logout is a normal link to /logout */
}

function setupTasksPage() {
  const taskForm = document.querySelector("#taskForm");
  const filter = document.querySelector("#taskFilter");
  const taskFormCard = document.querySelector("#taskFormCard");
  const showTaskFormButton = document.querySelector("#showTaskFormButton");
  const hideTaskFormButton = document.querySelector("#hideTaskFormButton");
  const taskFormCancelButton = document.querySelector("#taskFormCancelButton");

  function openTaskForm() {
    if (taskFormCard) {
      taskFormCard.hidden = false;
    }
  }

  function closeTaskForm() {
    if (taskFormCard) {
      taskFormCard.hidden = true;
    }
  }

  if (showTaskFormButton) {
    showTaskFormButton.addEventListener("click", openTaskForm);
  }

  if (hideTaskFormButton) {
    hideTaskFormButton.addEventListener("click", closeTaskForm);
  }

  if (taskFormCancelButton) {
    taskFormCancelButton.addEventListener("click", closeTaskForm);
  }

  if (taskForm) {
    taskForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      await addTask(taskForm);
      taskForm.reset();
      closeTaskForm();
    });
  }

  if (filter) {
    filter.addEventListener("change", renderTasks);
  }

  document.addEventListener("click", (event) => {
    const toggleButton = event.target.closest("[data-toggle-task]");
    const deleteButton = event.target.closest("[data-delete-task]");

    if (toggleButton) {
      void toggleTask(toggleButton.dataset.toggleTask);
    }

    if (deleteButton) {
      void deleteTask(deleteButton.dataset.deleteTask);
    }
  });
}

function setupNotesPage() {
  const noteForm = document.querySelector("#noteForm");
  const noteFiles = document.querySelector("#noteFiles");
  const noteFormCard = document.querySelector("#noteFormCard");
  const showNoteFormButton = document.querySelector("#showNoteFormButton");
  const hideNoteFormButton = document.querySelector("#hideNoteFormButton");
  const noteFormCancelButton = document.querySelector("#noteFormCancelButton");

  function openNoteForm() {
    if (noteFormCard) {
      noteFormCard.hidden = false;
    }
  }

  function closeNoteForm() {
    if (noteFormCard) {
      noteFormCard.hidden = true;
    }

    const preview = document.querySelector("#filePreview");
    if (preview) {
      preview.innerHTML = "";
    }
  }

  if (showNoteFormButton) {
    showNoteFormButton.addEventListener("click", openNoteForm);
  }

  if (hideNoteFormButton) {
    hideNoteFormButton.addEventListener("click", closeNoteForm);
  }

  if (noteFormCancelButton) {
    noteFormCancelButton.addEventListener("click", closeNoteForm);
  }

  if (noteForm) {
    noteForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      await addNote(noteForm);
      noteForm.reset();
      document.querySelector("#filePreview").innerHTML = "";
      fillLinkSelects();
      closeNoteForm();
    });
  }

  if (noteFiles) {
    noteFiles.addEventListener("change", showSelectedFiles);
  }
}

function setupFilesPage() {
  const fileForm = document.querySelector("#fileForm");
  const fileFormCard = document.querySelector("#fileFormCard");
  const showFileFormButton = document.querySelector("#showFileFormButton");
  const hideFileFormButton = document.querySelector("#hideFileFormButton");
  const fileFormCancelButton = document.querySelector("#fileFormCancelButton");

  function openFileForm() {
    if (fileFormCard) {
      fileFormCard.hidden = false;
    }
  }

  function closeFileForm() {
    if (fileFormCard) {
      fileFormCard.hidden = true;
    }
  }

  if (showFileFormButton) {
    showFileFormButton.addEventListener("click", openFileForm);
  }

  if (hideFileFormButton) {
    hideFileFormButton.addEventListener("click", closeFileForm);
  }

  if (fileFormCancelButton) {
    fileFormCancelButton.addEventListener("click", closeFileForm);
  }

  if (fileForm) {
    fileForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      await addFile(fileForm);
      fileForm.reset();
      closeFileForm();
    });
  }

  document.addEventListener("click", (event) => {
    const deleteButton = event.target.closest("[data-delete-file]");
    const downloadButton = event.target.closest("[data-download-file]");

    if (deleteButton) {
      void deleteFile(deleteButton.dataset.deleteFile);
    }

    if (downloadButton) {
      handleDownload();
    }
  });
}

function setupProfilePage() {
  const profileForm = document.querySelector("#profileForm");

  if (profileForm) {
    profileForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      await saveProfile(profileForm);
    });
  }
}

async function init() {
  if (syncOn()) {
    let rem = defaultState.user.reminderPreference;
    try {
      const raw = localStorage.getItem(STORAGE_KEY + "_prefs");
      if (raw) {
        rem = JSON.parse(raw).user?.reminderPreference || rem;
      }
    } catch (_) {}
    await pullState();
    state.user.reminderPreference = rem;
  } else {
    Object.assign(state, loadState());
    ensureDemoData();
  }
  fillLinkSelects();
  renderWelcome();
  renderPreview();
  renderHomeTasks();
  renderHomeNotes();
  renderHomeFiles();
  renderStats();
  renderPriorityList();
  renderReminderList();
  renderTasks();
  renderNotes();
  renderFiles();
  renderProfile();
  setupHomePage();
  setupAuthPages();
  setupDashboardPage();
  setupTasksPage();
  setupNotesPage();
  setupFilesPage();
  setupProfilePage();
}

void init();

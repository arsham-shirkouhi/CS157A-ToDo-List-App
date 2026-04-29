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

let state = loadState();

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
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
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
    const card = document.createElement("article");
    card.className = `task-card${task.completed ? " completed" : ""}`;
    card.innerHTML = `
      <div class="task-head">
        <div>
          <h3 class="task-title">${escapeHtml(task.name)}</h3>
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
      const card = document.createElement("article");
      card.className = "note-card";
      card.innerHTML = `
        <div class="note-head">
          <div>
            <h3 class="note-title">${escapeHtml(note.title)}</h3>
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

function addTask(form) {
  const formData = new FormData(form);
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
  renderTasks();
  renderStats();
  renderPriorityList();
  renderReminderList();
  renderPreview();
  fillLinkSelects();
}

function addNote(form) {
  const formData = new FormData(form);
  const files = Array.from(document.querySelector("#noteFiles")?.files || []);
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
      taskId: formData.get("noteTaskLink") || "",
      noteId,
      createdAt: new Date().toISOString(),
    });
  });

  state.notes.push({
    id: noteId,
    title: formData.get("noteTitle").trim(),
    contents: formData.get("noteContents").trim(),
    taskId: formData.get("noteTaskLink") || "",
    createdAt: new Date().toISOString(),
    fileIds,
  });

  saveState();
  renderNotes();
  renderFiles();
  renderStats();
  fillLinkSelects();
  showSelectedFiles();
}

function addFile(form) {
  const formData = new FormData(form);
  const pickedFiles = Array.from(document.querySelector("#uploadFiles")?.files || []);

  pickedFiles.forEach((file) => {
    state.files.push({
      id: createId(),
      name: file.name,
      sizeLabel: formatFileSize(file.size),
      type: file.type || "File",
      taskId: formData.get("fileTaskLink") || "",
      noteId: formData.get("fileNoteLink") || "",
      createdAt: new Date().toISOString(),
    });
  });

  saveState();
  renderFiles();
  renderNotes();
}

function toggleTask(taskId) {
  state.tasks = state.tasks.map((task) =>
    task.id === taskId ? { ...task, completed: !task.completed } : task
  );
  saveState();
  renderTasks();
  renderStats();
  renderPriorityList();
  renderReminderList();
  renderPreview();
}

function deleteTask(taskId) {
  state.tasks = state.tasks.filter((task) => task.id !== taskId);
  state.notes = state.notes.map((note) =>
    note.taskId === taskId ? { ...note, taskId: "" } : note
  );
  state.files = state.files.map((file) =>
    file.taskId === taskId ? { ...file, taskId: "" } : file
  );
  saveState();
  renderTasks();
  renderNotes();
  renderFiles();
  renderStats();
  renderPriorityList();
  renderReminderList();
  renderPreview();
  fillLinkSelects();
}

function deleteFile(fileId) {
  state.files = state.files.filter((file) => file.id !== fileId);
  state.notes = state.notes.map((note) => ({
    ...note,
    fileIds: (note.fileIds || []).filter((id) => id !== fileId),
  }));
  saveState();
  renderFiles();
  renderNotes();
}

function saveProfile(form) {
  const formData = new FormData(form);
  state.user = {
    ...state.user,
    name: formData.get("profileName").trim(),
    email: formData.get("profileEmail").trim(),
    reminderPreference: formData.get("profileReminderPreference"),
  };
  saveState();
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
  const loginForm = document.querySelector("#loginForm");
  const signupForm = document.querySelector("#signupForm");

  if (loginForm) {
    loginForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const formData = new FormData(loginForm);
      state.user = {
        ...state.user,
        email: formData.get("email").trim(),
      };
      saveState();
      window.location.href = "dashboard.html";
    });
  }

  if (signupForm) {
    signupForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const formData = new FormData(signupForm);
      state.user = {
        ...state.user,
        name: formData.get("name").trim(),
        email: formData.get("email").trim(),
      };
      saveState();
      window.location.href = "dashboard.html";
    });
  }
}

function setupDashboardPage() {
  const logoutButton = document.querySelector("#logoutButton");
  if (logoutButton) {
    logoutButton.addEventListener("click", () => {
      window.location.href = "index.html";
    });
  }
}

function setupTasksPage() {
  const taskForm = document.querySelector("#taskForm");
  const filter = document.querySelector("#taskFilter");

  if (taskForm) {
    taskForm.addEventListener("submit", (event) => {
      event.preventDefault();
      addTask(taskForm);
      taskForm.reset();
    });
  }

  if (filter) {
    filter.addEventListener("change", renderTasks);
  }

  document.addEventListener("click", (event) => {
    const toggleButton = event.target.closest("[data-toggle-task]");
    const deleteButton = event.target.closest("[data-delete-task]");

    if (toggleButton) {
      toggleTask(toggleButton.dataset.toggleTask);
    }

    if (deleteButton) {
      deleteTask(deleteButton.dataset.deleteTask);
    }
  });
}

function setupNotesPage() {
  const noteForm = document.querySelector("#noteForm");
  const noteFiles = document.querySelector("#noteFiles");

  if (noteForm) {
    noteForm.addEventListener("submit", (event) => {
      event.preventDefault();
      addNote(noteForm);
      noteForm.reset();
      document.querySelector("#filePreview").innerHTML = "";
      fillLinkSelects();
    });
  }

  if (noteFiles) {
    noteFiles.addEventListener("change", showSelectedFiles);
  }
}

function setupFilesPage() {
  const fileForm = document.querySelector("#fileForm");

  if (fileForm) {
    fileForm.addEventListener("submit", (event) => {
      event.preventDefault();
      addFile(fileForm);
      fileForm.reset();
    });
  }

  document.addEventListener("click", (event) => {
    const deleteButton = event.target.closest("[data-delete-file]");
    const downloadButton = event.target.closest("[data-download-file]");

    if (deleteButton) {
      deleteFile(deleteButton.dataset.deleteFile);
    }

    if (downloadButton) {
      handleDownload();
    }
  });
}

function setupProfilePage() {
  const profileForm = document.querySelector("#profileForm");

  if (profileForm) {
    profileForm.addEventListener("submit", (event) => {
      event.preventDefault();
      saveProfile(profileForm);
    });
  }
}

function init() {
  ensureDemoData();
  fillLinkSelects();
  renderWelcome();
  renderPreview();
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

init();

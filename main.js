let remindersCache = [];

function showToast(message) {
    const container = document.getElementById("toastContainer");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.classList.add("show"), 10);
    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 280);
    }, 2600);
}

function requestNotificationPermission() {
    if (!("Notification" in window)) {
        showToast("Browser notifications are not supported.");
        return;
    }
    Notification.requestPermission().then((permission) => {
        showToast(permission === "granted" ? "Notifications enabled." : "Notification permission not granted.");
    });
}

function currentHHMM() {
    const now = new Date();
    return `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
}

function reminderFromCache(type) {
    return remindersCache.find((item) => item.type === type) || null;
}

function hydrateReminderUI() {
    const morning = reminderFromCache("morning");
    const night = reminderFromCache("night");

    const morningTime = document.getElementById("morningReminderTime");
    const nightTime = document.getElementById("nightReminderTime");
    const morningToggle = document.getElementById("morningReminderToggle");
    const nightToggle = document.getElementById("nightReminderToggle");
    const morningStatus = document.getElementById("morningStatusText");
    const nightStatus = document.getElementById("nightStatusText");

    if (morningTime) morningTime.value = morning?.time || "";
    if (nightTime) nightTime.value = night?.time || "";
    if (morningToggle) morningToggle.checked = !!morning?.enabled;
    if (nightToggle) nightToggle.checked = !!night?.enabled;
    if (morningStatus) morningStatus.textContent = morning?.enabled ? "Active" : "Disabled";
    if (nightStatus) nightStatus.textContent = night?.enabled ? "Active" : "Disabled";
}

async function fetchReminders() {
    const response = await fetch("/api/reminders");
    const data = await response.json();
    remindersCache = Array.isArray(data) ? data : [];
    hydrateReminderUI();
}

async function saveReminder(type, time, enabled) {
    console.log("Saving reminder", { type, time, enabled });
    const response = await fetch("/api/reminders/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type, time, enabled }),
    });
    return response.json();
}

async function toggleReminder(type, enabled) {
    console.log("Toggling reminder", { type, enabled });
    const response = await fetch("/api/reminders/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type, enabled }),
    });
    return response.json();
}

function validateTimeOrToast(value, label) {
    if (!value) {
        showToast(`${label} time is required.`);
        return false;
    }
    return true;
}

async function handleSaveReminder(type) {
    const inputId = type === "morning" ? "morningReminderTime" : "nightReminderTime";
    const toggleId = type === "morning" ? "morningReminderToggle" : "nightReminderToggle";
    const timeInput = document.getElementById(inputId);
    const toggle = document.getElementById(toggleId);
    if (!timeInput || !toggle) return;

    const timeValue = timeInput.value;
    const enabled = toggle.checked;
    if (!validateTimeOrToast(timeValue, type[0].toUpperCase() + type.slice(1))) return;

    const result = await saveReminder(type, timeValue, enabled);
    if (result.ok) {
        showToast("Reminder saved successfully");
        await fetchReminders();
    } else {
        showToast("Unable to save reminder.");
    }
}

function checkReminderNotification() {
    const current = currentHHMM();
    remindersCache.forEach((rem) => {
        if (!rem.enabled) return;
        if (rem.time === current) {
            if ("Notification" in window && Notification.permission === "granted") {
                new Notification("SkinSync Reminder", { body: "Time for your skincare routine ✨" });
            }
            showToast(`${rem.type} routine time ✨`);
        }
    });
}

function wireReminderControls() {
    const saveMorning = document.getElementById("saveMorningReminderBtn");
    const saveNight = document.getElementById("saveNightReminderBtn");
    const morningToggle = document.getElementById("morningReminderToggle");
    const nightToggle = document.getElementById("nightReminderToggle");

    if (saveMorning) saveMorning.addEventListener("click", () => handleSaveReminder("morning"));
    if (saveNight) saveNight.addEventListener("click", () => handleSaveReminder("night"));

    if (morningToggle) {
        morningToggle.addEventListener("change", async () => {
            const result = await toggleReminder("morning", morningToggle.checked);
            showToast(result.ok ? "Morning reminder status updated" : "Unable to update morning reminder");
            await fetchReminders();
        });
    }
    if (nightToggle) {
        nightToggle.addEventListener("change", async () => {
            const result = await toggleReminder("night", nightToggle.checked);
            showToast(result.ok ? "Night reminder status updated" : "Unable to update night reminder");
            await fetchReminders();
        });
    }
}

async function loadRemindersAndStartTimer() {
    const remindersSection = document.getElementById("reminders");
    if (!remindersSection) return;
    await fetchReminders();
    wireReminderControls();
    checkReminderNotification();
    setInterval(async () => {
        await fetchReminders();
        checkReminderNotification();
    }, 60 * 1000);
}

function renderWeeklyChart() {
    const canvas = document.getElementById('weeklyChart');
    if (!canvas) return;
    const weekData = JSON.parse(canvas.dataset.week || '[]');
    const labels = weekData.map((d) => d.date.slice(5));
    const values = weekData.map((d) => (d.done ? 1 : 0));

    new Chart(canvas, {
        type: 'bar',
        data: {
            labels,
            datasets: [{ label: 'Full routine completed', data: values, backgroundColor: '#d18ce0' }]
        },
        options: {
            scales: { y: { beginAtZero: true, max: 1, ticks: { stepSize: 1, callback: (v) => (v === 1 ? 'Yes' : 'No') } } }
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('enableNotificationsBtn');
    if (btn) btn.addEventListener('click', requestNotificationPermission);
    loadRemindersAndStartTimer();
    renderWeeklyChart();
});

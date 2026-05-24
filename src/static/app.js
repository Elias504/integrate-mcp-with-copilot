document.addEventListener("DOMContentLoaded", () => {
  // --- Dark mode ---
  const themeCheckbox = document.getElementById("theme-checkbox");
  const html = document.documentElement;

  function applyTheme(theme) {
    html.setAttribute("data-theme", theme);
    themeCheckbox.checked = theme === "dark";
  }

  function getInitialTheme() {
    const saved = localStorage.getItem("theme");
    if (saved === "dark" || saved === "light") return saved;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  applyTheme(getInitialTheme());

  themeCheckbox.addEventListener("change", () => {
    const next = themeCheckbox.checked ? "dark" : "light";
    localStorage.setItem("theme", next);
    applyTheme(next);
  });
  // --- End dark mode ---

  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const searchInput = document.getElementById("activity-search");
  const scheduleFilter = document.getElementById("schedule-filter");
  const sortSelect = document.getElementById("activity-sort");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  let latestRequestId = 0;

  function buildActivitiesUrl() {
    const queryParams = new URLSearchParams();
    const search = searchInput.value.trim();
    const schedule = scheduleFilter.value;
    const sort = sortSelect.value;

    if (search) {
      queryParams.set("search", search);
    }
    if (schedule) {
      queryParams.set("schedule", schedule);
    }
    if (sort) {
      queryParams.set("sort", sort);
    }

    const query = queryParams.toString();
    return query ? `/activities?${query}` : "/activities";
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    const requestId = ++latestRequestId;
    try {
      const selectedSchedule = scheduleFilter.value;
      const response = await fetch(buildActivitiesUrl());
      const activities = await response.json();

      if (requestId !== latestRequestId) {
        return;
      }

      // Clear loading message
      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      const schedules = new Set();

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        schedules.add(details.schedule);

        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;

        // Create participants HTML with delete icons instead of bullet points
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) =>
                      `<li><span class="participant-email">${email}</span><button class="delete-btn" data-activity="${name}" data-email="${email}">❌</button></li>`
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      scheduleFilter.innerHTML = '<option value="">All schedules</option>';
      Array.from(schedules)
        .sort((a, b) => a.localeCompare(b))
        .forEach((schedule) => {
          const option = document.createElement("option");
          option.value = schedule;
          option.textContent = schedule;
          scheduleFilter.appendChild(option);
        });
      if (Array.from(scheduleFilter.options).some(opt => opt.value === selectedSchedule)) {
        scheduleFilter.value = selectedSchedule;
      }

      if (Object.keys(activities).length === 0) {
        activitiesList.innerHTML = "<p>No activities match your current filters.</p>";
      }

      // Add event listeners to delete buttons
      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      if (requestId !== latestRequestId) {
        return;
      }

      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to unregister. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  searchInput.addEventListener("input", fetchActivities);
  scheduleFilter.addEventListener("change", fetchActivities);
  sortSelect.addEventListener("change", fetchActivities);

  // Initialize app
  fetchActivities();
});

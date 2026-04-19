import { initSite, getCurrentUser } from "../shared/site.js";

async function loadProfile() {
  await initSite();
  const user = getCurrentUser();

  if (!user) {
    window.location.href = "login.html";
    return;
  }

  // Split name for firstname and lastname
  const names = (user.name || "").split(" ");
  const firstName = names[0] || "N/A";
  const lastName = names.length > 1 ? names.slice(1).join(" ") : "";

  const welcomeText = document.getElementById("welcome-message-text");
  if (welcomeText) {
    const fullName = user.name || firstName;
    if (user.gender === "Mr") {
      welcomeText.textContent = `👉 Mr. ${fullName}, welcome to your Trident Wear account`;
    } else if (user.gender === "Miss") {
      welcomeText.textContent = `👉 Miss ${fullName}, welcome to your Trident Wear account`;
    } else {
      welcomeText.textContent = `👉 Welcome ${fullName}, to your Trident Wear account`;
    }
  }

  // Sidebar Updates
  const sidebarName = document.getElementById("sidebar-name");
  const sidebarEmail = document.getElementById("sidebar-email");
  const sidebarRole = document.getElementById("sidebar-role");

  if (sidebarName) sidebarName.textContent = user.name || "N/A";
  if (sidebarEmail) sidebarEmail.textContent = user.email || "N/A";
  if (sidebarRole) sidebarRole.textContent = user.role === "admin" ? "(Admin)" : "(Member)";

  // Content Updates
  const emailInput = document.getElementById("profile-email-input");
  const firstNameInput = document.getElementById("profile-firstname");
  const lastNameInput = document.getElementById("profile-lastname");

  if (emailInput) emailInput.value = user.email || "N/A";
  if (firstNameInput) firstNameInput.value = firstName;
  if (lastNameInput) lastNameInput.value = lastName;

  // Setup tabs
  const tabLinks = document.querySelectorAll("[data-tab]");
  const sections = document.querySelectorAll(".profile-section-tab");

  tabLinks.forEach(link => {
    link.addEventListener("click", e => {
      e.preventDefault();
      
      // Get target tab
      const targetId = "section-" + link.getAttribute("data-tab");
      
      // Hide all panels
      sections.forEach(sec => {
        sec.style.display = "none";
      });

      // Show target panel if it exists
      const targetPanel = document.getElementById(targetId);
      if (targetPanel) {
        targetPanel.style.display = "block";
      }

      // Update sidebar active link styling if needed (optional)
      tabLinks.forEach(l => {
        l.style.color = "#555";
        l.style.fontWeight = "normal";
      });
      link.style.color = "#117864";
      link.style.fontWeight = "600";
    });
  });
}

loadProfile();

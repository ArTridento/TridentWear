import { post } from "../shared/api.js";
import { initSite, showToast } from "../shared/site.js";

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();

  const form = document.querySelector("[data-contact-form]");
  const status = document.querySelector("[data-contact-status]");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      name: form.querySelector("#contact-name").value.trim(),
      email: form.querySelector("#contact-email").value.trim(),
      message: form.querySelector("#contact-message").value.trim(),
    };

    try {
      await post("/api/contact", payload);
      form.reset();
      status.innerHTML = `<div class="helper-note success">Message sent. We will reply from the Trident desk soon.</div>`;
      showToast("Message sent successfully.");
    } catch (error) {
      status.innerHTML = `<div class="helper-note danger">${error.message}</div>`;
      showToast(error.message, "error");
    }
  });
});

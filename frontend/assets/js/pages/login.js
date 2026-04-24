import { initAuthPage } from "./auth-page.js";

window.addEventListener("DOMContentLoaded", async () => {
  await initAuthPage("login");
});

// Simple mobile nav toggle
document.addEventListener("DOMContentLoaded", () => {
  const navToggle = document.getElementById("navToggle");
  const nav = document.getElementById("siteNav");

  if (!navToggle || !nav) return;

  navToggle.addEventListener("click", () => {
    nav.classList.toggle("open");
  });
});

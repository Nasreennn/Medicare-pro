document.addEventListener('DOMContentLoaded', function () {
  // quick safe helper for toasts/messages if you want to expose messages to JS
  // theme cookie toggle (simple)
  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', function () {
      document.body.classList.toggle('dark-mode');
      document.cookie = `theme=${document.body.classList.contains('dark-mode') ? 'dark' : 'light'};path=/;max-age=${60*60*24*7}`;
    });
  }
});

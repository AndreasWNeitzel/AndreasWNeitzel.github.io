(() => {
  const root = document.documentElement;
  const button = document.querySelector(".theme");
  if (!button) return;
  const dark = matchMedia("(prefers-color-scheme: dark)");
  const current = () => root.dataset.theme || (dark.matches ? "dark" : "light");
  const label = () => { button.textContent = current() === "dark" ? "Light theme" : "Dark theme"; };
  button.addEventListener("click", () => {
    const next = current() === "dark" ? "light" : "dark";
    root.dataset.theme = next;
    try { localStorage.setItem("theme", next); } catch (e) {}
    label();
  });
  dark.addEventListener("change", label);
  label();
  button.hidden = false;
})();

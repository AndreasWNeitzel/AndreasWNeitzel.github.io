// Home band: a pause button for the sliding title cards (hover and keyboard focus pause them too).
(() => {
  const band = document.querySelector("[data-band]");
  const btn = band && band.querySelector("[data-band-pause]");
  if (!btn) return;
  btn.addEventListener("click", () => {
    const paused = band.classList.toggle("is-paused");
    btn.setAttribute("aria-pressed", String(paused));
    btn.setAttribute("aria-label", paused ? "Play the sliding cards" : "Pause the sliding cards");
  });
})();

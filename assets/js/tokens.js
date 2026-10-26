// Resolve site colour tokens to real colours and notice theme changes.
(() => {
  const probe = document.createElement("span");
  probe.style.cssText = "position:absolute;visibility:hidden;pointer-events:none";
  document.body.appendChild(probe);
  window.siteTokens = {
    colour(name) {
      probe.style.color = `var(${name})`;
      return getComputedStyle(probe).color;
    },
    onThemeChange(callback) {
      const observer = new MutationObserver(callback);
      observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
      const scheme = matchMedia("(prefers-color-scheme: dark)");
      scheme.addEventListener("change", callback);
      return () => { observer.disconnect(); scheme.removeEventListener("change", callback); };
    },
    categorical() { return Array.from({ length: 10 }, (_, i) => this.colour(`--cat-${i}`)); },
  };
})();

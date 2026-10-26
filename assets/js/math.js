// Typeset mathematics with KaTeX on pages that declare `math: true`. Each formula is written as
// <span class="tex" data-tex="LaTeX">plain fallback</span>, so readers without JavaScript keep the
// fallback. Scripts that write formulas later call window.renderTex(element).
(() => {
  const render = (root) => {
    if (!window.katex) return;
    (root || document).querySelectorAll(".tex[data-tex]").forEach((el) => {
      if (el.dataset.done === el.dataset.tex) return;
      try {
        window.katex.render(el.dataset.tex, el, {
          throwOnError: false,
          displayMode: el.classList.contains("tex-display"),
          output: "htmlAndMathml",
        });
        el.dataset.done = el.dataset.tex;
      } catch (e) {
        /* keep the fallback text */
      }
    });
  };
  window.renderTex = render;
  render(document);
})();

"""Print the CSS for the site's type marks: one line pictogram per entry type, used as a CSS mask
so it takes the type colour. Paste the output over the .tag block in assets/css/site.css.

Usage: python3 scripts/type_marks.py
"""

from urllib.parse import quote

# 16 x 16 line pictograms, drawn on a 1.5 px stroke with round caps and joins
GLYPHS = {
    "paper": "M4 1.75h5.25l3 3V14.25H4Z M9.25 1.75v3h3 M6 8h4.25 M6 10.25h4.25 M6 12.5h2.5",
    "talk": "M6 3.5a2 2 0 0 1 4 0v3.75a2 2 0 0 1-4 0Z M3.75 7.25a4.25 4.25 0 0 0 8.5 0 M8 11.5v2.75 M5.75 14.25h4.5",
    "poster": "M2.5 2h11v8h-11Z M5 10l-1.25 4.25 M11 10l1.25 4.25 M5 4.75h6 M5 7h3.75",
    "grant": "M8 1.75a4.25 4.25 0 1 1 0 8.5a4.25 4.25 0 1 1 0-8.5Z M8 4.25v3.5 M6.25 6h3.5 M5.5 9.5l-1 4.75 3.5-1.75 3.5 1.75-1-4.75",
    "hpc": "M3 1.75h10v12.5H3Z M3 5.9h10 M3 10.1h10 M5.25 3.8h1.5 M5.25 8h1.5 M5.25 12.2h1.5 M9.5 3.8h1.25 M9.5 8h1.25 M9.5 12.2h1.25",
    "observing": "M1.75 14.25h12.5 M3 14.25v-4.5a5 5 0 0 1 10 0v4.5 M7 5v4.75 M9 5v4.75 M7 9.75h2",
    "software": "M5.5 4.25L2 8l3.5 3.75 M10.5 4.25L14 8l-3.5 3.75 M9 2.75l-2 10.5",
    "award": "M5 1.75l3 4.5 3-4.5 M8 7.25a3.5 3.5 0 1 1 0 7a3.5 3.5 0 1 1 0-7Z M8 9.25v3",
    "position": "M1.75 5.75L8 2l6.25 3.75 M2.75 5.75h10.5 M4.25 6.5v5.5 M8 6.5v5.5 M11.75 6.5v5.5 M2 14.25h12",
    "abroad": "M8 1.75a6.25 6.25 0 1 1 0 12.5a6.25 6.25 0 1 1 0-12.5Z M1.75 8h12.5 M8 1.75c-2.25 2.4-2.25 10.1 0 12.5 M8 1.75c2.25 2.4 2.25 10.1 0 12.5",
    "degree": "M1.5 6L8 3l6.5 3L8 9Z M4.5 7.5v3.25c2 1.5 5 1.5 7 0V7.5 M14.5 6v4",
    "service": "M2.5 3.25h11v11h-11Z M2.5 6.25h11 M5 1.75v3 M11 1.75v3 M5 9h1 M7.5 9h1 M10 9h1 M5 11.5h1 M7.5 11.5h1",
    "teaching": "M2 2.25h12v8H2Z M5.25 13.75L8 10.25l2.75 3.5 M4.25 4.75l2.5 2.25 M9 5h3 M9 7.5h2",
    "membership": "M8 1.75a1.75 1.75 0 1 1 0 3.5a1.75 1.75 0 1 1 0-3.5Z M3.25 10.75a1.75 1.75 0 1 1 0 3.5a1.75 1.75 0 1 1 0-3.5Z M12.75 10.75a1.75 1.75 0 1 1 0 3.5a1.75 1.75 0 1 1 0-3.5Z M7.1 5L4.1 10.9 M8.9 5l3 5.9 M5 12.5h6",
    "data": "M3 4c0-1.25 2.25-2.25 5-2.25S13 2.75 13 4s-2.25 2.25-5 2.25S3 5.25 3 4Z M3 4v8c0 1.25 2.25 2.25 5 2.25s5-1 5-2.25V4 M3 8c0 1.25 2.25 2.25 5 2.25s5-1 5-2.25",
    "event": "M3.5 14.5V1.75 M3.5 2.5h8.75l-1.75 3 1.75 3H3.5",
    "now": "M8 6.5a1.5 1.5 0 1 1 0 3a1.5 1.5 0 1 1 0-3Z M5 5a4.25 4.25 0 0 0 0 6 M11 5a4.25 4.25 0 0 1 0 6 M3 3a7 7 0 0 0 0 10 M13 3a7 7 0 0 1 0 10",
    "guide": "M8 3.75C6.5 2.5 4.25 2 1.75 2.25V12.5c2.5-.25 4.75.25 6.25 1.5 1.5-1.25 3.75-1.75 6.25-1.5V2.25C11.75 2 9.5 2.5 8 3.75Z M8 3.75V14",
    "accepted": "M8 1.75a6.25 6.25 0 1 1 0 12.5a6.25 6.25 0 1 1 0-12.5Z M5.25 8.25l1.9 1.9 3.6-4",
}
COLOUR = {  # type -> colour token
    "paper": "--t-paper", "talk": "--t-talk", "poster": "--t-poster", "grant": "--t-grant", "hpc": "--t-hpc",
    "observing": "--t-observing", "software": "--t-software", "award": "--t-award", "position": "--t-position",
    "abroad": "--t-position", "degree": "--t-position", "service": "--t-service", "teaching": "--t-service",
    "membership": "--t-position", "data": "--t-data", "event": "--t-data", "now": "--t-software", "guide": "--t-data", "accepted": "--t-paper",
}


def uri(path: str) -> str:
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='none' stroke='black' "
        f"stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'><path d='{path}'/></svg>"
    )
    return 'url("data:image/svg+xml,' + quote(svg, safe=" /:=',.") + '")'


print("  /* type marks: a line pictogram in the type colour, then a plain label (scripts/type_marks.py) */")
print("  .tag { --tag: var(--muted); --glyph: none; display: inline-flex; align-items: center; gap: 7px;")
print("    font: 500 0.76rem/1.25 var(--mono); color: var(--ink-2); white-space: nowrap; }")
print("  .tag::before { content: \"\"; flex: none; inline-size: 15px; block-size: 15px; background: var(--tag);")
print("    -webkit-mask: var(--glyph) center / contain no-repeat; mask: var(--glyph) center / contain no-repeat; }")
for k, path in GLYPHS.items():
    print(f"  .tag--{k} {{ --tag: var({COLOUR[k]}); --glyph: {uri(path)}; }}")

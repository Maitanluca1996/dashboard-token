"""Il CSS della pagina "Guida ai costi", in un posto solo.

La guida ha due template, uno per lingua (guide.html e guide.en.html). Lo
stile e' lo stesso nei due e con la lingua non c'entra niente: tenerlo
scritto in entrambi vorrebbe dire copiare a mano ogni ritocco nell'altro
file, e prima o poi qualcuno se ne dimentica. Sta quindi qui, e i due
template lo richiamano con il segnaposto __GUIDE_CSS__.

E' la stessa scelta, per la stessa ragione, che tiene HEADER_CSS dentro
header.py invece che dentro le tre pagine.

NOTA PER CHI NON CONOSCE PYTHON: quella qui sotto e' una semplice stringa
di testo lunga (tripla virgoletta = puo' andare a capo quante volte vuole).
Python non esegue nulla di cio' che c'e' scritto dentro: si limita a
incollarlo nell'HTML finale, dove sara' il browser a interpretarlo. Le
graffe { } del CSS non danno nessun fastidio proprio perche' questa non e'
una stringa "formattata" -- vedi il docstring di templating.py.

[EN] The CSS of the "Cost guide" page, in one place only.

The guide has two templates, one per language (guide.html and
guide.en.html). The style is the same in both and has nothing to do with
language: keeping it written in both would mean copying every tweak by hand
into the other file, and sooner or later someone forgets. So it lives here,
and the two templates call it in with the __GUIDE_CSS__ placeholder.

It is the same choice, for the same reason, that keeps HEADER_CSS inside
header.py rather than inside the three pages.

NOTE FOR THOSE UNFAMILIAR WITH PYTHON: what follows is simply a long text
string (triple quotes = it may wrap as many times as it likes). Python does
not execute anything written inside: it just pastes it into the final HTML,
where the browser will interpret it. The CSS braces { } cause no trouble
precisely because this is not a "formatted" string -- see templating.py's
docstring.
"""

GUIDE_CSS = """  :root {
    color-scheme: light;
    --surface-1: #fcfcfb; --page: #f9f9f7; --text-primary: #0b0b0b;
    --text-secondary: #52514e; --text-muted: #898781; --gridline: #e1e0d9;
    --series-1: #2a78d6; --border: rgba(11, 11, 11, 0.10);
    --accent-bg: rgba(42, 120, 214, 0.08); --accent-br: rgba(42, 120, 214, 0.30);
    --pos: #2f6f4a; --warn: #9a5b12; --warn-bg: rgba(154, 91, 18, 0.09);
    --alert: #a33a2a;
    --control-bg: #ffffff;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      color-scheme: dark;
      --surface-1: #1a1a19; --page: #0d0d0d; --text-primary: #ffffff;
      --text-secondary: #c3c2b7; --text-muted: #898781; --gridline: #2c2c2a;
      --series-1: #3987e5; --border: rgba(255, 255, 255, 0.10);
      --accent-bg: rgba(57, 135, 229, 0.13); --accent-br: rgba(57, 135, 229, 0.38);
      --pos: #6cbf90; --warn: #d69b4e; --warn-bg: rgba(214, 155, 78, 0.12);
      --alert: #e08571;
      --control-bg: #24241f;
    }
  }
  * { box-sizing: border-box; }
  body { margin: 0; padding: 24px 16px 56px; background: var(--page); color: var(--text-primary); font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
__HEADER_CSS__

  .page-title-block { margin-bottom: 8px; }

  .sec { margin-bottom: 24px; scroll-margin-top: 20px; }
  .sec:last-child { margin-bottom: 0; }

  /* Sezioni collassabili: bottone di testata + wrapper animato via
     grid-template-rows (0fr -> 1fr), il modo per animare un'altezza
     "auto" senza dover misurare nulla in JS. Il fade sul contenuto interno
     rende il movimento morbido invece dello scatto secco di <details>.
     [EN] Collapsible sections: header button + wrapper animated via
     grid-template-rows (0fr -> 1fr), the way to animate an "auto" height
     without measuring anything in JS. The fade on the inner content makes
     the movement smooth instead of the abrupt snap of <details>. */
  .sec-summary { all: unset; box-sizing: border-box; display: flex; align-items: flex-start; gap: 10px; padding: 10px 0; margin-bottom: 6px; border-radius: 8px; cursor: pointer; width: 100%; }
  .sec-summary:hover .sec-head-text h2 { color: var(--series-1); }
  .sec-summary:focus-visible { outline: 2px solid var(--series-1); outline-offset: 4px; }
  .sec.open .sec-summary { margin-bottom: 16px; }
  .sec-chevron { flex-shrink: 0; margin-top: 5px; color: var(--text-muted); transition: transform 0.28s cubic-bezier(0.4, 0, 0.2, 1); }
  .sec.open .sec-chevron { transform: rotate(90deg); }
  .sec-head-text { flex: 1; min-width: 0; }
  .sec-eyebrow { font-size: 11px; color: var(--series-1); font-weight: 700; letter-spacing: 0.06em; display: block; margin-bottom: 4px; text-transform: uppercase; }
  h2 { font-size: 19px; margin: 0; letter-spacing: -0.01em; transition: color 0.15s ease; }
  .sec-sub { color: var(--text-secondary); font-size: 13.5px; margin: 6px 0 0; line-height: 1.55; }

  .sec-body { display: grid; grid-template-rows: 0fr; transition: grid-template-rows 0.32s cubic-bezier(0.4, 0, 0.2, 1); }
  .sec.open .sec-body { grid-template-rows: 1fr; }
  .sec-body-inner { overflow: hidden; opacity: 0; transition: opacity 0.2s ease; }
  .sec.open .sec-body-inner { opacity: 1; transition: opacity 0.3s ease 0.08s; }

  .group-divider { display: flex; align-items: center; gap: 12px; margin: 40px 0 24px; }
  .group-divider:first-child { margin-top: 0; }
  .group-divider .gd-title { font-size: 12px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-muted); white-space: nowrap; }
  .group-divider .gd-line { height: 1px; background: var(--gridline); flex: 1; }

  .panel { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 16px 18px; margin-bottom: 14px; }
  .prose { font-size: 13.5px; line-height: 1.65; color: var(--text-secondary); }
  .prose p { margin: 0 0 12px; }
  .prose p:last-child { margin-bottom: 0; }
  .prose strong { color: var(--text-primary); font-weight: 600; }
  h3 { font-size: 13.5px; margin: 18px 0 8px; color: var(--text-primary); }
  h3:first-child { margin-top: 0; }

  .table-wrap { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: left; color: var(--text-muted); font-weight: 500; font-size: 11px; text-transform: uppercase; letter-spacing: 0.02em; padding: 8px; border-bottom: 1px solid var(--gridline); white-space: nowrap; }
  td { padding: 8px; border-bottom: 1px solid var(--gridline); vertical-align: top; color: var(--text-secondary); line-height: 1.5; }
  tr:last-child td { border-bottom: none; }
  td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
  td.model-name { font-weight: 600; color: var(--text-primary); white-space: nowrap; }
  td strong { color: var(--text-primary); font-weight: 600; }
  tr.row-hi td { background: var(--accent-bg); }
  .cell-note { display: block; color: var(--text-muted); font-size: 11.5px; margin-top: 2px; font-style: italic; }

  .keybox { background: var(--accent-bg); border: 1px solid var(--accent-br); border-radius: 12px; padding: 14px 18px; margin-bottom: 14px; font-size: 13.5px; line-height: 1.65; color: var(--text-secondary); }
  .keybox .kb-label { font-size: 11px; font-weight: 600; letter-spacing: 0.06em; color: var(--series-1); margin: 0 0 6px; }
  .keybox p { margin: 0; }
  .keybox p + p { margin-top: 10px; }
  .keybox strong { color: var(--text-primary); font-weight: 600; }

  .callout { border: 1px solid var(--border); border-left: 3px solid var(--warn); background: var(--warn-bg); border-radius: 0 12px 12px 0; padding: 14px 18px; margin-bottom: 14px; font-size: 13px; line-height: 1.6; color: var(--text-secondary); }
  .callout-title { display: block; font-weight: 600; color: var(--warn); margin-bottom: 5px; }
  .callout p { margin: 0; }

  .scen-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; margin-bottom: 14px; }
  .scen { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 16px 18px; }
  .scen-ppu { border-top: 3px solid var(--series-1); }
  .scen-flat { border-top: 3px solid var(--pos); }
  .scen-kicker { font-size: 11px; font-weight: 600; letter-spacing: 0.06em; margin: 0 0 3px; }
  .scen-ppu .scen-kicker { color: var(--series-1); }
  .scen-flat .scen-kicker { color: var(--pos); }
  .scen h3 { margin: 0 0 2px; font-size: 15px; }
  .scen-who { font-size: 12px; color: var(--text-muted); margin: 0 0 14px; }
  .scen dl { margin: 0; }
  .scen dt { font-size: 11px; font-weight: 600; letter-spacing: 0.04em; color: var(--text-muted); margin-top: 12px; }
  .scen dt:first-child { margin-top: 0; }
  .scen dd { margin: 3px 0 0; font-size: 13px; line-height: 1.55; color: var(--text-secondary); }
  .scen dd strong { color: var(--text-primary); font-weight: 600; }

  .lever { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; margin-bottom: 12px; overflow: hidden; }
  .lever-main { padding: 16px 18px 14px; display: flex; gap: 14px; }
  .lever-rank { flex-shrink: 0; width: 26px; height: 26px; border-radius: 8px; background: var(--page); border: 1px solid var(--gridline); display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; color: var(--text-muted); }
  .lever-body { flex: 1; min-width: 0; }
  .lever-top { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin-bottom: 8px; }
  .lever-top h3 { margin: 0; font-size: 14.5px; flex: 1 1 auto; min-width: 180px; }
  .impact { font-size: 10px; font-weight: 600; letter-spacing: 0.07em; text-transform: uppercase; padding: 3px 7px; border-radius: 5px; white-space: nowrap; }
  .impact-alto { background: rgba(163, 58, 42, 0.10); color: var(--alert); }
  .impact-medio { background: var(--warn-bg); color: var(--warn); }
  .impact-basso { background: var(--gridline); color: var(--text-muted); }
  .lever .prose { font-size: 13px; }

  .antis { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 12px; }
  .anti { background: var(--surface-1); border: 1px solid var(--border); border-left: 3px solid var(--alert); border-radius: 0 12px 12px 0; padding: 14px 16px; }
  .anti h3 { margin: 0 0 5px; font-size: 13.5px; color: var(--alert); }
  .anti p { margin: 0; font-size: 12.5px; line-height: 1.55; color: var(--text-secondary); }

  .check-panel { padding: 4px 0 0; }
  .check-groups { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0; }
  .check-group { padding: 16px 18px; border-left: 1px solid var(--gridline); }
  .check-group:first-child { border-left: none; }
  .check-group h3 { margin: 0 0 10px; font-size: 11px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: var(--text-muted); display: flex; align-items: center; gap: 7px; }
  .check-group .cg-num { display: inline-flex; align-items: center; justify-content: center; width: 16px; height: 16px; border-radius: 50%; background: var(--accent-bg); color: var(--series-1); font-size: 9.5px; font-weight: 700; }
  .check-group ul { margin: 0; padding: 0; list-style: none; }
  .check-group li { position: relative; padding-left: 20px; margin-bottom: 9px; font-size: 12.5px; line-height: 1.5; color: var(--text-secondary); }
  .check-group li:last-child { margin-bottom: 0; }
  .check-group li::before { content: ""; position: absolute; left: 0; top: 4px; width: 11px; height: 11px; border: 1.5px solid var(--gridline); border-radius: 3px; background: var(--page); }
  @media (max-width: 760px) {
    .check-groups { grid-template-columns: 1fr; }
    .check-group { border-left: none; border-top: 1px solid var(--gridline); }
    .check-group:first-child { border-top: none; }
  }

  .hint { font-size: 12.5px; color: var(--text-muted); margin: 0 0 10px; line-height: 1.55; }
  .hint:last-child { margin-bottom: 0; }
  .hint strong { color: var(--text-secondary); font-weight: 600; }
  code { font-family: ui-monospace, "Cascadia Code", monospace; font-size: 11.5px; color: var(--text-secondary); }
  @media (prefers-reduced-motion: reduce) {
    * { animation-duration: 0.001ms !important; transition-duration: 0.001ms !important; }
    html { scroll-behavior: auto; }
  }"""

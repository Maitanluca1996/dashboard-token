"""Componente condiviso per l'intestazione e la barra di navigazione del sito.

Genera un'intestazione identica e coerente per tutte le pagine
(dashboard.html, pricing.html, guida-costi.html) con evidenziazione
automatica della voce di menu attiva e data/ora di aggiornamento.

NOTA PER CHI NON CONOSCE PYTHON:
Prima le 3 pagine avevano ciascuna il proprio pezzo di HTML/CSS per
l'intestazione, ripetuto e copiato tre volte nei rispettivi template. Qui
invece l'intestazione (CSS + HTML della barra di navigazione) è scritta
UNA volta sola, in questo file: ogni pagina, alla generazione, chiama
render_header() passando solo "quale scheda è quella attiva in questa
pagina" (dashboard / pricing / guide), e si ritrova l'HTML già pronto e
identico nelle altre due. Se domani si vuole cambiare il logo o aggiungere
una voce di menu, si tocca SOLO questo file, non tre template diversi.

[EN] Shared component for the site header and navigation bar.

Generates an identical, consistent header for every page
(dashboard.html, pricing.html, guida-costi.html) with automatic
highlighting of the active menu item and the last-update date/time.

NOTE FOR THOSE UNFAMILIAR WITH PYTHON:
Previously each of the 3 pages had its own chunk of HTML/CSS for the
header, repeated and copied three times in their respective templates.
Here instead the header (CSS + HTML of the navigation bar) is written
ONCE, in this file: each page, at generation time, calls
render_header() passing only "which tab is the active one on this
page" (dashboard / pricing / guide), and gets HTML that is ready-made
and identical to the other two pages. If tomorrow you want to change
the logo or add a menu item, you touch ONLY this file, not three
different templates.
"""

# Una TRIPLA STRINGA (tra tre virgolette """ ... """) può contenere testo
# su più righe così com'è scritto, "a capo" inclusi: qui dentro c'è del CSS
# vero e proprio, che verrà incollato nell'HTML finale al posto del
# segnaposto __HEADER_CSS__ (vedi templating.py e i vari render_*.py).
# Essendo una stringa Python come un'altra, il CSS qui dentro NON viene
# eseguito da Python in alcun modo: è testo puro, che il browser leggerà
# più tardi come foglio di stile.
# [EN] A TRIPLE-QUOTED STRING (between three quotes """ ... """) can hold
# text spanning multiple lines exactly as written, line breaks included:
# inside here there is actual CSS, which will be pasted into the final
# HTML in place of the __HEADER_CSS__ placeholder (see templating.py and
# the various render_*.py). Being an ordinary Python string, the CSS in
# here is NOT executed by Python in any way: it is plain text, which the
# browser will later read as a stylesheet.
HEADER_CSS = """
  /* Header & Navigation Bar Condivisi
     [EN] Shared header & navigation bar */
  html {
    scroll-behavior: smooth;
    /* Spazio della barra di scorrimento sempre riservato, anche sulle
       pagine corte che non ne hanno bisogno. Senza, passando da una
       pagina lunga (dashboard) a una corta (tariffario) la barra
       sparisce, l'area utile si allarga di una quindicina di pixel e
       tutto il contenuto centrato -- intestazione compresa -- scatta di
       lato: sembra che l'intestazione cambi larghezza ad ogni cambio di
       pagina, mentre in realta' si sta spostando la pagina sotto.
       [EN] Scrollbar space always reserved, even on short pages that do
       not need one. Without it, moving from a long page (dashboard) to a
       short one (price list) the scrollbar disappears, the usable area
       widens by some fifteen pixels and all the centered content --
       header included -- jumps sideways: the header seems to change
       width on every page switch, while it is really the page shifting
       underneath. */
    scrollbar-gutter: stable;
  }

  /* Larghezza del contenuto: UNA sola definizione per tutte e tre le
     pagine. Prima ogni template aveva la sua (900px dashboard e
     tariffario, 860px guida) e l'intestazione, che e' identica ovunque,
     si ritrovava larga 40px in meno su una pagina delle tre. Se domani
     va cambiata, si cambia qui e vale per tutte -- che e' lo stesso
     motivo per cui il resto dell'intestazione vive in questo file.
     [EN] Content width: ONE single definition for all three pages. Each
     template used to have its own (900px dashboard and price list, 860px
     guide) and the header, identical everywhere, ended up 40px narrower
     on one page out of three. If it ever needs changing, change it here
     and it applies to all -- the same reason the rest of the header
     lives in this file. */
  .wrap { max-width: 900px; margin: 0 auto; }
  /* Il respiro superiore della pagina passa dal body all'intestazione.
     Serve perche' l'intestazione e' agganciata in cima: il padding del
     body scorre via col resto della pagina, e senza questo spostamento il
     logo finirebbe a filo del bordo dello schermo non appena si scorre.
     Da fermi l'aspetto e' identico a prima -- e' lo stesso spazio, solo
     dentro un elemento diverso. Questa regola arriva DOPO quella di body
     nei tre template, quindi vince per ordine di cascata.
     [EN] The page's top breathing room moves from the body to the
     header. Needed because the header is pinned to the top: the body
     padding scrolls away with the rest of the page, and without this
     shift the logo would end up flush with the screen edge as soon as
     you scroll. At rest the look is identical to before -- the same
     space, just inside a different element. This rule comes AFTER the
     body rule in the three templates, so it wins by cascade order. */
  body { padding-top: 0; }
  .site-header {
    display: flex;
    flex-direction: column;
    gap: 14px;
    margin-bottom: 24px;
    padding-top: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--gridline);
    /* Resta visibile mentre si scorre: e' la barra di navigazione fra le
       tre pagine, e serve tanto in cima quanto in fondo a una tabella
       lunga. Lo sfondo non e' un abbellimento ma un requisito: da
       trasparente il contenuto le scorrerebbe attraverso, rendendola
       illeggibile. E' lo stesso --page che mostra gia' oggi.
       [EN] Stays visible while scrolling: it is the navigation bar
       between the three pages, needed at the bottom of a long table as
       much as at the top. The background is not cosmetic but a
       requirement: if transparent, the content would scroll right
       through it, making it unreadable. Same --page it already shows. */
    position: sticky;
    top: 0;
    z-index: 200;
    background: var(--page);
  }
  .site-header-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
  }
  .brand-group {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .brand-badge {
    font-size: 22px;
    line-height: 1;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .brand-info {
    display: flex;
    flex-direction: column;
  }
  .brand-name {
    font-size: 15px;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: var(--text-primary);
    line-height: 1.2;
  }
  .brand-tag {
    font-size: 11.5px;
    color: var(--text-muted);
    font-weight: 500;
  }
  .site-header-meta {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .meta-status {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: var(--text-secondary);
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 5px 12px;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }
  .status-indicator {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #1baf7a;
    display: inline-block;
    flex-shrink: 0;
    box-shadow: 0 0 0 2px rgba(27, 175, 122, 0.2);
  }
  .meta-label {
    color: var(--text-muted);
  }
  .meta-timestamp {
    font-weight: 500;
    color: var(--text-primary);
  }
  /* Il pallino verde vuol dire "questi numeri sono di adesso". Se la
     pagina resta aperta mentre il file viene rigenerato i numeri
     invecchiano: il pallino passa all'ambra e accanto si accende il
     bottone "Aggiorna" (chi decide quando, vedi lo script in fondo alla
     dashboard). Nessun ricaricamento a sorpresa: lo chiede l'utente.
     [EN] The green dot means "these numbers are current". If the page
     stays open while the file is regenerated, the numbers age: the dot
     turns amber and the "Aggiorna" (refresh) button lights up next to it
     (who decides when: see the script at the bottom of the dashboard).
     No surprise reloads: the user asks for it. */
  .meta-status.stale .status-indicator {
    background: #d99a1e;
    box-shadow: 0 0 0 2px rgba(217, 154, 30, 0.2);
  }
  .meta-refresh {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: inherit;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-secondary);
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 5px 12px;
    cursor: pointer;
    white-space: nowrap;
    transition: color 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
    /* Il bottone nasce nascosto e compare a meta' lettura: che si presenti
       con una piccola entrata invece di apparire di colpo accanto alla
       data. Nessun fill-mode, cosi' a fine animazione il transform torna
       a quello dichiarato qui sotto per :hover.
       [EN] The button starts hidden and shows up mid-reading: let it
       enter with a small animation instead of popping in next to the
       date. No fill-mode, so when the animation ends the transform goes
       back to the one declared below for :hover. */
    animation: meta-refresh-in 0.32s ease;
  }
  @keyframes meta-refresh-in {
    from { opacity: 0; transform: translateY(-3px); }
    to { opacity: 1; transform: none; }
  }
  .meta-refresh[hidden] { display: none; }
  .meta-refresh:hover {
    color: var(--text-primary);
    border-color: var(--series-1);
    transform: translateY(-1px);
  }
  .meta-refresh:active { transform: translateY(0); }
  .meta-refresh:focus-visible {
    outline: 2px solid var(--series-1);
    outline-offset: 2px;
  }
  .meta-refresh .refresh-icon { transition: transform 0.45s ease; }
  .meta-refresh:hover .refresh-icon { transform: rotate(180deg); }
  /* Mentre la pagina si sta ricaricando l'iconcina gira: il click ha
     avuto effetto anche se il browser ci mette un attimo a rispondere.
     [EN] While the page is reloading the little icon spins: the click
     did take effect even if the browser takes a moment to respond. */
  .meta-refresh.busy .refresh-icon { animation: meta-refresh-spin 0.8s linear infinite; }
  @keyframes meta-refresh-spin { to { transform: rotate(360deg); } }
  .site-nav {
    display: flex;
    width: 100%;
  }
  .nav-tabs {
    display: flex;
    align-items: center;
    gap: 4px;
    width: 100%;
    box-sizing: border-box;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  .nav-tab {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    flex: 1;
    min-width: 120px;
    padding: 8px 14px;
    border-radius: 7px;
    font-size: 13px;
    font-weight: 500;
    text-decoration: none;
    color: var(--text-secondary);
    border: 1px solid transparent;
    /* Solo i colori, non le misure. Con "all" si animavano anche padding e
       min-width, che cambiano quando l'intestazione passa in forma
       compatta: per i 150ms dell'animazione la scheda era piu' alta di
       quanto sarebbe finita, e --header-h -- che si misura nell'istante
       del cambio -- usciva sbagliata di 4px. Quattro pixel di contenuto in
       movimento tra intestazione e barra dei filtri, per un paio di
       fotogrammi. Le misure ora scattano, e la misura e' esatta subito.
       [EN] Colors only, not measures. With "all", padding and min-width
       animated too, and those change when the header goes compact: for
       the 150ms of the animation the tab was taller than it would end
       up, and --header-h -- measured at the instant of the switch --
       came out 4px wrong. Four pixels of content moving between header
       and filter bar, for a couple of frames. Measures now snap, and the
       measurement is exact right away. */
    transition: color 0.15s ease, background-color 0.15s ease,
                border-color 0.15s ease, box-shadow 0.15s ease;
    white-space: nowrap;
  }
  .nav-tab:hover {
    color: var(--text-primary);
    background: var(--border);
  }
  .nav-tab.active {
    color: var(--series-1);
    background: var(--control-bg, #ffffff);
    font-weight: 600;
    border-color: var(--border);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }
  @media (prefers-color-scheme: dark) {
    .nav-tab.active {
      background: var(--control-bg, #24241f);
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
    }
  }
  .nav-tab:focus-visible {
    outline: 2px solid var(--series-1);
    outline-offset: 2px;
  }
  .nav-icon {
    flex-shrink: 0;
    stroke: currentColor;
    opacity: 0.85;
    transition: opacity 0.15s ease;
  }
  .nav-tab.active .nav-icon {
    opacity: 1;
  }
  .nav-text {
    display: inline-block;
  }
  .page-title-block {
    margin-bottom: 20px;
  }
  .page-title-block h1 {
    font-size: 24px;
    font-weight: 700;
    letter-spacing: -0.01em;
    margin: 0 0 4px;
    color: var(--text-primary);
  }
  .page-desc {
    color: var(--text-secondary);
    font-size: 13px;
    margin: 0;
    line-height: 1.5;
  }

  /* --- Forma compatta durante lo scorrimento -------------------------------
     Da ferma l'intestazione resta quella di sempre: logo, sottotitolo, data
     e schede su due righe. Appena la pagina scorre si stringe su una riga
     sola. Serve perche' agganciata in cima, sommata alla barra dei filtri,
     arrivava a coprire un terzo dello schermo -- in una pagina che esiste
     per leggere una tabella lunga.
     "display: contents" su .site-header-top toglie di mezzo il contenitore
     senza toccare il markup: logo, data e schede diventano fratelli sulla
     stessa riga. Nel sorgente la data viene prima delle schede (perche' a
     due righe sta in alto a destra); "order" le rimette nell'ordine giusto
     per una riga sola, senza duplicare markup ne' spostare nodi da JS.
     La classe la accende lo script in fondo a questo file.
     [EN] --- Compact form while scrolling ---
     At rest the header stays as always: logo, subtitle, date and tabs on
     two rows. As soon as the page scrolls it tightens onto a single row.
     Needed because, pinned to the top and added to the filter bar, it
     came to cover a third of the screen -- on a page that exists to read
     a long table.
     "display: contents" on .site-header-top removes the container
     without touching the markup: logo, date and tabs become siblings on
     the same row. In the source the date comes before the tabs (because
     on two rows it sits top right); "order" puts them back in the right
     order for a single row, without duplicating markup or moving nodes
     via JS. The class is switched on by the script at the end of this
     file. */
  html.chrome-compact .site-header {
    padding-top: 10px;
    padding-bottom: 10px;
    gap: 10px;
  }
  html.chrome-compact .brand-tag { display: none; }
  /* Su schermo stretto ci si ferma qui, e in piu' si toglie la data: logo,
     data e tre schede su una riga sola a 375px non ci stanno: le schede
     finirebbero fuori dallo schermo e la pagina prenderebbe a scorrere in
     orizzontale. La data torna appena si risale in cima.
     [EN] On narrow screens we stop here, and the date goes away too:
     logo, date and three tabs on one row do not fit at 375px -- the tabs
     would overflow the screen and the page would start scrolling
     horizontally. The date comes back as soon as you scroll back to the
     top. */
  @media (max-width: 699px) {
    html.chrome-compact .site-header-meta { display: none; }
  }
  @media (min-width: 700px) {
    html.chrome-compact .site-header {
      flex-direction: row;
      align-items: center;
      gap: 16px;
    }
    html.chrome-compact .site-header-top { display: contents; }
    html.chrome-compact .brand-group { order: 1; flex-shrink: 0; }
    html.chrome-compact .site-nav { order: 2; flex: 1; min-width: 0; }
    html.chrome-compact .site-header-meta { order: 3; flex-shrink: 0; }
    html.chrome-compact .nav-tab { padding: 6px 12px; min-width: 92px; }
  }
  /* Niente transizione sulle misure: il passaggio da due righe a una non e'
     animabile (flex-direction non lo e') e scatta comunque. Animare intanto
     il padding darebbe un ibrido -- meta' scatto e meta' scivolamento -- e
     soprattutto lascerebbe --header-h in ritardo per tutta la durata
     dell'animazione, con la barra dei filtri agganciata a un'altezza che
     l'intestazione non ha piu'. Meglio uno scatto netto e coerente; a non
     farlo sfarfallare pensa la fascia morta tra le due soglie.
     [EN] No transition on measures: the two-rows-to-one switch is not
     animatable (flex-direction is not) and snaps anyway. Animating the
     padding meanwhile would give a hybrid -- half snap, half glide --
     and above all would leave --header-h lagging for the whole
     animation, with the filter bar pinned to a height the header no
     longer has. Better one clean, consistent snap; the dead band between
     the two thresholds keeps it from flickering. */

  /* Entrata dell'intestazione: la pagina si compone invece di apparire
     tutta insieme al primo fotogramma. "backwards" applica lo stato
     iniziale (trasparente, spostato in alto) gia' prima che l'animazione
     parta, altrimenti si vedrebbe un lampo del contenuto gia' a posto.
     [EN] Header entrance: the page composes itself instead of appearing
     all at once on the first frame. "backwards" applies the initial
     state (transparent, shifted up) before the animation even starts,
     otherwise you would see a flash of the content already in place. */
  .has-reveal .site-header { animation: header-in 0.5s cubic-bezier(0.22, 1, 0.36, 1) backwards; }
  .has-reveal .page-title-block { animation: header-in 0.5s cubic-bezier(0.22, 1, 0.36, 1) 0.07s backwards; }
  @keyframes header-in { from { opacity: 0; transform: translateY(-8px); } }

  /* RIVELAZIONE ALLO SCROLL (condivisa dalle 3 pagine)
     Ogni elemento marcato con l'attributo data-reveal nel template parte
     trasparente e leggermente piu' in basso, e scivola al suo posto quando
     entra nella finestra del browser: la classe "revealed" gliela mette
     REVEAL_JS (vedi in fondo a questo file) via IntersectionObserver.

     Tutto e' condizionato alla classe "has-reveal" sull'elemento <html>,
     messa da REVEAL_BOOT nell'<head>: se il JS e' disattivato, o il
     browser non ha IntersectionObserver, quella classe non arriva mai e le
     regole qui sotto non si applicano affatto -- la pagina resta
     semplicemente visibile e statica, invece di restare invisibile per
     sempre in attesa di un osservatore che non esiste.

     La regola sul selettore universale dentro un blocco non ancora
     rivelato mette in PAUSA le animazioni CSS dei suoi contenuti (le barre
     che crescono, la linea che si disegna nei grafici della dashboard):
     senza, partirebbero al caricamento mentre il riquadro e' ancora fuori
     schermo, e sarebbero gia' finite quando ci si arriva scorrendo.
     [EN] SCROLL REVEAL (shared by the 3 pages)
     Every element marked with the data-reveal attribute in the template
     starts transparent and slightly lower, and slides into place when it
     enters the browser viewport: the "revealed" class is added by
     REVEAL_JS (see the bottom of this file) via IntersectionObserver.

     Everything is gated on the "has-reveal" class on the <html> element,
     set by REVEAL_BOOT in the <head>: if JS is disabled, or the browser
     lacks IntersectionObserver, that class never arrives and the rules
     below do not apply at all -- the page simply stays visible and
     static, instead of staying invisible forever waiting for an observer
     that does not exist.

     The universal-selector rule inside a not-yet-revealed block PAUSES
     the CSS animations of its contents (the growing bars, the line
     drawing itself in the dashboard charts): without it they would start
     at load time while the box is still off-screen, and would already be
     over by the time you scroll down to it. */
  .has-reveal [data-reveal] {
    opacity: 0;
    transform: translateY(16px);
    transition: opacity 0.45s cubic-bezier(0.22, 1, 0.36, 1),
                transform 0.45s cubic-bezier(0.22, 1, 0.36, 1);
  }
  .has-reveal [data-reveal].revealed {
    opacity: 1;
    transform: none;
  }
  .has-reveal [data-reveal]:not(.revealed) * {
    animation-play-state: paused;
  }

  /* Chi ha chiesto al sistema operativo di ridurre le animazioni ottiene
     la pagina gia' a posto: niente scorrimento morbido, niente entrata, e
     le animazioni interne partono subito invece di restare in pausa in
     attesa di una rivelazione che qui non produce alcun movimento.
     [EN] Whoever asked the operating system to reduce animations gets
     the page already in place: no smooth scrolling, no entrance, and the
     inner animations start right away instead of staying paused waiting
     for a reveal that produces no motion here. */
  /* In stampa non c'e' nessuno scorrimento che possa far scattare
     l'osservatore: senza questa regola, tutto cio' che al momento della
     stampa non era ancora stato rivelato finirebbe sul foglio come uno
     spazio bianco.
     [EN] In print there is no scrolling that could trigger the observer:
     without this rule, whatever had not been revealed yet at print time
     would end up on paper as blank space. */
  @media print {
    .has-reveal [data-reveal] { opacity: 1; transform: none; }
  }

  @media (prefers-reduced-motion: reduce) {
    html { scroll-behavior: auto; }
    .site-header, .page-title-block { animation: none; }
    .has-reveal [data-reveal] { opacity: 1; transform: none; transition: none; }
    .has-reveal [data-reveal]:not(.revealed) * { animation-play-state: running; }
    .meta-refresh { animation: none; }
    .meta-refresh, .meta-refresh .refresh-icon { transition: none; }
    .meta-refresh:hover { transform: none; }
    .meta-refresh:hover .refresh-icon { transform: none; }
    .meta-refresh.busy .refresh-icon { animation: none; }
  }
"""

# NAV_ITEMS e' una LISTA di dizionari: un elemento per ciascuna voce di
# menu della barra di navigazione, nell'ordine in cui appaiono in pagina.
# "id" e' usato solo internamente (per capire qual e' la voce "attiva",
# vedi render_header sotto), "href" e' il link vero, "label" il testo
# mostrato, "icon" l'SVG dell'iconcina incollato cosi' com'e' nell'HTML.
# [EN] NAV_ITEMS is a LIST of dictionaries: one element per menu item of
# the navigation bar, in the order they appear on the page.
# "id" is used only internally (to figure out which item is "active",
# see render_header below), "href" is the actual link, "label" the text
# shown, "icon" the SVG of the small icon pasted as-is into the HTML.
NAV_ITEMS = [
    {
        "id": "dashboard",
        "href": "dashboard.html",
        "label": "Dashboard",
        "icon": '<svg class="nav-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9"></rect><rect x="14" y="3" width="7" height="5"></rect><rect x="14" y="12" width="7" height="9"></rect><rect x="3" y="16" width="7" height="5"></rect></svg>',
    },
    {
        "id": "pricing",
        "href": "pricing.html",
        "label": "Tariffario",
        "icon": '<svg class="nav-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg>',
    },
    {
        "id": "guide",
        "href": "guida-costi.html",
        "label": "Guida ai costi",
        "icon": '<svg class="nav-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 1 1 7.072 0l-.548.547A3.374 3.374 0 0 0 14 18.469V19a2 2 0 1 1-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path></svg>',
    },
]


# Script che accompagna l'intestazione. Vive qui fuori, come stringa
# normale, e NON dentro la f-string di render_header: in una f-string le
# graffe { } sono segnaposto, e un blocco JavaScript ne e' pieno
# ("function () {"), quindi Python proverebbe a interpretarlo come codice
# suo. E' lo stesso motivo per cui templating.py usa .replace() invece di
# .format() sui template (vedi il docstring li').
# [EN] Script that goes along with the header. It lives out here, as a
# regular string, and NOT inside render_header's f-string: in an f-string
# the braces { } are placeholders, and a JavaScript block is full of them
# ("function () {"), so Python would try to interpret it as its own code.
# It is the same reason templating.py uses .replace() instead of
# .format() on the templates (see the docstring there).
HEADER_SCRIPT = """  <script>
  document.getElementById('meta-timestamp').textContent = GENERATED_AT;
  /* Pubblica l'altezza dell'intestazione come variabile CSS --header-h.
     Serve a chi deve agganciarsi SOTTO di lei (la barra dei filtri della
     dashboard): un valore fisso si romperebbe, perche' l'altezza cambia
     quando le schede di navigazione vanno a capo su schermo stretto.
     ResizeObserver segue anche i riflow che non passano da un resize della
     finestra (caricamento dei font, zoom); dove non c'e', si ripiega sui
     due eventi che lo approssimano meglio.
     [EN] Publishes the header height as the CSS variable --header-h.
     Needed by whatever must pin itself BELOW it (the dashboard's filter
     bar): a fixed value would break, because the height changes when the
     navigation tabs wrap on narrow screens. ResizeObserver also follows
     reflows that do not go through a window resize (font loading, zoom);
     where unavailable, we fall back on the two events that approximate
     it best. */
  (function () {
    var root = document.documentElement;
    var h = document.querySelector('.site-header');
    if (!h) return;
    function publish() {
      root.style.setProperty('--header-h', h.offsetHeight + 'px');
    }
    publish();
    if (typeof ResizeObserver !== 'undefined') {
      new ResizeObserver(publish).observe(h);
    } else {
      window.addEventListener('resize', publish);
      window.addEventListener('load', publish);
    }

    /* Forma compatta dell'intestazione una volta che la pagina si e' mossa:
       le regole stanno nel CSS, sotto html.chrome-compact.
       Due soglie invece di una: si stringe oltre i 100px e si riapre sotto
       i 60. Con una soglia sola, fermarsi giusto sul valore limite farebbe
       rimbalzare la classe avanti e indietro ad ogni pixel -- e qui il
       cambio e' vistoso, perche' l'intestazione passa da due righe a una.
       La fascia morta tra le due soglie lo impedisce.
       --header-h viene ripubblicata SUBITO dopo il cambio di classe, e non
       lasciata al ResizeObserver: quello notifica al giro di rendering
       successivo, e per quel fotogramma la barra dei filtri resterebbe
       agganciata a un'altezza che l'intestazione non ha piu', scoprendo
       una striscia di contenuto in movimento. Qui la lettura di
       offsetHeight forza il calcolo e la misura e' gia' quella nuova.
       L'osservatore resta comunque, per i riflow che non passano di qui
       (schede che vanno a capo, zoom, caricamento dei font).
       [EN] Compact form of the header once the page has moved: the rules
       live in the CSS, under html.chrome-compact.
       Two thresholds instead of one: it tightens past 100px and reopens
       below 60. With a single threshold, stopping right on the limit
       would bounce the class back and forth at every pixel -- and here
       the change is conspicuous, since the header goes from two rows to
       one. The dead band between the two thresholds prevents it.
       --header-h is re-published IMMEDIATELY after the class change, not
       left to the ResizeObserver: that one notifies on the next
       rendering pass, and for that frame the filter bar would stay
       pinned to a height the header no longer has, uncovering a strip of
       moving content. Here the offsetHeight read forces the layout and
       the measurement is already the new one. The observer stays anyway,
       for reflows that do not come through here (tabs wrapping, zoom,
       font loading). */
    function check() {
      var y = window.scrollY || window.pageYOffset || 0;
      var compatta = root.classList.contains('chrome-compact');
      var vuole = y > 100 ? true : (y < 60 ? false : compatta);
      if (vuole === compatta) return;
      root.classList.toggle('chrome-compact', vuole);
      publish();
    }
    window.addEventListener('scroll', check, { passive: true });
    check();
  })();
  </script>"""


def render_header(active_id, refresh_control=False):
    """Genera l'HTML dell'intestazione unificata con navigazione a schede.

    "active_id" e' l'id (es. "dashboard") della pagina che sta venendo
    generata in questo momento, cosi' la funzione sa su quale scheda
    mettere l'evidenziazione "sei qui". La data/ora di generazione non
    viene piu' passata qui come testo gia' pronto: lo span resta vuoto e
    lo riempie a runtime lo script in fondo a questa funzione, leggendo la
    variabile GENERATED_AT definita in site-meta.js (vedi main.py) --
    cosi' l'orario non finisce piu' scritto rigido nell'HTML delle 3
    pagine, e rigenerare la dashboard senza nuovi dati non produce piu'
    un diff fatto solo di quello.

    "refresh_control" aggiunge accanto alla data il bottone "Aggiorna",
    che ricarica la pagina conservando i filtri: serve solo alla
    dashboard, l'unica pagina i cui numeri cambiano ad ogni turno. Nasce
    nascosto (hidden) e viene acceso dallo script della dashboard quando
    i dati a schermo cominciano ad essere vecchi; sulle altre pagine il
    bottone non viene proprio generato.

    [EN] Generates the HTML of the unified header with tabbed navigation.

    "active_id" is the id (e.g. "dashboard") of the page being generated
    right now, so the function knows which tab gets the "you are here"
    highlight. The generation date/time is no longer passed here as
    ready-made text: the span stays empty and is filled at runtime by
    the script at the end of this function, reading the GENERATED_AT
    variable defined in site-meta.js (see main.py) -- this way the time
    no longer ends up hard-coded in the HTML of the 3 pages, and
    regenerating the dashboard without new data no longer produces a
    diff made only of that.

    "refresh_control" adds next to the date the "Aggiorna" button, which
    reloads the page preserving the filters: only the dashboard needs
    it, being the only page whose numbers change every turn. It starts
    hidden and is turned on by the dashboard script when the on-screen
    data starts getting old; on the other pages the button is not even
    generated.
    """
    # qui accumuliamo un pezzo di HTML per ciascuna voce di menu
    # [EN] here we accumulate one chunk of HTML for each menu item
    tabs_html = []

    for item in NAV_ITEMS:
        is_active = item["id"] == active_id
        # Se questa e' la voce della pagina corrente, aggiungiamo la classe
        # CSS "active" (per lo stile evidenziato) e l'attributo HTML
        # aria-current="page" (segnala "questa e' la pagina attuale" ai
        # lettori di schermo per non vedenti); altrimenti, stringhe vuote.
        # [EN] If this is the current page's item, we add the CSS class
        # "active" (for the highlighted style) and the HTML attribute
        # aria-current="page" (which tells screen readers for blind
        # users "this is the current page"); otherwise, empty strings.
        active_cls = " active" if is_active else ""
        aria_current = ' aria-current="page"' if is_active else ""

        # F-string su piu' righe (una stringa f'...' per riga, che Python
        # incolla automaticamente in una sola perche' sono scritte una
        # sotto l'altra tra parentesi tonde): costruisce il link <a> di
        # questa singola voce di menu, con dentro l'icona SVG e il testo.
        # [EN] Multi-line f-string (one f'...' string per line, which
        # Python automatically glues into a single one because they are
        # written one below the other inside round brackets): it builds
        # the <a> link of this single menu item, with the SVG icon and
        # the text inside.
        tabs_html.append(
            f'      <a href="{item["href"]}" class="nav-tab{active_cls}"{aria_current}>\n'
            f'        {item["icon"]}\n'
            f'        <span class="nav-text">{item["label"]}</span>\n'
            f'      </a>'
        )

    # "\n".join(tabs_html) incolla tutte le voci di menu una sotto l'altra
    # (con un a-capo tra l'una e l'altra), ottenendo il blocco HTML
    # completo della barra di navigazione.
    # [EN] "\n".join(tabs_html) glues all the menu items one below the
    # other (with a newline between each), producing the complete HTML
    # block of the navigation bar.
    tabs_block = "\n".join(tabs_html)

    # Bottone "Aggiorna" (solo dashboard, vedi refresh_control nella
    # docstring). L'icona e' la classica freccia circolare; aria-live
    # sull'insieme non serve, perche' il bottone che appare non e' un
    # annuncio ma un comando disponibile.
    # [EN] "Aggiorna" (refresh) button (dashboard only, see
    # refresh_control in the docstring). The icon is the classic
    # circular arrow; aria-live on the group is not needed, because the
    # button that appears is not an announcement but an available
    # command.
    refresh_html = ""
    if refresh_control:
        refresh_html = (
            '\n        <button type="button" class="meta-refresh" id="meta-refresh" hidden'
            ' title="Ricarica i dati conservando i filtri scelti">'
            '<svg class="refresh-icon" width="13" height="13" viewBox="0 0 24 24" fill="none"'
            ' stroke="currentColor" stroke-width="2.2" stroke-linecap="round"'
            ' stroke-linejoin="round" aria-hidden="true">'
            '<path d="M21 12a9 9 0 1 1-2.64-6.36"></path>'
            '<polyline points="21 3 21 9 15 9"></polyline>'
            "</svg>"
            "<span>Aggiorna</span></button>"
        )

    # Il "return f\"\"\" ... \"\"\"" restituisce l'HTML completo
    # dell'intestazione come un'unica stringa multi-riga, con dentro
    # {generated_at} e {tabs_block} sostituiti dai valori calcolati sopra
    # (stessa tecnica delle f-string vista poco fa, solo su un blocco di
    # testo piu' grande).
    # [EN] The "return f\"\"\" ... \"\"\"" returns the complete HTML of
    # the header as a single multi-line string, with {generated_at} and
    # {tabs_block} inside replaced by the values computed above (same
    # f-string technique seen just before, only on a larger block of
    # text).
    return f"""  <script src="site-meta.js"></script>
  <header class="site-header">
    <div class="site-header-top">
      <div class="brand-group">
        <span class="brand-badge" aria-hidden="true">🪙</span>
        <div class="brand-info">
          <span class="brand-name">Claude Code</span>
          <span class="brand-tag">Monitoraggio Token &amp; Costi</span>
        </div>
      </div>
      <div class="site-header-meta">
        <div class="meta-status" id="meta-status" title="Data e ora dell'ultimo aggiornamento">
          <span class="status-indicator" aria-hidden="true"></span>
          <span class="meta-label">Aggiornato</span>
          <span class="meta-timestamp" id="meta-timestamp"></span>
        </div>{refresh_html}
      </div>
    </div>
    <nav class="site-nav" aria-label="Navigazione principale">
      <div class="nav-tabs">
{tabs_block}
      </div>
    </nav>
  </header>
{HEADER_SCRIPT}"""


# Frammento da incollare nell'<head> di ogni pagina (segnaposto
# __REVEAL_BOOT__, vedi i template e i render_*.py). Deve stare li' e non
# in fondo al body: marca l'elemento <html> PRIMA che il browser disegni
# qualcosa, cosi' i blocchi con data-reveal nascono gia' trasparenti. Se
# lo si mettesse in fondo alla pagina si vedrebbe un lampo del contenuto
# gia' a posto, subito seguito dalla sua sparizione e ri-entrata --
# esattamente l'effetto opposto di quello voluto.
#
# Il controllo su IntersectionObserver e' il "degrado elegante": su un
# browser che non ha quella funzione (o con JavaScript disattivato) la
# classe non viene mai messa, il CSS di rivelazione resta inerte e la
# pagina si vede tutta, ferma. Meglio nessuna animazione che una pagina
# bianca.
#
# La chiave 'skipPageIntro' in sessionStorage e' la scappatoia per i
# ricaricamenti "di servizio" della dashboard: quello silenzioso che
# avviene mentre la finestra non e' in primo piano e quello chiesto col
# bottone "Aggiorna". In entrambi i casi si sta solo rinfrescando dei
# numeri, e senza questo interruttore l'intera pagina rifarebbe la sua
# entrata animata da capo -- fastidioso, non grazioso. Chi ricarica
# imposta la chiave subito prima; qui la si legge, la si cancella (vale
# per un solo caricamento) e si salta l'animazione. Un ricaricamento
# manuale col tasto del browser, che la chiave non ce l'ha, continua a
# mostrare l'entrata normalmente.
# [EN] Fragment to paste into the <head> of every page (placeholder
# __REVEAL_BOOT__, see the templates and the render_*.py). It must live
# there and not at the end of the body: it marks the <html> element
# BEFORE the browser paints anything, so blocks with data-reveal are
# born already transparent. Putting it at the bottom of the page would
# show a flash of the content already in place, immediately followed by
# its disappearance and re-entrance -- exactly the opposite of the
# intended effect.
#
# The check on IntersectionObserver is the "graceful degradation": on a
# browser lacking that feature (or with JavaScript disabled) the class
# is never added, the reveal CSS stays inert and the page is fully
# visible, static. Better no animation than a blank page.
#
# The 'skipPageIntro' key in sessionStorage is the escape hatch for the
# dashboard's "service" reloads: the silent one that happens while the
# window is not in the foreground and the one requested via the
# "Aggiorna" button. In both cases we are just refreshing some numbers,
# and without this switch the whole page would replay its animated
# entrance from scratch -- annoying, not graceful. Whoever reloads sets
# the key right before; here we read it, delete it (it is valid for a
# single load) and skip the animation. A manual reload with the browser
# button, which does not carry the key, keeps showing the entrance
# normally.
REVEAL_BOOT = (
    "<script>(function(){"
    # sessionStorage puo' sollevare un'eccezione (cookie di terze parti
    # bloccati, modalita' privata di alcuni browser): il try/catch evita
    # che un errore qui impedisca del tutto le animazioni.
    # [EN] sessionStorage may raise an exception (third-party cookies
    # blocked, private mode in some browsers): the try/catch prevents an
    # error here from blocking the animations entirely.
    "try{if(sessionStorage.getItem('skipPageIntro')){"
    "sessionStorage.removeItem('skipPageIntro');return;}}catch(e){}"
    "if('IntersectionObserver' in window)"
    "document.documentElement.classList.add('has-reveal');"
    "})();</script>"
)

# Script condiviso, incollato in fondo al <body> di ogni pagina
# (segnaposto __REVEAL_JS__). Osserva i blocchi marcati data-reveal e
# aggiunge la classe "revealed" appena entrano in vista, una volta sola:
# unobserve() subito dopo, perche' un blocco gia' rivelato non deve
# ri-animarsi scorrendo avanti e indietro, e togliere l'osservatore evita
# di tenere in vita callback inutili su una pagina lunga.
#
# Come per HEADER_CSS, questa e' una semplice stringa di testo: Python non
# esegue nulla di quello che c'e' scritto qui dentro, si limita a
# incollarlo nell'HTML finale, dove sara' il browser a eseguirlo.
# [EN] Shared script, pasted at the bottom of the <body> of every page
# (placeholder __REVEAL_JS__). It watches the blocks marked data-reveal
# and adds the "revealed" class as soon as they come into view, once
# only: unobserve() right after, because an already revealed block must
# not re-animate while scrolling back and forth, and removing the
# observer avoids keeping useless callbacks alive on a long page.
#
# As with HEADER_CSS, this is a plain text string: Python does not
# execute anything written in here, it just pastes it into the final
# HTML, where the browser will execute it.
REVEAL_JS = """<script>
(function () {
  // Se REVEAL_BOOT non ha messo la classe (JS o API non disponibili), il
  // CSS di rivelazione non e' attivo: non c'e' niente da rivelare.
  // [EN] If REVEAL_BOOT did not set the class (JS or API unavailable),
  // the reveal CSS is not active: there is nothing to reveal.
  if (!document.documentElement.classList.contains('has-reveal')) return;
  var els = document.querySelectorAll('[data-reveal]');
  if (!els.length) return;
  var obs = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('revealed');
      obs.unobserve(entry.target);
    });
  }, {
    // Margine negativo in basso: il blocco si rivela quando e' entrato per
    // davvero, non appena il suo primo pixel sfiora il bordo dello schermo.
    // threshold 0 e non una percentuale perche' un riquadro piu' alto della
    // finestra non raggiungerebbe mai una soglia di visibilita' elevata.
    // [EN] Negative bottom margin: the block reveals itself once it has
    // truly entered, not as soon as its first pixel grazes the screen
    // edge. threshold 0 rather than a percentage because a box taller
    // than the window would never reach a high visibility ratio.
    rootMargin: '0px 0px -48px 0px',
    threshold: 0
  });
  els.forEach(function (el) { obs.observe(el); });
})();
</script>"""

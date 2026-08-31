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
# i18n serve per due cose sole, entrambe nello switch di lingua piu'
# sotto: sapere QUALI lingue esistono e come si chiamano. Le stringhe
# dell'intestazione non passano da qui -- vengono tradotte nel browser
# a partire dagli attributi data-i18n del markup.
# [EN] i18n is needed for two things only, both in the language switch
# below: knowing WHICH languages exist and what they are called. The
# header strings do not go through here -- they are translated in the
# browser starting from the markup's data-i18n attributes.
from . import i18n

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
     pagine, e nessuna eccezione. Prima ogni template aveva la sua (900px
     dashboard e tariffario, 860px guida) e l'intestazione, che e'
     identica ovunque, si ritrovava larga 40px in meno su una pagina
     delle tre; poi la dashboard ha rialzato la propria a 1172px per far
     posto alla colonna dei filtri, ed e' tornato lo stesso difetto al
     contrario -- passando da una scheda all'altra la cornice si
     restringeva sotto gli occhi.
     Il valore e' quello che serve alla pagina piu' esigente: 900px di
     contenuto piu' la colonna dei filtri della dashboard (248px) e il
     suo scarto (24px). Le altre due pagine non hanno una colonna e
     usano tutto lo spazio per il contenuto: e' una riga di testo lunga
     sulla guida, ed e' il prezzo di una cornice che non si muove.
     [EN] Content width: ONE single definition for all three pages, and
     no exceptions. Each template used to have its own (900px dashboard
     and price list, 860px guide) and the header, identical everywhere,
     ended up 40px narrower on one page out of three; then the dashboard
     raised its own to 1172px to make room for the filters column, and
     the same flaw came back the other way round -- moving from one tab
     to the next, the frame narrowed before your eyes.
     The value is what the most demanding page needs: 900px of content
     plus the dashboard's filters column (248px) and its gap (24px). The
     other two pages have no column and spend it all on content: that is
     a long line of text on the guide, and it is the price of a frame
     that does not move. */
  .wrap { max-width: 1172px; margin: 0 auto; }
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
  /* Tre zone: il logo a sinistra, la data con il bottone Aggiorna al
     centro, la scelta della lingua a destra.
     Griglia "1fr auto 1fr" e non flex con space-between: con space-between
     il gruppo di mezzo finisce al centro solo se i due lati pesano uguale,
     e non pesano uguale -- il logo con il suo sottotitolo e' largo, la
     combo della lingua no. Le due colonne 1fr, essendo per definizione
     larghe uguale, tengono il gruppo di mezzo al centro VERO della riga
     qualunque cosa ci sia ai lati.
     [EN] Three zones: the logo on the left, the date with the refresh
     button in the centre, the language choice on the right.
     A "1fr auto 1fr" grid and not flex with space-between: with
     space-between the middle group only ends up centred if the two sides
     weigh the same, and they do not -- the logo with its subtitle is wide,
     the language combo is not. The two 1fr columns, being by definition
     equally wide, hold the middle group at the TRUE centre of the row
     whatever sits on either side. */
  .site-header-top {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 12px;
  }
  .brand-group { justify-self: start; min-width: 0; }
  .site-header-meta { justify-self: center; }
  .lang-combo { justify-self: end; }
  /* Sotto i 700px le tre zone su una riga non ci stanno. La riga va a capo:
     logo e lingua restano affiancati, la data con il suo bottone scende
     sotto, sempre centrata. Non e' una "forma compatta" che scatta allo
     scorrimento: e' la stessa intestazione che si dispone su due righe, e
     vale identica da ferma e mentre si scorre.
     [EN] Below 700px the three zones do not fit on one row. The row wraps:
     logo and language stay side by side, the date with its button drops
     below, still centred. It is not a "compact form" triggered by
     scrolling: it is the same header laid out on two rows, and it is
     identical at rest and while scrolling. */
  @media (max-width: 699px) {
    .site-header-top {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
    }
    .site-header-meta { order: 3; width: 100%; justify-content: center; }
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
  /* La data non e' una pillola come il bottone accanto: non si preme, non
     si apre, non ha stati. Il bordo tondo la faceva sembrare un controllo
     e le dava un peso che una didascalia non deve avere. Restano il
     pallino e il testo, che sono l'informazione.
     [EN] The date is not a pill like the button next to it: it is not
     pressed, does not open, has no states. The round border made it look
     like a control and gave it a weight a caption should not have. The
     dot and the text remain, which are the information. */
  .meta-status {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: var(--text-secondary);
    padding: 5px 2px;
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
  /* La scelta della lingua.
     NON un <select> nativo: dentro un <option> il browser non disegna
     markup, quindi una bandiera non si potrebbe mostrare. E le bandiere
     emoji non sono un'alternativa -- Windows non le disegna, le rende come
     la coppia di lettere che le compone dentro due riquadri (verificato
     misurando la larghezza resa). Quindi un elenco costruito a mano, con i
     ruoli ARIA che dicono a un lettore di schermo che si tratta di una
     scelta fra opzioni, e non un bottone qualsiasi.
     Il bottone che apre resta nel vocabolario "a pillola" gia' adoperato
     qui accanto da .meta-status e .meta-refresh: bordo tondo, stesso corpo,
     stessi colori. Cambia il contenuto, non la forma.
     [EN] The language choice.
     NOT a native <select>: inside an <option> the browser draws no markup,
     so a flag could not be shown. And flag emoji are no alternative --
     Windows does not draw them, it renders them as the pair of letters
     composing them inside two boxes (verified by measuring the rendered
     width). Hence a hand-built list, with the ARIA roles that tell a screen
     reader this is a choice among options and not just some button.
     The button that opens it stays in the "pill" vocabulary already used
     next to it by .meta-status and .meta-refresh: round border, same size,
     same colours. The content changes, not the shape. */
  .lang-combo { position: relative; }
  .lang-trigger {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    font-family: inherit;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-secondary);
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 5px 10px 5px 8px;
    cursor: pointer;
    white-space: nowrap;
    transition: color 0.18s ease, border-color 0.18s ease;
  }
  .lang-trigger:hover {
    color: var(--text-primary);
    border-color: var(--series-1);
  }
  .lang-trigger:focus-visible {
    outline: 2px solid var(--series-1);
    outline-offset: 2px;
  }
  .lang-current { display: inline-flex; align-items: center; gap: 7px; }
  /* La bandiera e' un rettangolo pieno: senza un filo di contorno, la banda
     bianca dell'italiana sparirebbe nello sfondo chiaro della pillola. Il
     contorno lo mette il CSS e non l'SVG, ed e' un grigio medio
     semitrasparente: un nero trasparente sarebbe invisibile sul tema scuro,
     un bianco trasparente sul tema chiaro. Un grigio a meta' strada si vede
     su entrambi, e questo CSS serve le due varianti di tutte e tre le
     pagine.
     box-shadow inset e non border: un bordo spingerebbe il contenuto
     dell'SVG verso l'interno, restringendo le bande di un pixel per lato;
     l'ombra interna si disegna sopra senza toccare il disegno.
     [EN] The flag is a solid rectangle: without a hairline outline, the
     white band of the Italian one would vanish into the pill's light
     background. The outline is done in CSS and not in the SVG, and it is a
     semi-transparent mid grey: a transparent black would be invisible on
     the dark theme, a transparent white on the light one. A grey halfway
     between shows on both, and this CSS serves both variants of all three
     pages.
     box-shadow inset and not border: a border would push the SVG's
     contents inwards, narrowing the bands by a pixel a side; the inner
     shadow paints on top without touching the drawing. */
  .lang-flag {
    display: block;
    flex-shrink: 0;
    border-radius: 2px;
    box-shadow: inset 0 0 0 1px rgba(128, 128, 128, 0.45);
  }
  .lang-caret {
    font-size: 9px;
    color: var(--text-muted);
    transition: transform 0.18s ease;
  }
  .lang-combo.open .lang-caret { transform: rotate(180deg); }
  /* L'elenco si apre ancorato al bordo DESTRO del bottone, perche' la combo
     sta all'estremita' destra dell'intestazione: ancorandolo a sinistra
     uscirebbe dallo schermo.
     [EN] The list opens anchored to the button's RIGHT edge, because the
     combo sits at the far right of the header: anchored left it would run
     off the screen. */
  .lang-menu {
    position: absolute;
    top: calc(100% + 6px);
    right: 0;
    min-width: 100%;
    display: flex;
    flex-direction: column;
    gap: 2px;
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 4px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    z-index: 300;
  }
  .lang-menu[hidden] { display: none; }
  .lang-option {
    display: flex;
    align-items: center;
    gap: 7px;
    font-family: inherit;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-secondary);
    background: none;
    border: 0;
    border-radius: 7px;
    padding: 6px 10px;
    cursor: pointer;
    white-space: nowrap;
    text-align: left;
  }
  /* --gridline e non una tinta d'accento: e' l'unica variabile di sfondo
     tenue definita da tutte e tre le pagine, e questo CSS le serve tutte.
     [EN] --gridline and not an accent tint: it is the only soft background
     variable defined by all three pages, and this CSS serves all three. */
  .lang-option:hover {
    background: var(--gridline);
    color: var(--text-primary);
  }
  .lang-option[aria-selected="true"] { color: var(--text-primary); }
  .lang-option:focus-visible {
    outline: 2px solid var(--series-1);
    outline-offset: -2px;
  }
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

  /* L'intestazione agganciata in cima resta IDENTICA a quella ferma: due
     righe, logo con sottotitolo, data, lingua e schede tutti al loro posto.
     Prima si stringeva su una riga sola appena la pagina si muoveva. Serviva
     a recuperare spazio verticale su una pagina che esiste per leggere una
     tabella lunga, ma il prezzo era che l'intestazione cambiava forma sotto
     gli occhi mentre si scorreva -- e il suo contenuto si spostava di
     conseguenza. Adesso non cambia: quel che si vede fermi e' quel che si
     vede scorrendo.
     Il costo dichiarato: sulla dashboard l'intestazione, sommata alla
     colonna dei filtri agganciata, occupa mentre si scorre lo spazio che
     occupa da ferma.
     [EN] The header pinned to the top stays IDENTICAL to the one at rest:
     two rows, logo with subtitle, date, language and tabs all in place.
     It used to tighten onto a single row as soon as the page moved. That
     bought back vertical space on a page that exists to read a long table,
     but the price was that the header changed shape under your eyes while
     scrolling -- and its contents moved accordingly. Now it does not
     change: what you see at rest is what you see while scrolling.
     The stated cost: on the dashboard the header, added to the pinned
     filters column, takes up while scrolling the room it takes up at rest.
  */
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
  /* Varco anti-lampeggio della traduzione. La classe la mette lo script
     nell'<head> (I18N_BOOT) e la toglie quello che applica le traduzioni
     (I18N_APPLY), che gira poco piu' avanti nella pagina: nel mezzo il
     corpo resta invisibile, cosi' chi ha il browser in inglese non vede
     un lampo di italiano prima dello scambio.
     Quasi tutta la pagina sarebbe gia' coperta dalla rivelazione allo
     scorrimento qui sotto (nasce a opacita' zero); questa regola serve ai
     pochi blocchi che non hanno data-reveal e nascerebbero visibili.
     visibility e non display: lo spazio resta occupato, quindi non c'e'
     nessun salto di impaginazione quando il corpo ricompare.
     La classe viene messa SOLO se il dizionario si e' caricato davvero, e
     tolta in un finally: nessuna combinazione di errori puo' lasciare la
     pagina vuota per sempre.
     [EN] Anti-flash gate for the translation. The class is set by the
     script in the <head> (I18N_BOOT) and removed by the one applying the
     translations (I18N_APPLY), which runs slightly further down the page:
     in between the body stays invisible, so someone with an English
     browser does not see a flash of Italian before the swap.
     Almost all of the page would already be covered by the reveal-on-
     scroll below (it is born at zero opacity); this rule serves the few
     blocks that have no data-reveal and would be born visible.
     visibility and not display: the space stays occupied, so there is no
     layout jump when the body comes back.
     The class is set ONLY if the dictionary actually loaded, and removed
     in a finally: no combination of errors can leave the page blank
     forever. */
  html.i18n-pending body { visibility: hidden; }

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
    .lang-trigger { transition: none; }
    .lang-caret { transition: none; }
  }
"""

# NAV_ITEMS e' una LISTA di dizionari: un elemento per ciascuna voce di
# menu della barra di navigazione, nell'ordine in cui appaiono in pagina.
# "id" e' usato solo internamente (per capire qual e' la voce "attiva",
# vedi render_header sotto), "href" e' il link vero, "label" il testo
# mostrato, "icon" l'SVG dell'iconcina incollato cosi' com'e' nell'HTML.
# "key" e' la chiave con cui il testo viene tradotto a runtime: "label"
# resta l'italiano scritto nell'HTML, che e' quello che si vede se il
# dizionario non si carica o se JavaScript e' spento.
# [EN] NAV_ITEMS is a LIST of dictionaries: one element per menu item of
# the navigation bar, in the order they appear on the page.
# "id" is used only internally (to figure out which item is "active",
# see render_header below), "href" is the actual link, "label" the text
# shown, "icon" the SVG of the small icon pasted as-is into the HTML.
# "key" is the key the text is translated with at runtime: "label" stays
# the Italian written into the HTML, which is what one sees if the
# dictionary fails to load or if JavaScript is off.
NAV_ITEMS = [
    {
        "id": "dashboard",
        "key": "nav.dashboard",
        "href": "dashboard.html",
        "label": "Dashboard",
        "icon": '<svg class="nav-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9"></rect><rect x="14" y="3" width="7" height="5"></rect><rect x="14" y="12" width="7" height="9"></rect><rect x="3" y="16" width="7" height="5"></rect></svg>',
    },
    {
        "id": "pricing",
        "key": "nav.pricing",
        "href": "pricing.html",
        "label": "Tariffario",
        "icon": '<svg class="nav-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg>',
    },
    {
        "id": "guide",
        "key": "nav.guide",
        # Unica voce con un collegamento che cambia con la lingua: la
        # guida esiste in due file, uno per lingua (vedi config.py).
        # [EN] The only entry whose link changes with the language: the
        # guide exists as two files, one per language (see config.py).
        "hrefKey": "nav.guideHref",
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
  /* L'ora si scrive due volte in due modi, e si prende il primo che
     riesce: l'istante formattato nella lingua attiva, oppure -- se il
     dizionario non si e' caricato e fmtGeneratedAt non esiste -- il testo
     italiano gia' pronto che main.py scrive comunque. Senza questo
     ripiego, un dizionario mancante lascerebbe uno spazio vuoto accanto al
     pallino verde, che e' peggio di una data nella lingua sbagliata.
     [EN] The time is written twice in two ways, and the first that works
     wins: the instant formatted in the active language, or -- if the
     dictionary did not load and fmtGeneratedAt does not exist -- the
     ready-made Italian text main.py writes anyway. Without this fallback,
     a missing dictionary would leave a blank next to the green dot, which
     is worse than a date in the wrong language. */
  (function () {
    var el = document.getElementById('meta-timestamp');
    if (!el) return;
    if (typeof GENERATED_AT_ISO !== 'undefined' &&
        typeof window.fmtGeneratedAt === 'function') {
      var text = window.fmtGeneratedAt(GENERATED_AT_ISO);
      if (text) { el.textContent = text; return; }
    }
    if (typeof GENERATED_AT !== 'undefined') el.textContent = GENERATED_AT;
  })();
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
        # Se questa voce ha un collegamento che cambia con la lingua, la
        # si marca perche' la passata di traduzione lo riscriva. L'href
        # scritto nell'HTML resta quello italiano, ed e' quello che si
        # segue se il dizionario non si carica: un collegamento rotto
        # sarebbe una degradazione peggiore di un collegamento in
        # un'altra lingua.
        # [EN] If this entry has a link that changes with the language,
        # we mark it so the translation pass rewrites it. The href
        # written into the HTML stays the Italian one, and that is the
        # one followed if the dictionary does not load: a broken link
        # would be a worse degradation than a link in another language.
        href_attr = ""
        if item.get("hrefKey"):
            href_attr = f' data-i18n-href="{item["hrefKey"]}"'

        tabs_html.append(
            f'      <a href="{item["href"]}"{href_attr} class="nav-tab{active_cls}"{aria_current}>\n'
            f'        {item["icon"]}\n'
            f'        <span class="nav-text" data-i18n="{item["key"]}">{item["label"]}</span>\n'
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
            ' data-i18n-title="header.refreshTitle"'
            ' title="Ricarica i dati conservando i filtri scelti">'
            '<svg class="refresh-icon" width="13" height="13" viewBox="0 0 24 24" fill="none"'
            ' stroke="currentColor" stroke-width="2.2" stroke-linecap="round"'
            ' stroke-linejoin="round" aria-hidden="true">'
            '<path d="M21 12a9 9 0 1 1-2.64-6.36"></path>'
            '<polyline points="21 3 21 9 15 9"></polyline>'
            "</svg>"
            '<span data-i18n="header.refresh">Aggiorna</span></button>'
        )

    # La scelta della lingua, costruita SCORRENDO IL REGISTRO invece di
    # essere scritta a mano. E' la differenza fra una fattorizzazione vera e
    # una a meta': con le voci scritte a mano, aggiungere una lingua
    # costringerebbe comunque a tornare qui, e il registro in i18n.py
    # sarebbe solo meta' della verita'.
    #
    # Ogni voce porta la bandiera e il nome della lingua nella lingua stessa
    # ("Italiano", non "Italian"). I due insieme e non la bandiera da sola:
    # una bandiera indica un paese, e una lingua non appartiene a un paese
    # solo -- aiuta a trovare la voce con la coda dell'occhio, ma e' il nome
    # a dire quale sia. Il nome non passa da tr(): resta "Italiano" anche
    # mentre la pagina e' in inglese, altrimenti chi cerca la propria lingua
    # leggerebbe il nome che le da' un'altra.
    #
    # lang="xx" su ciascuna voce serve a chi usa un lettore di schermo: dice
    # al sintetizzatore vocale di pronunciare quella parola con la fonetica
    # della sua lingua, invece di leggere "English" all'italiana.
    # I ruoli listbox/option dicono che questa e' una scelta fra alternative
    # e non una fila di bottoni qualsiasi. aria-selected nasce "false" su
    # tutte e viene acceso a runtime da I18N_APPLY, che riempie anche il
    # bottone: quale lingua sia attiva qui non si sa ancora, e cuocerlo
    # nell'HTML vorrebbe dire generare pagine diverse per ogni lingua.
    # [EN] The language choice, built by WALKING THE REGISTRY instead of
    # being written out by hand. It is the difference between a real
    # factorisation and a half one: with the entries written by hand, adding
    # a language would still force a return here, and the registry in
    # i18n.py would be only half the truth.
    #
    # Every entry carries the flag and the language's name in that language
    # ("Italiano", not "Italian"). The two together and not the flag alone:
    # a flag denotes a country, and a language does not belong to a single
    # country -- it helps to spot the entry out of the corner of the eye,
    # but it is the name that says which one it is. The name does not go
    # through tr(): it stays "Italiano" even while the page is in English,
    # otherwise someone looking for their own language would read the name
    # another language gives it.
    #
    # lang="xx" on each entry serves screen-reader users: it tells the
    # speech synthesiser to pronounce that word with its own language's
    # phonetics, instead of reading "English" the Italian way.
    # The listbox/option roles say this is a choice among alternatives and
    # not just a row of buttons. aria-selected is born "false" on all of
    # them and is lit at runtime by I18N_APPLY, which also fills the button:
    # which language is active is not known here yet, and baking it into the
    # HTML would mean generating different pages per language.
    lang_options = "".join(
        f'<button type="button" role="option" class="lang-option"'
        f' data-lang="{code}" lang="{code}" aria-selected="false">'
        f"{i18n.FLAGS[code]}"
        f'<span class="lang-name">{i18n.ENDONYMS[code]}</span>'
        "</button>"
        for code in i18n.LANGS
    )
    lang_html = (
        '<div class="lang-combo" id="lang-combo">'
        '<button type="button" class="lang-trigger" id="lang-trigger"'
        ' aria-haspopup="listbox" aria-expanded="false"'
        ' data-i18n-aria-label="header.langSwitch"'
        ' aria-label="Lingua della pagina">'
        '<span class="lang-current"></span>'
        '<span class="lang-caret" aria-hidden="true">&#9662;</span>'
        "</button>"
        '<div class="lang-menu" id="lang-menu" role="listbox"'
        ' data-i18n-aria-label="header.langSwitch"'
        ' aria-label="Lingua della pagina" hidden>'
        f"{lang_options}</div></div>"
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
          <span class="brand-tag" data-i18n="header.brandTag">Monitoraggio Token &amp; Costi</span>
        </div>
      </div>
      <div class="site-header-meta">
        <div class="meta-status" id="meta-status" data-i18n-title="header.updatedTitle" title="Data e ora dell'ultimo aggiornamento">
          <span class="status-indicator" aria-hidden="true"></span>
          <span class="meta-label" data-i18n="header.updated">Aggiornato</span>
          <span class="meta-timestamp" id="meta-timestamp"></span>
        </div>{refresh_html}
      </div>
      {lang_html}
    </div>
    <nav class="site-nav" data-i18n-aria-label="header.nav" aria-label="Navigazione principale">
      <div class="nav-tabs">
{tabs_block}
      </div>
    </nav>
  </header>
{HEADER_SCRIPT}"""


# I due frammenti JavaScript della traduzione. Sono divisi in due, e per
# la stessa ragione per cui lo sono REVEAL_BOOT e REVEAL_JS qui sotto: il
# primo deve girare PRIMA che il browser disegni qualcosa, il secondo ha
# bisogno che il markup esista gia'.
#
# I18N_BOOT (segnaposto __I18N_BOOT__, nell'<head>) carica il dizionario,
# sceglie la lingua e pubblica gli attrezzi che tutto il resto usera':
# LANG, FMT, t() e switchLanguage(). Nient'altro: al momento in cui gira
# il corpo della pagina non esiste ancora.
#
# I18N_APPLY (segnaposto __I18N_APPLY__) fa la passata vera e propria
# sugli attributi data-i18n*, accende il bottone della lingua attiva e
# toglie il varco anti-lampeggio.
#
# DOVE VA MESSO I18N_APPLY, E PERCHE' E' IMPORTANTE. Va incollato subito
# PRIMA dello <script src> dei dati (dashboard-data.js), non in fondo alla
# pagina e non dentro un DOMContentLoaded. E' uno script classico, quindi
# bloccante: quando gira, tutto il markup che lo precede esiste gia' (ed e'
# tutto quello che c'e' da tradurre), ma il file dei dati -- che pesa
# megabyte -- non e' ancora stato chiesto. Aspettare DOMContentLoaded
# significherebbe tenere il corpo invisibile finche' quei megabyte non
# sono stati letti e interpretati: secondi di pagina bianca.
# C'e' un secondo motivo, meno ovvio: la dashboard posiziona gli
# indicatori scorrevoli dei suoi controlli segmentati misurando la
# larghezza dei bottoni, una sola volta, quando li collega. Se le
# etichette venissero tradotte DOPO quel momento, gli indicatori
# resterebbero misurati sul testo italiano e storti fino al primo
# ridimensionamento della finestra. Girando qui, le etichette sono gia'
# quelle giuste quando il collegamento avviene. L'ordine e' portante:
# spostare questo script piu' in basso romperebbe due cose insieme.
#
# [EN] The two JavaScript fragments of the translation. They are split in
# two, and for the same reason REVEAL_BOOT and REVEAL_JS below are: the
# first must run BEFORE the browser paints anything, the second needs the
# markup to already exist.
#
# I18N_BOOT (placeholder __I18N_BOOT__, in the <head>) loads the
# dictionary, chooses the language and publishes the tools everything else
# will use: LANG, FMT, t() and switchLanguage(). Nothing else: at the
# moment it runs, the page body does not exist yet.
#
# I18N_APPLY (placeholder __I18N_APPLY__) does the actual pass over the
# data-i18n* attributes, lights up the active language button and removes
# the anti-flash gate.
#
# WHERE I18N_APPLY GOES, AND WHY IT MATTERS. It is pasted right BEFORE the
# data <script src> (dashboard-data.js), not at the bottom of the page and
# not inside a DOMContentLoaded. It is a classic script, therefore
# blocking: when it runs, all the markup preceding it already exists (and
# that is all there is to translate), but the data file -- weighing
# megabytes -- has not been requested yet. Waiting for DOMContentLoaded
# would mean keeping the body invisible until those megabytes have been
# read and parsed: seconds of blank page.
# There is a second, less obvious reason: the dashboard positions the
# sliding indicators of its segmented controls by measuring the buttons'
# width, once, when it wires them. If the labels were translated AFTER
# that moment, the indicators would stay measured against the Italian text
# and sit crooked until the first window resize. Running here, the labels
# are already the right ones when the wiring happens. The order is
# load-bearing: moving this script further down would break two things at
# once.
I18N_BOOT = r"""  <script src="site-i18n.js"></script>
  <script>
  (function () {
    /* Se il dizionario non si e' caricato non si fa NIENTE: niente varco
       anti-lampeggio, niente traduzione. Il markup delle pagine porta il
       testo italiano scritto dentro, quindi la degradazione e' una pagina
       in italiano perfettamente leggibile -- molto meglio di una pagina
       piena di nomi di chiave, e infinitamente meglio di una pagina
       bianca in attesa di uno scambio che non arrivera'.
       [EN] If the dictionary did not load we do NOTHING: no anti-flash
       gate, no translation. The pages' markup carries the Italian text
       written inside, so the degradation is a perfectly readable Italian
       page -- much better than a page full of key names, and infinitely
       better than a blank page waiting for a swap that will never come. */
    if (typeof I18N === 'undefined' || !I18N.strings) return;

    var LIST = I18N.langs || [];

    /* La lingua si sceglie in tre mosse, dalla piu' esplicita alla piu'
       generica: la scelta gia' fatta con lo switch, la lingua del
       browser, il ripiego. Una scelta esplicita vince SEMPRE su quello
       che dice il browser -- e' il senso stesso di avere uno switch.
       navigator.languages e non solo navigator.language: e' la lista
       ordinata delle preferenze, e chi ha l'inglese come seconda scelta
       preferisce l'inglese al ripiego.
       [EN] The language is chosen in three moves, from the most explicit
       to the most generic: the choice already made with the switch, the
       browser language, the fallback. An explicit choice ALWAYS wins over
       what the browser says -- that is the very point of having a switch.
       navigator.languages and not just navigator.language: it is the
       ordered list of preferences, and someone with English as a second
       choice prefers English to the fallback. */
    function pick() {
      var stored = null;
      /* localStorage puo' sollevare un'eccezione (modalita' privata,
         cookie di terze parti bloccati): senza try/catch un browser
         configurato cosi' resterebbe senza traduzione del tutto.
         [EN] localStorage can throw (private mode, blocked third-party
         cookies): without try/catch a browser configured that way would
         end up with no translation at all. */
      try { stored = localStorage.getItem('dashboardLang'); } catch (e) {}
      if (stored && LIST.indexOf(stored) >= 0) return stored;

      var tags = [];
      if (navigator.languages && navigator.languages.length) {
        tags = tags.concat([].slice.call(navigator.languages));
      }
      if (navigator.language) tags.push(navigator.language);
      for (var i = 0; i < tags.length; i++) {
        /* "it-IT" e "en_US.UTF-8" cominciano entrambi con le due lettere
           che ci interessano: si taglia al primo separatore.
           [EN] "it-IT" and "en_US.UTF-8" both start with the two letters
           we care about: cut at the first separator. */
        var code = String(tags[i]).toLowerCase().split(/[-_.]/)[0];
        if (LIST.indexOf(code) >= 0) return code;
      }
      return I18N.fallback;
    }

    var LANG = pick();
    var DICT = I18N.strings[LANG] || {};

    window.LANG = LANG;
    window.FMT = I18N.fmt[LANG] || {};

    /* tr('sezione.chiave') restituisce il testo tradotto.

       Si chiama tr e non t perche' in dashboard.html "t" e' gia' il nome
       della variabile "turno" in una trentina di callback: un traduttore
       chiamato t sarebbe irraggiungibile proprio dentro le funzioni che
       disegnano le righe della tabella, e chi ci provasse otterrebbe un
       "t is not a function" invece di una traduzione.
       [EN] It is called tr and not t because in dashboard.html "t" is
       already the name of the "turn" variable in some thirty callbacks: a
       translator called t would be unreachable precisely inside the
       functions that draw the table rows, and whoever tried would get a
       "t is not a function" instead of a translation.
       Il secondo argomento e' opzionale e ha due forme: un NUMERO, per le
       chiavi che hanno singolare e plurale (finisce anche in {n}), oppure
       un OGGETTO di valori da mettere nei segnaposto {cosi'}.
       Una chiave che non esiste torna indietro come chiave: un
       "chart.avgOthers" ben visibile in pagina e' una segnalazione che
       chiunque riconosce, mentre un ripiego silenzioso sull'italiano
       sarebbe un errore che viene spedito senza che nessuno se ne accorga.
       Il perche' di tutto questo, per esteso, e' nel docstring di i18n.py.
       [EN] tr('section.key') returns the translated text.
       The second argument is optional and has two shapes: a NUMBER, for
       keys having a singular and a plural (it also lands in {n}), or an
       OBJECT of values to put into the {like_this} placeholders.
       A key that does not exist comes back as the key: a plainly visible
       "chart.avgOthers" on the page is a report anyone recognises, whereas
       a silent fallback to Italian would be a bug that ships unnoticed.
       The full reasoning is in i18n.py's docstring. */
    /* La ricerca di una chiave, in una lingua qualsiasi. Sta fuori da tr()
       perche' serve anche a switchLanguage, che deve leggere il dizionario
       della lingua verso cui si sta andando, non di quella attuale.
       [EN] Key lookup, in any language. It lives outside tr() because
       switchLanguage needs it too: that one has to read the dictionary of
       the language being switched TO, not the current one. */
    function lookup(lang, key) {
      var node = I18N.strings[lang];
      var parts = key.split('.');
      for (var i = 0; i < parts.length; i++) {
        if (!node || typeof node !== 'object' || !(parts[i] in node)) return null;
        node = node[parts[i]];
      }
      return node;
    }

    window.tr = function (key, arg) {
      var node = lookup(LANG, key);
      if (node === null) return key;
      if (node && typeof node === 'object') {
        /* Chiave a due forme senza il numero per sceglierle: si torna
           indietro con la chiave invece di tirare a indovinare.
           [EN] Two-form key without the number to choose between them: we
           come back with the key instead of guessing. */
        if (typeof arg !== 'number') return key;
        node = (arg === 1) ? node.one : node.other;
      }
      if (typeof node !== 'string') return key;
      var values = (typeof arg === 'number') ? { n: arg } : (arg || {});
      /* Un segnaposto senza valore resta scritto com'e': si vede cosa
         manca, invece di ritrovarsi un "undefined" in mezzo alla frase.
         [EN] A placeholder with no value stays written as it is: you see
         what is missing, instead of finding an "undefined" mid-sentence. */
      return node.replace(/\{(\w+)\}/g, function (whole, name) {
        return (name in values) ? values[name] : whole;
      });
    };

    /* Cambiare lingua ricarica la pagina. Non e' una rinuncia: e' la
       scelta descritta al punto 3 del docstring di i18n.py, e riusa il
       meccanismo che la dashboard ha gia' per i propri ricaricamenti di
       servizio -- si salvano i filtri, si salta l'animazione d'entrata,
       si ricarica. La dashboard pubblica __saveStateForReload; le altre
       due pagine non hanno stato da conservare e semplicemente non lo
       definiscono, quindi qui non serve nessun caso speciale per pagina.
       [EN] Changing language reloads the page. Not a concession: it is
       the choice described at point 3 of i18n.py's docstring, and it
       reuses the mechanism the dashboard already has for its own service
       reloads -- save the filters, skip the entrance animation, reload.
       The dashboard publishes __saveStateForReload; the other two pages
       have no state to preserve and simply do not define it, so no
       per-page special case is needed here. */
    window.switchLanguage = function (next) {
      if (next === LANG || LIST.indexOf(next) < 0) return;
      /* Quasi tutte le pagine esistono in un file solo e si traducono
         ricaricandosi. La guida no: e' prosa lunga e vive in un file per
         lingua, quindi ricaricare lo stesso file darebbe testo inglese
         dentro una cornice italiana. Una pagina cosi' lo dichiara scrivendo
         sull'elemento <html> la chiave che contiene il proprio indirizzo, e
         qui si va a leggerla nel dizionario della lingua di destinazione.
         Non e' un caso speciale per la guida: e' un meccanismo che vale per
         qualunque pagina futura che nasca in piu' file.
         [EN] Almost every page exists as a single file and translates
         itself by reloading. The guide does not: it is long prose and lives
         as one file per language, so reloading the same file would give
         English text inside an Italian frame. Such a page declares itself
         by writing on the <html> element the key holding its own address,
         and here we read that key in the destination language's dictionary.
         It is not a special case for the guide: it is a mechanism serving
         any future page born as several files. */
      var pageKey = document.documentElement.getAttribute('data-page-href');
      var target = pageKey ? lookup(next, pageKey) : null;
      try {
        localStorage.setItem('dashboardLang', next);
        sessionStorage.setItem('skipPageIntro', '1');
        /* Dopo il ricaricamento il fuoco deve tornare sullo switch: chi
           naviga da tastiera lo ha appena premuto, e ritrovarsi il fuoco
           in cima al documento vorrebbe dire rifare tutta la strada.
           [EN] After the reload the focus must return to the switch:
           whoever navigates by keyboard has just pressed it, and finding
           the focus back at the top of the document would mean walking
           the whole way again. */
        sessionStorage.setItem('focusAfterLangSwitch', '1');
      } catch (e) {}
      if (typeof window.__saveStateForReload === 'function') {
        try { window.__saveStateForReload(); } catch (e) {}
      }
      if (typeof target === 'string' && target) {
        location.assign(target);
      } else {
        location.reload();
      }
    };

    /* L'ora di generazione, scritta nella lingua attiva e nel fuso di chi
       guarda. new Date() su un istante ISO fa la conversione di fuso da
       sola, per qualunque fuso e con le regole giuste: e' il motivo per
       cui il fuso NON segue la lingua, ma il computer di chi legge (vedi
       il punto 6 nel docstring di i18n.py).
       La forma e' la stessa nelle due lingue -- "25 ago 2026, 10:40" e
       "25 Aug 2026, 10:40" -- quindi cambia solo la tabella dei mesi, che
       arriva dal profilo di formattazione.
       [EN] The generation time, written in the active language and in the
       viewer's time zone. new Date() on an ISO instant does the zone
       conversion by itself, for any zone and with the right rules: it is
       why the zone does NOT follow the language, but the reader's computer
       (see point 6 in i18n.py's docstring).
       The shape is the same in both languages -- "25 ago 2026, 10:40" and
       "25 Aug 2026, 10:40" -- so only the month table changes, and that
       comes from the formatting profile. */
    window.fmtGeneratedAt = function (iso) {
      var d = new Date(iso);
      /* Un istante che il browser non sa leggere non deve buttare giu'
         tutto: si restituisce vuoto e chi chiama ripiega.
         [EN] An instant the browser cannot read must not bring everything
         down: we return empty and the caller falls back. */
      if (isNaN(d.getTime())) return '';
      var months = window.FMT.monthsShort || [];
      function pad(n) { return (n < 10 ? '0' : '') + n; }
      return d.getDate() + ' ' + months[d.getMonth()] + ' ' + d.getFullYear() +
             ', ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
    };

    document.documentElement.lang = LANG;
    document.documentElement.classList.add('i18n-pending');
  })();
  </script>"""

# Vedi il commento sopra I18N_BOOT per il perche' di questa divisione in
# due e, soprattutto, per il perche' della POSIZIONE di questo secondo
# frammento nella pagina.
# [EN] See the comment above I18N_BOOT for why this is split in two and,
# above all, for why this second fragment sits where it sits in the page.
I18N_APPLY = r"""  <script>
  (function () {
    var root = document.documentElement;
    try {
      if (typeof window.tr !== 'function') return;

      /* Gli attributi che non sono testo visibile. Una tabella e non una
         catena di if: aggiungere un attributo traducibile e' una riga qui,
         e il ciclo sotto non cambia.
         [EN] The attributes that are not visible text. A table and not a
         chain of ifs: adding a translatable attribute is one line here,
         and the loop below does not change. */
      var ATTRS = {
        'data-i18n-title': 'title',
        'data-i18n-aria-label': 'aria-label',
        'data-i18n-placeholder': 'placeholder',
        'data-i18n-href': 'href'
      };

      var els, i;

      /* textContent e non innerHTML: il testo tradotto viene messo cosi'
         com'e', quindi una traduzione non puo' mai iniettare markup per
         sbaglio. Funziona anche sul <title> della scheda.
         [EN] textContent and not innerHTML: the translated text is put in
         as-is, so a translation can never inject markup by accident. It
         works on the tab <title> too. */
      els = document.querySelectorAll('[data-i18n]');
      for (i = 0; i < els.length; i++) {
        els[i].textContent = tr(els[i].getAttribute('data-i18n'));
      }

      /* L'eccezione: le poche stringhe che contengono markup (un <code>,
         un <strong>). Stanno sotto un attributo diverso proprio perche' si
         veda a colpo d'occhio, leggendo il markup, quali sono.
         [EN] The exception: the few strings containing markup (a <code>, a
         <strong>). They sit under a different attribute precisely so that
         one can see at a glance, reading the markup, which ones they are. */
      els = document.querySelectorAll('[data-i18n-html]');
      for (i = 0; i < els.length; i++) {
        els[i].innerHTML = tr(els[i].getAttribute('data-i18n-html'));
      }

      for (var data in ATTRS) {
        if (!Object.prototype.hasOwnProperty.call(ATTRS, data)) continue;
        els = document.querySelectorAll('[' + data + ']');
        for (i = 0; i < els.length; i++) {
          els[i].setAttribute(ATTRS[data], tr(els[i].getAttribute(data)));
        }
      }

      /* La combo della lingua: si marca la voce attiva, la si copia dentro
         il bottone che apre, e si collegano apertura, scelta e chiusura.
         aria-selected viene messo qui e non nell'HTML generato perche'
         quale lingua sia attiva si sa solo adesso: cuocerlo nel markup
         vorrebbe dire generare tre pagine diverse per ogni lingua, che e'
         esattamente cio' che questo disegno evita.
         [EN] The language combo: mark the active entry, copy it into the
         button that opens the list, and wire opening, choosing and
         closing. aria-selected is set here and not in the generated HTML
         because which language is active is known only now: baking it into
         the markup would mean generating three different pages per
         language, which is exactly what this design avoids. */
      var restore = false;
      try {
        restore = !!sessionStorage.getItem('focusAfterLangSwitch');
        if (restore) sessionStorage.removeItem('focusAfterLangSwitch');
      } catch (e) {}

      var combo = document.getElementById('lang-combo');
      var current = null;
      if (combo) {
        var trigger = document.getElementById('lang-trigger');
        var menu = document.getElementById('lang-menu');
        var options = menu.querySelectorAll('.lang-option[data-lang]');
        var attiva = null;

        for (i = 0; i < options.length; i++) {
          (function (opt) {
            var active = opt.getAttribute('data-lang') === window.LANG;
            opt.setAttribute('aria-selected', active ? 'true' : 'false');
            if (active) attiva = opt;
            opt.addEventListener('click', function () {
              switchLanguage(opt.getAttribute('data-lang'));
            });
          })(options[i]);
        }

        /* Il bottone mostra la voce attiva copiandone il contenuto invece
           di ricostruirlo: bandiera e nome sono gia' nel documento,
           generati una volta sola da render_header, e una seconda copia
           sarebbe una seconda cosa da tenere allineata alla prima.
           [EN] The button shows the active entry by copying its content
           rather than rebuilding it: flag and name are already in the
           document, generated once by render_header, and a second copy
           would be a second thing to keep in step with the first. */
        if (attiva) {
          trigger.querySelector('.lang-current').innerHTML = attiva.innerHTML;
        }
        current = trigger;

        function apri(si) {
          combo.classList.toggle('open', si);
          menu.hidden = !si;
          trigger.setAttribute('aria-expanded', si ? 'true' : 'false');
        }

        trigger.addEventListener('click', function (e) {
          /* Senza fermare l'evento, il click che apre l'elenco arriverebbe
             subito dopo al documento, che lo leggerebbe come "click fuori"
             e lo richiuderebbe all'istante.
             [EN] Without stopping the event, the click that opens the list
             would immediately reach the document, which would read it as a
             "click outside" and close it again at once. */
          e.stopPropagation();
          apri(menu.hidden);
        });

        document.addEventListener('click', function (e) {
          if (!menu.hidden && !combo.contains(e.target)) apri(false);
        });

        /* Esc chiude e riporta il fuoco sul bottone: chi ha aperto l'elenco
           da tastiera deve ritrovarsi dov'era, non in cima al documento.
           [EN] Esc closes and returns focus to the button: whoever opened
           the list from the keyboard must end up where they were, not at
           the top of the document. */
        document.addEventListener('keydown', function (e) {
          if (e.key === 'Escape' && !menu.hidden) {
            apri(false);
            trigger.focus();
          }
        });
      }

      /* Il fuoco e' l'unica cosa qui dentro che NON va fatta subito.
         Questo script gira mentre il parser sta ancora leggendo la pagina,
         e un focus() dato in quel momento viene perso: a fine caricamento
         il browser riporta il fuoco su <body>, e chi era arrivato allo
         switch da tastiera se lo ritroverebbe in cima al documento --
         esattamente il disagio che questo pezzo vuole evitare.
         Le traduzioni, al contrario, devono restare qui e non possono
         aspettare (il perche' e' nel commento sopra I18N_BOOT): quindi le
         due cose si separano, ognuna nel momento che le serve.
         [EN] Focus is the only thing in here that must NOT be done right
         away. This script runs while the parser is still reading the page,
         and a focus() given at that moment is lost: at the end of loading
         the browser puts focus back on <body>, and whoever reached the
         switch by keyboard would find it back at the top of the document
         -- exactly the nuisance this piece is meant to avoid.
         The translations, on the contrary, must stay here and cannot wait
         (why is in the comment above I18N_BOOT): so the two are separated,
         each at the moment it needs. */
      if (restore && current) {
        if (document.readyState === 'loading') {
          document.addEventListener('DOMContentLoaded', function () {
            current.focus();
          });
        } else {
          current.focus();
        }
      }
    } finally {
      /* In un finally, sempre: qualunque errore capiti qui sopra, il corpo
         della pagina torna visibile. Una traduzione incompleta e' un
         difetto; una pagina che resta bianca per sempre e' un guasto.
         [EN] In a finally, always: whatever error happens above, the page
         body becomes visible again. An incomplete translation is a flaw; a
         page staying blank forever is a failure. */
      root.classList.remove('i18n-pending');
    }
  })();
  </script>"""


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

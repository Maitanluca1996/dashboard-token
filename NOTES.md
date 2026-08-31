# Dashboard Token Usage — Technical and Architectural Specifications / Specifiche Tecniche e Architetturali

## 🇬🇧 English

Static HTML dashboard and hook suite for monitoring Claude Code token consumption and costs. Generation happens entirely locally from the CSV logs recorded on disk, with no external API calls.

---

### 1. Architecture and Paths

#### Component Map
| Component | Default path | Description |
|---|---|---|
| **Generator package** | `~/.claude/hooks/generate_dashboard/` | Aggregation and HTML rendering core |
| **Stop hook** | `~/.claude/hooks/log_tokens.py` | Records per-turn tokens and triggers generation |
| **PostToolUse hook** | `~/.claude/hooks/log_operation.py` | Records individual tool operations |
| **Turn log** | `~/.claude/logs/tokens.csv` | Historical records per conversation turn |
| **Action log** | `~/.claude/logs/operations.csv` | Historical records per individual tool call |
| **Session cache** | `~/.claude/logs/session_titles_cache.json` | On-disk cache of per-session titles and projects |
| **Configuration** | `~/.claude/hooks/dashboard_config.json` | Optional overrides: output folder (`{"out_dir": "..."}`) and app logs (`{"app_log_dir": "..."}`) |
| **Account labels** | `~/.claude/hooks/account_labels.json` | Optional UUID → human-readable label map |
| **Account observations** | `~/.claude/logs/account_osservazioni.json` | Archive of direct account observations, per session (see §7) |
| **Claude app logs** | `%APPDATA%\Claude\logs\main*.log` | Read-only: record of account switches used by the backfill (see §7) |
| **HTML output** | `~/.claude/dashboard-token/` | Generated files: `dashboard.html`, `pricing.html`, `guida-costi.html` |
| **Installer package** | `installer/` | Scripts and files for deployment on other machines |

#### Hook Execution Mechanism
- **Exec form**: the hooks are executed directly by the interpreter (`"command": "python3", "args": [...]` in `~/.claude/settings.json`), without invoking external shells (no dependency on bash or Git for Windows).
- **Synchronous generation**: at the end of each turn, `log_tokens.py` runs `import generate_dashboard; generate_dashboard.main()` in-process to regenerate the HTML pages.
- **Self-contained output**: the generated pages (`dashboard.html`, `pricing.html`, `guida-costi.html`) are fully self-contained (inline CSS and JS) and linked to each other via relative paths.

---

### 2. Structure of the `generate_dashboard/` Package

The generator is organized into dedicated modules:

| Module | Responsibility |
|---|---|
| `config.py` | Input/output path resolution and reading of `dashboard_config.json` |
| `pricing.py` | Price list definition (`MODEL_PRICING`), single source of truth for all pages |
| `timeutils.py` | Italian time zone handling (CET/CEST) with built-in daylight saving time algorithm |
| `numfmt.py` | Italian-style number and currency formatting utilities |
| `data.py` | Parsing and cleaning of data from `tokens.csv` and `operations.csv` |
| `sessions.py` | Extraction and enrichment of session metadata (title, project) with caching |
| `header.py` | Component generating the header, the unified navbar and the shared CSS styles |
| `templating.py` | HTML template loading and placeholder substitution |
| `templates/*.html` | Source templates for the dashboard (`dashboard.html`), the price list (`pricing.html`) and the guide (`guide.html`) |
| `render_dashboard.py` | Aggregation and population logic for `dashboard.html` |
| `render_pricing.py` | Rendering logic for the price table in `pricing.html` |
| `render_guide.py` | Break-even threshold computation and rendering for `guida-costi.html` |
| `main.py` | Entry point (`main()`) orchestrating the update and the writing of the three files |
| `backfill.py` | Retroactive reconstruction of the CSVs from the transcripts of sessions predating the installation (see §7) |

---

### 3. Interface Technical Specifications

#### Shared Header and Navigation Bar
- **Unified component (`header.py`)**: all pages share the same header and navbar, generated programmatically on the Python side (`render_header(active_id, generated_at)`) and injected into the templates via `__SITE_HEADER__` and `__HEADER_CSS__`.
- **Brand & metadata**:
  - Brand logo/icon (`🪙`), title ("Claude Code") and subtitle ("Monitoraggio Token & Costi" — token & cost monitoring; the interface is in Italian).
  - Status pill with a green indicator and a dynamic, Italian-style generation timestamp (`generated_at_now()`).
- **Tabbed navigation bar (`.nav-tabs`)**:
  - Main menu with 3 entries, named as they appear in the Italian interface: **Dashboard** (`dashboard.html`), **Tariffario** (price list, `pricing.html`), **Guida ai costi** (cost guide, `guida-costi.html`).
  - Semantic SVG icons for each menu entry (`currentColor`).
  - Automatic detection and highlighted styling of the active tab (`.nav-tab.active` with `--control-bg` background, dedicated border, shadow and `aria-current="page"`).
  - Smooth hover transitions and keyboard navigation support (`:focus-visible`).
- **Alignment and width**: `.wrap` container with uniform width (`max-width: 900px`) on all pages to prevent visual jumps while navigating.

#### Filter System (`dashboard.html`)
- **Custom dropdown controls**: the dropdown menus (`.custom-dropdown`) wrap a hidden `<select>` element (`display:none`) to preserve the underlying JS logic.
- **Grid layout**: the filter bar (`.filter-row`) adopts a `display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr))` layout to guarantee uniform, responsive sizing.
- **Long text handling**: dropdown triggers truncate overflowing text with an ellipsis (`overflow: hidden; text-overflow: ellipsis`), setting the native `title` attribute for the tooltip; inside the open menu, text wraps up to a maximum of 2 lines (`-webkit-line-clamp: 2`).
- **Data sanitization**: all dynamic values (session titles, account names, projects) are filtered through the `esc()` function before insertion into the DOM.
- **Hierarchy and cascade**:
  - The **Progetto** (project) filter cascades onto the **Sessione** (session) filter: selecting a project regenerates the session list (`populateSelect(proj)`) and resets any no-longer-relevant selections, including while restoring state from `sessionStorage`.
  - The **Periodo** (period) filter pairs the four calendar periods (*Oggi* — today, *Questa settimana* — this week, *Questo mese* — this month, *Quest'anno* — this year, all open-ended going forward) with one entry for each **month actually present in the data**, most recent first, generated at runtime by `addMonthPeriods()`. The current month is omitted because it is already covered by *Questo mese*. These are the only periods that also have an upper bound (`to`), which `filterByPeriod` applies as an exclusive endpoint.
  - The **Account** filter operates in intersection (AND) with the other filters on turns. *(Note: `operations.csv` inherits the project from the session but does not store the account, so the Account filter does not apply to the actions table.)*

#### Charts and Dynamic Controls
- **Segmented control**: the mode and time-range switches use an animated selection indicator (`.indicator`), synchronized via JS (`positionSegmentedIndicator`) on resize and state changes.
- **"Andamento Token" (token trend) chart modes**: handled through the generic `bucketTurns(..., keyFn)` function with four groupings (`CHART_MODES`):
  1. *Per sessione* (by session, `t.sid`)
  2. *Aggregato* (aggregate: global sum on a single line)
  3. *Per modello* (by model, grouped by `modelShortLabel(t.model)`)
  4. *Per progetto* (by project, grouped by `projectOf(t)`, i.e. the session's project)
- **Series selection on the line chart**: `rankGroupsInWindow` ranks the groups by their total **inside the drawn window**, measured with the active unit, and it is that order that `assignGroupColors` receives. The hues therefore land on the series that weigh something, not on the ones that happen to appear first; a deterministic tie-break (earliest appearance, then key comparison) keeps the colors stable across redraws. Past the eighth (`LINE_MAX_SERIES`, tied to the palette length) `collapseTailSeries` merges everything into a **single** series with key `LINE_TAIL_KEY`, summing the buckets of the same interval. The tail is summed, not averaged as in the bar chart: there the tail bar competes in the ranking, here the axis reads "how much was spent in this interval" and the sum of what is left *is* that number. Since no `keyFn` produces the tail, its group tooltip is built by `totalsFromBuckets` and declares "Totale nel periodo mostrato".
- **Scatter on wide windows**: with 24 sampled intervals over months an interval lasts days while a session lasts hours, so almost every session falls into a single bucket and a "line per session" degenerates into isolated dots. `seriesAreDegenerate` measures exactly this — the share of series occupying a single interval — and past one half the *Per sessione* mode (the only one declaring `scatterWhenSparse`) draws one lollipop marker per session instead: planted on its first turn, as tall as the session cost in the window. The criterion is scale-free, so it follows `LINE_CHART_BUCKETS` on its own. In this mode the tail is **not** collapsed: with no polylines involved, gray dots at different heights are information, and summing them would produce the tallest marker on the chart. Three choices make the cloud legible:
  - **Color changes job**: it stops saying *which* session and moves to saying *whose it is* — the project (`rankProjectsOfPoints`, legend borrowed from `CHART_MODES.project`). With few sessions one hue each is a name and the legend reads; with hundreds it is not, and past the eighth there are no distinguishable hues left, so the vast majority of markers would come out the same gray: a channel switched on saying nothing. Projects are few and named, so as a category they work — and isolating one from the legend thins the cloud (the muted targets get `pointer-events: none`) enough to point inside a crowded day with the mouse. This applies to the scatter only: in the line branch sessions are few, and there a hue each *is* a name.
  - **The stem carries "which ones count"**, going to the window's most expensive sessions (`stemmed`, from the session ranking). One channel per variable instead of two meanings on one. A stem for every session would be a picket fence of identical rods, long ones on a log scale, covering exactly the few one must compare; the others stay a smaller, less solid but still clickable dot, with the hit radius narrowed from 6 to 4 units since `r=6` is tuned for a chart where a series has at most twenty-four points, not hundreds.
  - **The SVG box grows** from `LINE_CHART_HEIGHT` = 200 to `LINE_SCATTER_HEIGHT` = 300, because here height is what separates markers sharing the same time slot.
- **Vertical scale** (*Scala* switch, persisted in `sessionStorage`): until the switch has been touched, the chart picks the scale — logarithmic for the scatter, linear for the lines — and moves the control along, so it never says something other than what is drawn. The first click sets `scaleChosenByHand` and the automatism stops for good; a restored value counts as a choice. It is not a guessed preference: a cloud of sessions spans three orders of magnitude and on a linear scale sits entirely glued to the baseline, while a trend over time reads linear. `makeValueAxis` returns the position function and the ticks, so the drawing code does not know which scale is active. In log mode the ticks sit on powers of ten (round labels at a single precision, since `fmtMoneyAxis` derives precision from `scale` for the whole axis), capped at three decades, and zero values rest on the baseline — where the linear axis already puts them, so switching scale that point does not jump.
- **Line chart legend and isolation**: `chartLegendHtml` (formerly `barLegendHtml`) serves both charts; `labelFn` turns the group id into a readable name and `interactive` makes the entries a command. Clicking one isolates its series by toggling two classes on nodes already in the page — no redraw, so pinned tooltip indexes stay valid. Every gray series shares a single `data-series` identifier, so the "altre N" entry lights them all at once.
- **Fills**: the area under the curve survives only with a single series on a linear scale. With several series the areas overlap into an unreadable smudge; on a log scale the area is proportional to nothing. Where the fill is dropped, the wide click target is provided by `.line-hit`, an invisible corridor along the stroke — a better target than the area it replaces, which was clickable across the whole dead band down to the baseline.
- **Bar chart grouping** (`BAR_GROUPS`, the *Raggruppa* — group by — switch): a twin structure of `CHART_MODES` that isolates key, label, ordering and truncation; accumulation, SVG drawing and tooltips remain shared.
  1. *Per giorno* (by day) — chronological order, cap of 14 bars (31 with a period selected).
  2. *Per mese* (by month) — key `monthKey(t.ts)` (local time zone, not the UTC substring), chronological order, cap of 12 bars.
  3. *Per progetto* (by project) — descending order by value **of the active unit** (in tokens the ranking may differ from the dollar one), cap of `BAR_MAX_PROJECTS` = 12; the excess projects are merged into a single trailing *Altri* (others) bar, so the on-screen total remains the real total. Project labels are tilted -30° and truncated at 14 characters (full name in the tooltip); in this mode the SVG viewport grows from 200 to 224 units of height, leaving the plotting area unchanged.
- **Title composition**: `UNIT_MODES` provides only the subject (`barNoun`: *Costo totale* — total cost / *Costo totale in euro* — total cost in euros / *Token totali* — total tokens), to which the active grouping adds the complement (*per giorno* / *per mese* / *per progetto*) and the period in parentheses.
- **Layout stability**: the hint element (`#line-chart-hint`) has a fixed minimum height (`min-height: 36px`) to avoid vertical jumps of the chart as the descriptive text changes.
- **Micro-animations**:
  - Dynamic SVG line tracing via a `stroke-dasharray` / `stroke-dashoffset` transition.
  - Hover elevation animation (`transform: translateY(-3px)`) on the hero stat cards.
  - Nested-actions panel expansion via a `max-height` animation (0 → 2000px) and a 90° rotation of the arrow glyph (`▶`).
  - Automatic disabling of animations and transitions under the `@media (prefers-reduced-motion: reduce)` media query.

#### Stat Cards
- The aggregate statistics strip (`.stat-mini-grid`) is structured with `gap: 1px` and a `--gridline` background, producing compact dividers with no orphan borders under responsive wrapping.
- Copy and descriptions follow a formal, neutral register.

---

### 4. Secondary Page Specifications

#### `pricing.html`
- Lists the active rates for all models supported by `MODEL_PRICING`.
- Model-specific notes are shown on dedicated rows (`<tr class="note-row">`) with full colspan.

#### `guida-costi.html`
- Dynamic guide to optimizing context and output costs.
- **Dynamic computation**: comparison tables, cost multipliers and break-even thresholds (cache vs standard input) are computed at runtime from `MODEL_PRICING` (filtered to the main models in `GUIDE_MODELS`).
- **Conditional blocks**: the promotional info block (`__PROMO_BLOCK__`) appears only if the reference model has active pricing notes.

---

### 5. Distribution and Installer (`installer/`)

The `installer/` folder contains the package for deploying the dashboard on Windows, macOS and Linux environments:

- **Setup scripts**:
  - `install.ps1` / `install.cmd`: setup for Windows.
  - `install.sh`: setup for macOS/Linux environments.
- **Installation logic**:
  - Verifies the presence of a working Python runtime (actually executing `python3 --version`, avoiding false positives from system aliases such as `WindowsApps`). If absent, it offers installation through a package manager (`winget`, `brew`, `apt`, `dnf`, `pacman`).
  - Recursively copies the `generate_dashboard/` package and the `log_tokens.py` and `log_operation.py` hooks into `~/.claude/hooks/`.
  - Configures `~/.claude/settings.json` with an idempotent merge (updates existing hooks identified by the file name in their arguments, preserving any other hooks defined by the user).
- **Development-time synchronization**:
  - The `sync-from-live.ps1` script keeps the `installer/hooks/` folder aligned with `~/.claude/hooks/`.

---

### 6. System Constraints and Implementation Details

1. **UTF-8 BOM handling**: the hooks read standard input as a binary byte stream (`sys.stdin.buffer`), decoding with the `utf-8-sig` codec, preventing JSON parsing errors when a BOM is present.
2. **Output directory creation**: the generator ensures `OUT_DIR` exists beforehand (`os.makedirs(OUT_DIR, exist_ok=True)`) before writing the files.
3. **Dependency-free time computation**: `timeutils.py` implements the algorithmic computation of the Italian time zone and the daylight saving transition (EU rules) to guarantee cross-platform compatibility without external packages such as `tzdata`.
4. **`<select>` DOM manipulation**: the hidden dropdowns are emptied by resetting `select.options.length = 0` to guarantee correct synchronization of the element collection.
5. **Data ordering**: sessions are sorted in reverse chronological order on the Python side before being passed to the template.

---

### 7. Retroactive History Recovery (`backfill.py`)

The hooks only observe what happens **after** installation. The `backfill.py` module fills that gap by reconstructing `tokens.csv` and `operations.csv` from the transcripts Claude Code writes anyway to `~/.claude/projects/<progetto>/<session_id>.jsonl`.

#### The two defects it fixes
| Case | Symptom | Remedy |
|---|---|---|
| Session never seen by the hooks | No rows in the CSVs | Full reconstruction from scratch |
| Session straddling the installation | At the first `Stop` hook, `session_cumulative_state.json` had no prior state, so `compute_turn_delta()` computed the delta starting from zero: **all** of the history ended up in **a single row** dated at installation time. Correct totals, flattened chronology | The row is replaced by the real turns, each with its own date |

#### Reconstruction criteria
- **Turns** (`rebuild_turns`): the turn boundary is the `queue-operation`/`enqueue` entry, the same source used by `extract_summary()` in the hooks — the `summary` field therefore comes out identical to what the hook would have written. Consumption is summed deduplicating by `message.id`, exactly like `sum_transcript_usage()`, because an API call's `usage` is repeated on every block of the message. Timestamp = last response of the turn; model = last non-`<synthetic>`; zero-token turns produce no row.
- **Operations** (`rebuild_ops`): one row per `tool_use`, deduplicating by `(message.id, block.id)` and dividing the message's `usage` by the number of `tool_use` blocks composing it. **Deliberate divergence from the hook**: `attribute_action_cost()` runs during the session and, for multi-block messages, must declare `n/d` (n/a) with zero cost; reading the transcript after the fact removes the ambiguity, so the reconstructed rows also attribute the cost of tools launched in parallel.

#### Account attribution: per turn, not per session
The account **is not a property of the session but of the moment**. On a machine with multiple accounts (in real cases, several switches within the same day are also observed), a session resumed weeks later spans multiple accounts, and attributing a single one to the whole session silently gets it wrong. Each turn therefore receives its own, from the first available source:

| # | Source | Where |
|---|---|---|
| 1 | **Login timeline** — the Claude app explicitly records every account switch with date and time (`[account] Login-state transition ... uuid: X -> Y`) | `%APPDATA%\Claude\logs\main*.log` (Win), `~/Library/Application Support/Claude/logs` (mac), `~/.config/Claude/logs` (Linux); override with `{"app_log_dir": "..."}` in `dashboard_config.json` |
| 2 | **Hook observation** on the same session, valid only **from the observed turn onward** (plus `MARGINE_OSSERVAZIONE`, 5 min, because the `Stop` hook writes a few seconds *after* the end of the turn it refers to) | `origine=hook` rows + `account_osservazioni.json` |
| 3 | **UUID declared by the transcript** (`bridge-session.ownerAccountUuid`), translated with `account_labels.json` | transcript |
| 4 | Fallback `non rilevato` (not detected), distinct from `sconosciuto` (unknown: a live row whose resolution failed) | — |

We **never** guess by using the account logged in at backfill time: a session from months earlier may have belonged to a different one.

**The app logs are in local time**, the CSVs in UTC: the conversion uses `timeutils.from_italy_time()`, the inverse of `to_italy_time()`, with the same hand-computed EU daylight saving rule (no `tzdata`).

**Why not the shell snapshots**: `~/.claude/shell-snapshots/*.sh` contain the UUID inside a `PATH` and carry the epoch in their name, so they look like a usable timeline. They were discarded after validation: Claude Code cleans them up after ~30 days, and their sparsity produces a significant share of errors **concentrated precisely on account switches**. The timeline from the app logs, validated against the rows written by the hooks, left **no residual errors on the available control rows**.

**Known limitation (MSIX)**: if Python runs inside an MSIX container (Microsoft Store / Python Install Manager), `%APPDATA%\Claude` is virtualized and appears *nonexistent* — the same pitfall documented in `log_tokens.account_uuid_candidates()`. The packaged application (a normal Windows process) is unaffected; those running the sources by hand use `app_log_dir`.

#### Consumption nobody was counting
- **Sub-agents** (`find_subagents`): the Task/Agent tool writes the sub-agent's conversation to a separate file, `projects/<progetto>/<session_id>/subagents/*.jsonl`. Not being in the main transcript, it was counted **neither by the backfill nor by the `Stop` hook**: in real cases it is a huge share of consumption, with individual sessions underestimated by more than half. Now `sum_transcript_usage()` and `_rebuild_turns()` also read those files, with a single `message.id` dedup set shared among all of them. The sub-agent's consumption is assigned to the parent session's turn during which it was launched, by timestamp comparison (binary search over turn end times).
- **Occurrences of the same `message.id` with different `usage`**: a message's blocks repeat the `usage`, which is why deduplication exists — but they do not always repeat it *identically*: on real messages, `output_tokens` can be seen growing from one occurrence to the next, because the first row is written while the response is still in progress. Discarding the subsequent occurrences lost that growth. `_incremento()` instead sums only the positive difference field by field: an exact duplicate counts as zero, an update counts as its increment. Verified against the independent "maximum per `message.id`" method: negligible deviation (under 0.1%), due to zero-token turns that produce no row.
- **Cache writes at 1-hour TTL**: they cost **2×** the input price, not 1.25× (which applies to the 5-minute TTL). Claude Code uses the one-hour TTL, so here that is **100%** of cache writes — the entire cache write cost was underestimated by 60%. The split lives in the `usage.cache_creation` field (`ephemeral_1h_input_tokens` / `ephemeral_5m_input_tokens`); `tokens.csv` has a `cache_write_1h_tokens` column (a subset of `cache_write_tokens`, **not** an addend) and the page computes the cost with `cacheWriteCostUsd()`. Rows without that column — logs from earlier versions — count as 5-minute cache, so no regression.
- **Additional transcript trees** (`config.PROJECT_DIRS_EXTRA`): the desktop app in *local agent mode* gives each session a home of its own with a complete `.claude/projects/` inside (`<app>/local-agent-mode-sessions/<account>/<org>/local_<id>/.claude/projects/`). These are real sessions, with far-from-negligible consumption.

#### Price modifiers verified and NOT applicable
Verified on 2026-08-27 against the official pricing page, listed here so that the next person wondering "is something missing?" does not have to redo the research:
- **Long context**: no surcharge. The 1M context is billed at the standard rate — *"a 900k request is billed at the same rate as a 9k one"*. Relevant because, had it existed, it would have been a significant correction.
- **Fast mode**: doubles Opus 5 ($10/$50). Here `usage.speed` is always `standard`.
- **`inference_geo: "us"`**: 1.1× on all line items. Here the field is always `global` or `not_available`.
- **Web search**: $10 per 1,000 searches. Here `usage.server_tool_use` is always empty.
- **`output_tokens_details.thinking_tokens`**: a *subset* of output tokens, already billed as such. It must not be added on top.
- **Sonnet 5 at $2/$10**: it was announced as a promotion until 2026-08-31 and became the standard price. The increase to $3/$15 will not happen, and the expiration notice has been removed.

#### Two archives that keep attribution from self-perpetuating
- **`origine` (origin) column** (`hook` / `backfill`) in `tokens.csv`: distinguishes direct observations from reconstructions. Without it, after the first backfill you could no longer tell which rows are evidence, source 2 would not know which turn to start from, and a wrong attribution would crystallize at every re-run. The hooks write the value only if the CSV header already declares the column (`_colonne_esistenti()`), so a CSV from an earlier version does not end up with rows longer than its own header.
- **`~/.claude/logs/account_osservazioni.json`**: the backfill *rewrites* the rows of the sessions it reconstructs, thereby deleting the `origine=hook` rows from which it had derived the account — the evidence would vanish at the next re-run and the result would no longer be idempotent. The archive accumulates, per session, the oldest observation and never loses anything.
- **`NON_SONO_ACCOUNT`** lists the values that are *not* accounts (`sconosciuto`, `non rilevato`, and `storico` for backward compatibility with the first version): encountering them is equivalent to knowing nothing, so the account is looked up from scratch.

#### Guarantees
- **Idempotence by construction**: the transcript is the source of truth for a session's entire history, so for every session with a transcript the existing rows are discarded and rewritten from scratch. Re-running the backfill cannot produce duplicates. Sessions **without** a transcript (deleted, or coming from another machine) are left untouched.
- **Exception for `operations.csv`**: here nothing existing is rewritten. Live rows carry the hook's timestamp, reconstructed ones the transcript's: close but never identical, so there is no way to recognize a duplicate by comparing them. Therefore only the operations **prior** to the first one already recorded for that session are added.
- **Atomic write** (`os.replace` on a temporary file) plus a **dated safety copy** `tokens.csv.bak-AAAAMMGG-HHMMSS` (YYYYMMDD-HHMMSS) before every rewrite: unlike the `settings.json` backup, a history is kept here, because the CSVs are the sole archive of consumption.
- **Fidelity check**: over all locally present sessions, the sum of the reconstructed turns matches **exactly** the one computed by `sum_transcript_usage()`, the hook's own function. The differences from the pre-existing CSVs are only turns the hooks had missed.

#### Calibration against a real billed figure
The cost model was verified against external data, not against itself. `%APPDATA%\Claude\plan-usage-history.json` samples over time `xu`, the consumed percentage of the plan's monthly spending cap: knowing the cap in dollars gives the value of one point, and hence an external yardstick against which to measure the model.

Correlating the increments of `xu` with the cost computed over the same intervals (dozens of independent intervals, spanning two full months), the computed/actual ratio of the individual intervals sits almost entirely just below 1; the few values above 1 are boundary misalignments (the turn's timestamp is the last response, the samples are hourly) which cancel out in the total. **The residual gap is uniform, not concentrated**: it is not a missing session but a small systematic underestimation factor, on the order of a few percentage points.

The residual gap is real consumption that does not appear in the local transcripts.

Causes still open: requests retried after an error (billed but never written to the transcript), and sessions whose transcript no longer exists (too rare to explain the gap on their own).

Ruled out with verification: non-`assistant` entries with `usage` (none exists among the entries with consumption), the cache split (the identity `totale = 1h + 5m` holds exactly on every message), a fixed per-call cost (the implied value matches no documented line item), API retries (the logs for the period contain only preview timeouts), and all the price modifiers listed above.

#### Activation
- Automatic at the end of the **interactive** installation (double-clicking the installer), with a textual progress bar in the same console — `ConsoleProgress` rewrites the line with `\r` on a real terminal and falls back to progress lines every 10% when output is redirected.
- **Not** re-run by the automatic update: that relaunches `install --no-pause` detached and without a console (`updater._spawn_detached`), and rewriting the CSVs behind the back of a running Claude Code session would lose the rows appended in the meantime.
- Re-runnable manually with `dashboard-token backfill` (`--dry-run` to compute the effect without writing).
- The installer does **not** contain the `generate_dashboard` package (see `installer.spec`): it invokes the freshly installed application as a subprocess — which does contain it — inheriting the console for the progress bar.

---

## 🇮🇹 Italiano

Dashboard HTML statica e suite di hook per il monitoraggio dei consumi di token e costi di Claude Code. La generazione avviene interamente in locale a partire dai log CSV registrati sul disco, senza effettuare chiamate API esterne.

---

### 1. Architettura e Percorsi

#### Mappa dei Componenti
| Componente | Percorso predefinito | Descrizione |
|---|---|---|
| **Package generatore** | `~/.claude/hooks/generate_dashboard/` | Core di aggregazione e rendering HTML |
| **Hook Stop** | `~/.claude/hooks/log_tokens.py` | Registra i token per turno e innesca la generazione |
| **Hook PostToolUse** | `~/.claude/hooks/log_operation.py` | Registra le operazioni dei singoli tool |
| **Log turni** | `~/.claude/logs/tokens.csv` | Record storici per turno di conversazione |
| **Log azioni** | `~/.claude/logs/operations.csv` | Record storici per singola chiamata a tool |
| **Cache sessioni** | `~/.claude/logs/session_titles_cache.json` | Cache su disco di titoli e progetti per sessione |
| **Configurazione** | `~/.claude/hooks/dashboard_config.json` | Override opzionali: cartella di output (`{"out_dir": "..."}`) e log dell'app (`{"app_log_dir": "..."}`) |
| **Etichette account** | `~/.claude/hooks/account_labels.json` | Mappa opzionale UUID → etichetta human-readable |
| **Osservazioni account** | `~/.claude/logs/account_osservazioni.json` | Archivio delle osservazioni dirette dell'account, per sessione (vedi §7) |
| **Log dell'app Claude** | `%APPDATA%\Claude\logs\main*.log` | Sola lettura: registro dei cambi di account usato dal backfill (vedi §7) |
| **Output HTML** | `~/.claude/dashboard-token/` | File generati: `dashboard.html`, `pricing.html`, `guida-costi.html` |
| **Pacchetto installer** | `installer/` | Script e file per la distribuzione su altre postazioni |

#### Meccanismo di Esecuzione degli Hook
- **Exec Form**: Gli hook sono eseguiti direttamente dall'interprete (`"command": "python3", "args": [...]` in `~/.claude/settings.json`), senza invocare shell esterne (nessuna dipendenza da bash o Git for Windows).
- **Generazione sincrona**: A ogni fine turno, `log_tokens.py` esegue `import generate_dashboard; generate_dashboard.main()` in-process per rigenerare le pagine HTML.
- **Output autonomi**: Le pagine generate (`dashboard.html`, `pricing.html`, `guida-costi.html`) sono completamente self-contained (CSS e JS inline) e collegate tra loro tramite percorsi relativi.

---

### 2. Struttura del Package `generate_dashboard/`

Il generatore è organizzato in moduli dedicati:

| Modulo | Responsabilità |
|---|---|
| `config.py` | Risoluzione percorsi di input/output e lettura di `dashboard_config.json` |
| `pricing.py` | Definizione del listino prezzi (`MODEL_PRICING`), unica fonte di verità per tutte le pagine |
| `timeutils.py` | Gestione fuso orario italiano (CET/CEST) con algoritmo ora legale integrato |
| `numfmt.py` | Utility di formattazione numerica e valuta in stile italiano |
| `data.py` | Parsing e pulizia dei dati da `tokens.csv` e `operations.csv` |
| `sessions.py` | Estrazione e arricchimento di metadati sessione (titolo, progetto) con cache |
| `header.py` | Componente per la generazione di header, navbar unificata e stili CSS condivisi |
| `templating.py` | Caricamento dei template HTML e sostituzione dei placeholder |
| `templates/*.html` | Template sorgente per dashboard (`dashboard.html`), tariffario (`pricing.html`) e guida (`guide.html`) |
| `render_dashboard.py` | Logica di aggregazione e popolamento per `dashboard.html` |
| `render_pricing.py` | Logica di rendering per la tabella prezzi in `pricing.html` |
| `render_guide.py` | Calcolo delle soglie di convenienza e rendering per `guida-costi.html` |
| `main.py` | Entry point (`main()`) che orchestra l'aggiornamento e la scrittura dei tre file |
| `backfill.py` | Ricostruzione retroattiva dei CSV dai transcript delle sessioni precedenti all'installazione (vedi §7) |

---

### 3. Specifiche Tecniche dell'Interfaccia

#### Intestazione e Barra di Navigazione Condivisa
- **Componente Unificato (`header.py`)**: Tutte le pagine condividono lo stesso header e navbar, generati programmaticamente lato Python (`render_header(active_id, generated_at)`) ed iniettati nei template via `__SITE_HEADER__` e `__HEADER_CSS__`.
- **Brand & Metadata**:
  - Logo/Icona brand (`🪙`), titolo ("Claude Code") e sottotitolo ("Monitoraggio Token & Costi").
  - Pillola di stato con indicatore verde e timestamp di generazione dinamico in stile italiano (`generated_at_now()`).
- **Barra di Navigazione a Schede (`.nav-tabs`)**:
  - Menu principale con 3 voci: **Dashboard** (`dashboard.html`), **Tariffario** (`pricing.html`), **Guida ai costi** (`guida-costi.html`).
  - Icone SVG semantiche per ciascuna voce di menu (`currentColor`).
  - Riconoscimento automatico e stile evidenziato per la scheda attiva (`.nav-tab.active` con background `--control-bg`, bordo dedicato, ombra e `aria-current="page"`).
  - Transizioni fluide di hover e compatibilità con navigazione da tastiera (`:focus-visible`).
- **Allineamento e Larghezza**: Contenitore `.wrap` a larghezza uniforme (`max-width: 900px`) su tutte le pagine per prevenire salti visivi durante la navigazione.

#### Sistema di Filtri (`dashboard.html`)
- **Controlli Custom Dropdown**: I menu a tendina (`.custom-dropdown`) incapsulano un elemento `<select>` nascosto (`display:none`) per preservare la logica JS sottostante.
- **Layout Griglia**: La barra filtri (`.filter-row`) adotta un layout `display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr))` per garantire dimensioni uniformi e responsive.
- **Gestione Testi Lunghi**: I trigger dei dropdown troncano il testo eccedente con ellipsis (`overflow: hidden; text-overflow: ellipsis`) valorizzando l'attributo nativo `title` per il tooltip; all'interno del menu aperto, il testo va a capo fino a un massimo di 2 righe (`-webkit-line-clamp: 2`).
- **Sanitizzazione Dati**: Tutti i valori dinamici (titoli sessione, nomi account, progetti) vengono filtrati tramite funzione `esc()` prima dell'inserimento nel DOM.
- **Gerarchia e Cascata**:
  - Il filtro **Progetto** agisce in cascata sul filtro **Sessione**: la selezione di un progetto rigenera la lista sessioni (`populateSelect(proj)`) e reimposta eventuali selezioni non pertinenti, anche durante il ripristino dello stato da `sessionStorage`.
  - Il filtro **Periodo** affianca ai quattro periodi a calendario (*Oggi*, *Questa settimana*, *Questo mese*, *Quest'anno*, tutti aperti in avanti) una voce per ogni **mese effettivamente presente nei dati**, dal più recente, generata a runtime da `addMonthPeriods()`. Il mese in corso è omesso perché già coperto da *Questo mese*. Sono gli unici periodi dotati anche di un limite superiore (`to`), che `filterByPeriod` applica come estremo escluso.
  - Il filtro **Account** opera in intersezione (AND) con gli altri filtri sui turni. *(Nota: `operations.csv` eredita il progetto dalla sessione ma non memorizza l'account, pertanto il filtro Account non si applica alla tabella azioni).*

#### Grafici e Controlli Dinamici
- **Segmented Control**: Gli interruttori di modalità e intervallo temporale utilizzano un indicatore di selezione animato (`.indicator`), sincronizzato via JS (`positionSegmentedIndicator`) su resize e cambio stato.
- **Modalità Grafico "Andamento Token"**: Gestite tramite funzione generica `bucketTurns(..., keyFn)` con quattro raggruppamenti (`CHART_MODES`):
  1. *Per sessione* (`t.sid`)
  2. *Aggregato* (somma globale su linea singola)
  3. *Per modello* (raggruppamento per `modelShortLabel(t.model)`)
  4. *Per progetto* (raggruppamento per `projectOf(t)`, ossia il progetto della sessione)
- **Scelta delle serie nel grafico a linea**: `rankGroupsInWindow` ordina i gruppi per totale **dentro la finestra disegnata**, misurato con l'unità attiva, ed è quell'ordine che riceve `assignGroupColors`. Le tinte finiscono così alle serie che pesano e non alle prime capitate; uno spareggio deterministico (prima comparsa, poi confronto tra le chiavi) tiene i colori stabili tra un ridisegno e l'altro. Oltre l'ottava (`LINE_MAX_SERIES`, legata alla lunghezza della palette) `collapseTailSeries` fonde tutto in **un'unica** serie di chiave `LINE_TAIL_KEY`, sommando i secchi dello stesso intervallo. La coda si somma e non si media come nel grafico a barre: lì la barra di coda compete in graduatoria, qui l'asse dice "quanto si è speso in questo intervallo" e la somma di chi resta *è* quel numero. Poiché nessuna `keyFn` produce la coda, il suo tooltip di gruppo è costruito da `totalsFromBuckets` e dichiara "Totale nel periodo mostrato".
- **Scatter sulle finestre ampie**: con 24 intervalli campionati su mesi un intervallo dura giorni mentre una sessione dura ore, quindi quasi ogni sessione cade in un solo secchio e la "linea per sessione" degenera in pallini isolati. `seriesAreDegenerate` misura esattamente questo — la quota di serie che occupano un intervallo soltanto — e oltre la metà la modalità *Per sessione* (l'unica a dichiarare `scatterWhenSparse`) disegna invece un marcatore lollipop per sessione: piantato sul suo primo turno, alto quanto la sessione è costata nella finestra. Il criterio è senza scala, quindi segue `LINE_CHART_BUCKETS` da solo. In questa modalità la coda **non** si collassa: senza polilinee di mezzo, pallini grigi ad altezze diverse sono informazione, e sommarli produrrebbe il marcatore più alto del grafico. Tre scelte rendono leggibile la nuvola:
  - **Il colore cambia mestiere**: smette di dire *quale* sessione e passa a dire *di chi è* — il progetto (`rankProjectsOfPoints`, legenda presa in prestito da `CHART_MODES.project`). Con poche sessioni una tinta a testa è un nome e la legenda si legge; con centinaia non lo è più, e oltre l'ottava non restano tinte distinguibili, quindi la stragrande maggioranza dei marcatori uscirebbe dello stesso grigio: un canale acceso che non dice niente. I progetti sono pochi e hanno un nome, quindi come categoria funzionano — e isolarne uno dalla legenda dirada la nuvola (i bersagli sbiaditi prendono `pointer-events: none`) abbastanza da poter puntare col mouse dentro una giornata affollata. Vale solo per lo scatter: nel ramo a linea le sessioni sono poche, e lì una tinta a testa *è* un nome.
  - **L'asta porta il "quali contano"**, e va alle sessioni più costose della finestra (`stemmed`, dalla graduatoria delle sessioni). Un canale per variabile invece di due significati sullo stesso. Un'asta per ogni sessione sarebbe una staccionata di aste uguali, lunghe su scala logaritmica, che coprirebbe proprio le poche da confrontare; le altre restano un pallino più piccolo e meno pieno, ma sempre cliccabile, col raggio del bersaglio ristretto da 6 a 4 unità dato che `r=6` è tarato su un grafico dove una serie ha al massimo ventiquattro punti, non centinaia.
  - **Il riquadro SVG cresce** da `LINE_CHART_HEIGHT` = 200 a `LINE_SCATTER_HEIGHT` = 300, perché qui è l'altezza a separare marcatori che condividono la stessa fascia oraria.
- **Scala verticale** (interruttore *Scala*, persistita in `sessionStorage`): finché l'interruttore non è stato toccato, la scala la sceglie il grafico — logaritmica per lo scatter, lineare per le linee — e il controllo si muove insieme, così non dice mai una cosa diversa da quella disegnata. Il primo clic accende `scaleChosenByHand` e l'automatismo si spegne per sempre; un valore ripristinato vale come scelta. Non è una preferenza indovinata: una nuvola di sessioni copre tre ordini di grandezza e in lineare sta tutta appiccicata alla base, mentre un andamento nel tempo si legge in lineare. `makeValueAxis` restituisce la funzione di posizionamento e le tacche, così il codice di disegno non sa quale scala sia attiva. In logaritmica le tacche stanno sulle potenze di dieci (etichette tonde e a precisione unica, dato che `fmtMoneyAxis` deriva la precisione da `scale` per tutto l'asse), con un tetto di tre decadi, e i valori a zero si appoggiano alla linea di base — dove li mette già l'asse lineare, così cambiando scala quel punto non salta.
- **Legenda del grafico a linea e isolamento**: `chartLegendHtml` (già `barLegendHtml`) serve entrambi i grafici; `labelFn` traduce l'id di gruppo in un nome leggibile e `interactive` rende le voci un comando. Cliccarne una isola la propria serie commutando due classi su nodi già in pagina — nessun ridisegno, quindi gli indici dei tooltip fissati restano validi. Tutte le serie grigie condividono un solo identificativo `data-series`, così la voce "altre N" le accende tutte insieme.
- **Riempimenti**: l'area sotto la curva sopravvive solo con una serie sola e in scala lineare. Con più serie le aree si accavallano in una macchia illeggibile; in scala logaritmica l'area non è proporzionale a niente. Dove il riempimento sparisce, il bersaglio di clic largo lo fornisce `.line-hit`, un corridoio invisibile lungo il tratto — bersaglio migliore dell'area che sostituisce, che era cliccabile in tutta la fascia morta fino alla linea di base.
- **Raggruppamento del Grafico a Barre** (`BAR_GROUPS`, interruttore *Raggruppa*): struttura gemella di `CHART_MODES` che isola chiave, etichetta, ordinamento e troncamento; accumulo, disegno SVG e tooltip restano condivisi.
  1. *Per giorno* — ordine cronologico, tetto di 14 barre (31 con un periodo selezionato).
  2. *Per mese* — chiave `monthKey(t.ts)` (fuso locale, non la sottostringa UTC), ordine cronologico, tetto di 12 barre.
  3. *Per progetto* — ordine decrescente per valore **dell'unità attiva** (in token la graduatoria può differire da quella in dollari), tetto di `BAR_MAX_PROJECTS` = 12; i progetti eccedenti confluiscono in un'unica barra *Altri* in coda, così il totale a schermo resta il totale reale. Le etichette dei progetti sono inclinate di -30° e troncate a 14 caratteri (nome integrale nel tooltip); in questa modalità il riquadro SVG passa da 200 a 224 unità di altezza, lasciando invariata l'area di tracciamento.
- **Composizione dei Titoli**: `UNIT_MODES` fornisce il solo soggetto (`barNoun`: *Costo totale* / *Costo totale in euro* / *Token totali*), a cui il raggruppamento attivo aggiunge il complemento (*per giorno* / *per mese* / *per progetto*) e il periodo fra parentesi.
- **Stabilità del Layout**: L'elemento hint (`#line-chart-hint`) possiede un'altezza minima fissa (`min-height: 36px`) per evitare salti verticali del grafico al variare del testo descrittivo.
- **Micro-Animazioni**:
  - Tracciamento dinamico delle linee SVG tramite transizione `stroke-dasharray` / `stroke-dashoffset`.
  - Animazione di hover con elevazione (`transform: translateY(-3px)`) sulle hero card statistiche.
  - Espansione del pannello azioni nidificate tramite animazione `max-height` (0 → 2000px) e rotazione a 90° del glifo freccia (`▶`).
  - Disattivazione automatica di animazioni e transizioni in presenza della media query `@media (prefers-reduced-motion: reduce)`.

#### Schede Statistiche
- La striscia delle statistiche aggregate (`.stat-mini-grid`) è strutturata con `gap: 1px` e sfondo `--gridline`, producendo divisori compatti senza bordi orfani in caso di wrapping responsivo.
- Testi e descrizioni seguono un registro formale e neutro.

---

### 4. Specifiche Pagine Secondarie

#### `pricing.html`
- Elenca le tariffe attive per tutti i modelli supportati da `MODEL_PRICING`.
- Le note specifiche sui modelli vengono visualizzate su righe dedicate (`<tr class="note-row">`) con colspan completo.

#### `guida-costi.html`
- Guida dinamica all'ottimizzazione dei costi di contesto e output.
- **Calcolo Dinamico**: Tabelle comparative, moltiplicatori di costo e soglie di convenienza (cache vs input standard) sono calcolati a runtime a partire da `MODEL_PRICING` (filtrato sui modelli principali in `GUIDE_MODELS`).
- **Blocchi Condizionali**: Il blocco informativo promozionale (`__PROMO_BLOCK__`) compare esclusivamente se il modello di riferimento contiene note tariffarie attive.

---

### 5. Distribuzione e Installer (`installer/`)

La cartella `installer/` contiene il pacchetto per distribuire la dashboard su ambienti Windows, macOS e Linux:

- **Script di Setup**:
  - `install.ps1` / `install.cmd`: Setup per Windows.
  - `install.sh`: Setup per ambienti macOS/Linux.
- **Logica di Installazione**:
  - Verifica la presenza di un runtime Python funzionante (esecuzione effettiva di `python3 --version`, evitando falsi positivi da alias di sistema come `WindowsApps`). Se assente, propone l'installazione tramite package manager (`winget`, `brew`, `apt`, `dnf`, `pacman`).
  - Copia ricorsivamente il package `generate_dashboard/` e gli hook `log_tokens.py` e `log_operation.py` in `~/.claude/hooks/`.
  - Configura `~/.claude/settings.json` eseguendo un merge idempotente (aggiorna gli hook esistenti identificati dal nome file negli argomenti, preservando eventuali altri hook definiti dall'utente).
- **Sincronizzazione in Sviluppo**:
  - Lo script `sync-from-live.ps1` mantiene allineata la cartella `installer/hooks/` con `~/.claude/hooks/`.

---

### 6. Vincoli di Sistema e Dettagli Implementativi

1. **Gestione BOM UTF-8**: Gli hook leggono lo standard input come stream di byte binari (`sys.stdin.buffer`) decodificando con codec `utf-8-sig`, prevenendo errori di parsing JSON in caso di presenza di BOM.
2. **Creazione Directory Output**: Il generatore assicura preventivamente l'esistenza di `OUT_DIR` (`os.makedirs(OUT_DIR, exist_ok=True)`) prima della scrittura dei file.
3. **Calcolo Orario Senza Dipendenze**: `timeutils.py` implementa il calcolo algoritmico del fuso orario italiano e del cambio ora legale (direttive UE) per garantire compatibilità multipiattaforma senza dipendenze da pacchetti esterni come `tzdata`.
4. **Manipolazione DOM `<select>`**: Lo svuotamento dei dropdown nascosti avviene reimpostando `select.options.length = 0` per garantire la corretta sincronizzazione della collection degli elementi.
5. **Ordinamento Dati**: Le sessioni vengono ordinate cronologicamente in modo decrescente lato Python prima di essere passate al template.

---

### 7. Recupero Retroattivo dello Storico (`backfill.py`)

Gli hook osservano solo ciò che accade **dopo** l'installazione. Il modulo `backfill.py` colma il buco ricostruendo `tokens.csv` e `operations.csv` a partire dai transcript che Claude Code scrive comunque in `~/.claude/projects/<progetto>/<session_id>.jsonl`.

#### I due difetti che corregge
| Caso | Sintomo | Rimedio |
|---|---|---|
| Sessione mai vista dagli hook | Nessuna riga nei CSV | Ricostruzione completa da zero |
| Sessione a cavallo dell'installazione | Al primo hook `Stop` `session_cumulative_state.json` non aveva stato precedente, quindi `compute_turn_delta()` ha calcolato il delta partendo da zero: **tutto** il pregresso è finito in **una sola riga** datata al momento dell'installazione. Totali corretti, cronologia schiacciata | La riga viene sostituita dai turni reali, ognuno con la propria data |

#### Criteri di ricostruzione
- **Turni** (`rebuild_turns`): il confine di turno è l'entry `queue-operation`/`enqueue`, la stessa fonte usata da `extract_summary()` negli hook — il campo `summary` risulta quindi identico a quello che avrebbe scritto l'hook. I consumi si sommano deduplicando per `message.id`, esattamente come `sum_transcript_usage()`, perché lo `usage` di una chiamata API viene ripetuto su ogni blocco del messaggio. Timestamp = ultima risposta del turno; modello = ultimo non-`<synthetic>`; i turni a zero token non producono riga.
- **Operazioni** (`rebuild_ops`): una riga per `tool_use`, deduplicando per `(message.id, block.id)` e dividendo lo `usage` del messaggio per il numero di `tool_use` che lo compongono. **Divergenza voluta rispetto all'hook**: `attribute_action_cost()` gira durante la sessione e per i messaggi multi-blocco deve dichiarare `n/d` con costo 0; leggendo il transcript a cose fatte l'ambiguità non esiste, quindi le righe ricostruite attribuiscono anche il costo dei tool lanciati in parallelo.

#### Attribuzione dell'account: per turno, non per sessione
L'account **non è una proprietà della sessione ma del momento**. Su una macchina con più account (nei casi reali si osservano anche più cambi nella stessa giornata) una sessione ripresa a distanza di settimane attraversa più account, e attribuirne uno solo a tutta la sessione sbaglia in silenzio. Ogni turno riceve quindi il proprio, dalla prima fonte disponibile:

| # | Fonte | Dove |
|---|---|---|
| 1 | **Timeline degli accessi** — l'app Claude registra esplicitamente ogni cambio di account con data e ora (`[account] Login-state transition ... uuid: X -> Y`) | `%APPDATA%\Claude\logs\main*.log` (Win), `~/Library/Application Support/Claude/logs` (mac), `~/.config/Claude/logs` (Linux); override con `{"app_log_dir": "..."}` in `dashboard_config.json` |
| 2 | **Osservazione dell'hook** sulla stessa sessione, valida solo **dal turno osservato in poi** (più `MARGINE_OSSERVAZIONE`, 5 min, perché l'hook `Stop` scrive qualche secondo *dopo* la fine del turno cui si riferisce) | righe `origine=hook` + `account_osservazioni.json` |
| 3 | **UUID dichiarato dal transcript** (`bridge-session.ownerAccountUuid`), tradotto con `account_labels.json` | transcript |
| 4 | Ripiego `non rilevato`, distinto da `sconosciuto` (riga live con risoluzione fallita) | — |

Non si tira **mai** a indovinare con l'account loggato al momento del backfill: una sessione di mesi prima può essere stata di un altro.

**I log dell'app sono in ora locale**, i CSV in UTC: la conversione usa `timeutils.from_italy_time()`, inverso di `to_italy_time()`, con la stessa regola di ora legale UE calcolata a mano (niente `tzdata`).

**Perché non gli shell-snapshot**: `~/.claude/shell-snapshots/*.sh` contengono l'UUID dentro un `PATH` e hanno l'epoch nel nome, quindi sembrano una timeline utilizzabile. Sono stati scartati dopo validazione: Claude Code li ripulisce dopo ~30 giorni, e la loro rarefazione produce una quota rilevante di errori **concentrati proprio sui cambi di account**. La timeline dai log dell'app, validata contro le righe scritte dagli hook, non ha lasciato **errori residui sulle righe di controllo disponibili**.

**Limite noto (MSIX)**: se Python gira dentro un container MSIX (Microsoft Store / Python Install Manager) `%APPDATA%\Claude` è virtualizzato e risulta *inesistente* — stesso inciampo documentato in `log_tokens.account_uuid_candidates()`. L'applicazione impacchettata (normale processo Windows) non ne soffre; chi lancia i sorgenti a mano usa `app_log_dir`.

#### Consumi che nessuno contava
- **Sotto-agenti** (`find_subagents`): il tool Task/Agent scrive la conversazione del sotto-agente in un file separato, `projects/<progetto>/<session_id>/subagents/*.jsonl`. Non essendo nel transcript principale, non veniva contato **né dal backfill né dall'hook `Stop`**: nei casi reali è una quota enorme dei consumi, con singole sessioni sottostimate anche di oltre la metà. Ora `sum_transcript_usage()` e `_rebuild_turns()` leggono anche quei file, con un unico insieme di dedup per `message.id` condiviso fra tutti. I consumi del sotto-agente vengono assegnati al turno della sessione madre durante il quale è stato lanciato, per confronto di timestamp (ricerca binaria sui tempi di fine turno).
- **Occorrenze dello stesso `message.id` con `usage` diverso**: i blocchi di un messaggio ripetono lo `usage`, ed è per questo che si deduplica — ma non sempre lo ripetono *identico*: su messaggi reali si osserva l'`output_tokens` crescere fra un'occorrenza e la successiva, perché la prima riga viene scritta a risposta ancora in corso. Scartare le occorrenze successive perdeva quella crescita. `_incremento()` somma invece solo la differenza positiva campo per campo: un duplicato esatto vale zero, un aggiornamento vale l'incremento. Verificato contro il metodo indipendente "massimo per `message.id`": scarto trascurabile (sotto lo 0,1%), dovuto ai turni a zero token che non producono riga.
- **Cache write a TTL 1 ora**: costa **2×** il prezzo input, non 1,25× (che vale per la TTL da 5 minuti). Claude Code usa la TTL da un'ora, quindi qui è il **100%** delle scritture di cache — l'intero costo di cache write era sottostimato del 60%. La ripartizione sta nel campo `usage.cache_creation` (`ephemeral_1h_input_tokens` / `ephemeral_5m_input_tokens`); `tokens.csv` ha una colonna `cache_write_1h_tokens` (sottoinsieme di `cache_write_tokens`, **non** un addendo) e la pagina calcola il costo con `cacheWriteCostUsd()`. Le righe senza quella colonna — log di versioni precedenti — valgono come cache a 5 minuti, quindi nessuna regressione.
- **Alberi di transcript aggiuntivi** (`config.PROJECT_DIRS_EXTRA`): l'app desktop in *local agent mode* dà a ogni sessione una home propria con dentro un `.claude/projects/` completo (`<app>/local-agent-mode-sessions/<account>/<org>/local_<id>/.claude/projects/`). Sono sessioni vere, con consumi tutt'altro che trascurabili.

#### Modificatori di prezzo verificati e NON applicabili
Verificati il 2026-08-27 sulla pagina prezzi ufficiale, elencati qui perché il prossimo che si chiede "manca qualcosa?" non debba rifare la ricerca:
- **Contesto lungo**: nessun sovrapprezzo. Il contesto da 1M è a tariffa standard — *"una richiesta da 900k è fatturata alla stessa tariffa di una da 9k"*. Rilevante perché, se fosse esistito, sarebbe stata una correzione di peso.
- **Modalità fast**: raddoppia Opus 5 ($10/$50). Qui `usage.speed` è sempre `standard`.
- **`inference_geo: "us"`**: 1,1× su tutte le voci. Qui il campo vale sempre `global` o `not_available`.
- **Ricerca web**: $10 ogni 1.000 ricerche. Qui `usage.server_tool_use` è sempre vuoto.
- **`output_tokens_details.thinking_tokens`**: è un *sottoinsieme* degli output, già fatturato come tale. Non va sommato.
- **Sonnet 5 a $2/$10**: era annunciato come promo fino al 2026-08-31, è diventato il prezzo standard. L'aumento a $3/$15 non ci sarà, e l'avviso di scadenza è stato tolto.

#### Due archivi che impediscono all'attribuzione di auto-perpetuarsi
- **Colonna `origine`** (`hook` / `backfill`) in `tokens.csv`: distingue le osservazioni dirette dalle ricostruzioni. Senza, dopo il primo backfill non si saprebbe più quali righe sono prove, la fonte 2 non saprebbe da quale turno partire, e un'attribuzione sbagliata si cristallizzerebbe a ogni rilancio. Gli hook scrivono il valore solo se l'intestazione del CSV già dichiara la colonna (`_colonne_esistenti()`), così un CSV di una versione precedente non si ritrova righe più lunghe della propria intestazione.
- **`~/.claude/logs/account_osservazioni.json`**: il backfill *riscrive* le righe delle sessioni che ricostruisce, cancellando così le righe `origine=hook` da cui aveva ricavato l'account — la prova sparirebbe al rilancio successivo e il risultato non sarebbe più idempotente. L'archivio accumula, per sessione, l'osservazione più antica e non perde mai nulla.
- **`NON_SONO_ACCOUNT`** elenca i valori che *non* sono account (`sconosciuto`, `non rilevato`, e `storico` per retrocompatibilità con la prima versione): incontrarli equivale a non sapere nulla, quindi l'account viene ricercato da capo.

#### Garanzie
- **Idempotenza per costruzione**: il transcript è la fonte di verità per l'intera storia di una sessione, quindi per ogni sessione con transcript le righe esistenti vengono buttate e riscritte da capo. Rilanciare il backfill non può produrre duplicati. Le sessioni **senza** transcript (cancellato, o proveniente da un'altra macchina) restano intoccate.
- **Eccezione per `operations.csv`**: qui non si riscrive nulla di esistente. Le righe live hanno il timestamp dell'hook, quelle ricostruite quello del transcript: vicini ma mai identici, quindi non c'è modo di riconoscere un doppione confrontandoli. Si aggiungono perciò solo le operazioni **anteriori** alla prima già registrata per quella sessione.
- **Scrittura atomica** (`os.replace` su file temporaneo) più **copia di sicurezza datata** `tokens.csv.bak-AAAAMMGG-HHMMSS` prima di ogni riscrittura: a differenza del backup di `settings.json` qui si conserva uno storico, perché i CSV sono l'unico archivio dei consumi.
- **Verifica di fedeltà**: su tutte le sessioni presenti in locale la somma dei turni ricostruiti coincide **esattamente** con quella calcolata da `sum_transcript_usage()`, la funzione dell'hook. Le differenze rispetto ai CSV preesistenti sono solo turni che gli hook avevano mancato.

#### Calibrazione contro una cifra fatturata reale
Il modello di costo è stato verificato contro un dato esterno, non contro sé stesso. `%APPDATA%\Claude\plan-usage-history.json` campiona nel tempo `xu`, la percentuale consumata del tetto di spesa mensile del piano: conoscendo il tetto in dollari si ricava il valore di un punto, e quindi un metro esterno con cui misurare il modello.

Correlando gli incrementi di `xu` con il costo calcolato negli stessi intervalli (decine di intervalli indipendenti, su due mesi interi), il rapporto calcolato/reale dei singoli intervalli sta quasi tutto poco sotto 1; i pochi valori sopra 1 sono sfasamenti di confine (il timestamp del turno è l'ultima risposta, i campionamenti sono orari) che si compensano nel totale. **Lo scarto residuo è uniforme, non concentrato**: non è una sessione mancante ma un piccolo fattore sistematico di sottostima, nell'ordine di qualche punto percentuale.

Lo scarto residuo è consumo reale che non compare nei transcript locali.

Cause ancora aperte: richieste ritentate dopo un errore (fatturate ma mai scritte nel transcript), e sessioni il cui transcript non esiste più (troppo rare per spiegare da sole lo scarto).

Escluse con verifica: entry non-`assistant` con `usage` (non ne esiste nessuna fra le entry con consumi), ripartizione della cache (l'identità `totale = 1h + 5m` è esatta su ogni messaggio), costo fisso per chiamata (il valore implicato non corrisponde ad alcuna voce documentata), retry API (nei log del periodo ci sono solo timeout di anteprima), e tutti i modificatori di prezzo elencati sopra.

#### Attivazione
- Automatica al termine dell'installazione **interattiva** (doppio click sull'installer), con barra di avanzamento testuale nella stessa console — `ConsoleProgress` riscrive la riga con `\r` su un terminale vero e ripiega su righe di avanzamento ogni 10% quando l'output è rediretto.
- **Non** viene rieseguito dall'aggiornamento automatico: quello rilancia `install --no-pause` staccato e senza console (`updater._spawn_detached`), e riscrivere i CSV alle spalle di una sessione di Claude Code in corso comporterebbe la perdita delle righe appendute nel frattempo.
- Rilanciabile a mano con `dashboard-token backfill` (`--dry-run` per calcolare l'effetto senza scrivere).
- L'installer **non** contiene il package `generate_dashboard` (vedi `installer.spec`): invoca come sottoprocesso l'applicazione appena installata, che lo contiene, ereditando la console per la barra.

"""Titolo leggibile e progetto per ogni sessione, con cache su disco.

Risolve un titolo leggibile per ogni sessione leggendo custom-title / ai-title
dal transcript (~/.claude/projects/*/<session_id>.jsonl) e li mette in cache
in session_titles_cache.json, per non riscansionare ad ogni turno le sessioni
gia' concluse.

NOTA PER CHI NON CONOSCE PYTHON:
Un "transcript" e' il file .jsonl che Claude Code scrive per ogni sessione di
chat: contiene la cronologia intera, una riga per evento, dove ogni riga e'
un oggetto JSON indipendente (per questo l'estensione e' ".jsonl" = "JSON
Lines", diverso da un singolo file .json che contiene un solo oggetto
grande). Rileggere un transcript intero ad ogni turno per TUTTE le sessioni
passate sarebbe lento, quindi qui teniamo una "cache" -- un file piu'
piccolo (session_titles_cache.json) con i risultati gia' calcolati, che
aggiorniamo solo per la sessione corrente e per quelle mai viste prima.

[EN] Readable title and project for each session, with an on-disk
cache.

Resolves a readable title for each session by reading custom-title /
ai-title from the transcript (~/.claude/projects/*/<session_id>.jsonl)
and caches them in session_titles_cache.json, to avoid rescanning the
already-finished sessions on every turn.

NOTE FOR READERS NEW TO PYTHON:
A "transcript" is the .jsonl file Claude Code writes for every chat
session: it holds the entire history, one line per event, where each
line is an independent JSON object (hence the ".jsonl" extension =
"JSON Lines", unlike a single .json file containing one big object).
Re-reading a whole transcript on every turn for ALL past sessions
would be slow, so here we keep a "cache" -- a smaller file
(session_titles_cache.json) with the already-computed results, which
we update only for the current session and for those never seen
before.
"""
import glob
import json
import os

from . import config

# Versione del formato delle voci di cache. Va alzata di 1 ogni volta che
# cambia il MODO in cui titolo/progetto vengono calcolati: le voci salvate con
# una versione piu' vecchia vengono ricalcolate da zero al primo giro, invece
# di restare congelate col vecchio risultato. (Alzata a 2 quando i worktree
# hanno smesso di contare come progetti a se'.)
# [EN] Version of the cache entry format. Bump it by 1 whenever the WAY
# title/project are computed changes: entries saved with an older
# version get recomputed from scratch on the first run, instead of
# staying frozen with the old result. (Bumped to 2 when worktrees
# stopped counting as projects of their own.)
INFO_VERSION = 2

# Le due cartelle che, una dentro l'altra, segnalano un worktree creato da
# Claude Code: <progetto>/.claude/worktrees/<nome-worktree>.
# [EN] The two folders that, one inside the other, mark a worktree
# created by Claude Code: <project>/.claude/worktrees/<worktree-name>.
WORKTREE_MARKER = (".claude", "worktrees")


def project_from_cwd(cwd):
    """Nome del progetto a partire dalla cartella di lavoro di una sessione.

    Di norma e' semplicemente il nome dell'ultima cartella del percorso. Fanno
    eccezione i worktree (copie di lavoro parallele dello stesso repository):
    Claude Code li crea dentro il progetto stesso, in
    <progetto>/.claude/worktrees/<nome-worktree>, quindi l'ultima cartella
    sarebbe il nome del worktree ("pillole-6a0a4e") invece di quello del
    progetto ("dashboard-token"). Contarli come progetti a se' spezzerebbe i
    costi di un solo progetto su decine di voci diverse nei filtri e nei
    grafici, percio' qui si risale al progetto che li contiene.

    [EN] Project name starting from a session's working directory.

    Normally it is simply the name of the path's last folder. Worktrees
    (parallel working copies of the same repository) are the exception:
    Claude Code creates them inside the project itself, at
    <project>/.claude/worktrees/<worktree-name>, so the last folder
    would be the worktree's name ("pillole-6a0a4e") instead of the
    project's ("dashboard-token"). Counting them as projects of their
    own would split a single project's costs across dozens of separate
    entries in the filters and the charts, so here we walk back up to
    the project containing them."""
    if not cwd:
        return None

    # Windows separa le cartelle con la barra rovescia e Unix con quella
    # normale: uniformando le prime alle seconde il percorso si puo' spezzare
    # in pezzi una volta sola, con la stessa regola sui due sistemi. Il filtro
    # "if p" scarta i pezzi vuoti, che nascono da barre doppie o finali.
    # [EN] Windows separates folders with a backslash and Unix with a
    # forward slash: normalising the former to the latter lets the path
    # be split into pieces just once, with the same rule on both
    # systems. The "if p" filter drops the empty pieces, which come
    # from double or trailing slashes.
    parts = [p for p in str(cwd).replace("\\", "/").split("/") if p]
    if not parts:
        return None

    # Si cerca la coppia ".claude/worktrees" scorrendo i pezzi del percorso e
    # si restituisce il nome della cartella che sta subito PRIMA: quella e' il
    # progetto. L'indice parte da 1 perche' prima del marcatore ci deve essere
    # almeno una cartella, altrimenti non c'e' nessun progetto da recuperare.
    # [EN] We look for the ".claude/worktrees" pair by scanning the
    # path's pieces and return the name of the folder sitting right
    # BEFORE it: that is the project. The index starts at 1 because
    # there must be at least one folder before the marker, otherwise
    # there is no project to recover.
    for i in range(1, len(parts) - 1):
        if (parts[i], parts[i + 1]) == WORKTREE_MARKER:
            return parts[i - 1]

    # Nessun worktree di mezzo: il progetto e' l'ultima cartella, come sempre.
    # [EN] No worktree in the way: the project is the last folder, as always.
    return parts[-1]


def load_cache():
    """Legge session_titles_cache.json e restituisce il suo contenuto come
    dizionario Python, oppure un dizionario vuoto se il file non esiste
    ancora o e' illeggibile (stesso pattern try/except visto in config.py).

    [EN] Reads session_titles_cache.json and returns its content as a
    Python dictionary, or an empty dictionary if the file does not
    exist yet or is unreadable (same try/except pattern seen in
    config.py)."""
    if os.path.exists(config.CACHE_FILE):
        try:
            with open(config.CACHE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}
    return {}


def save_cache(cache):
    """Scrive il dizionario cache su disco come JSON. Se la scrittura
    fallisce (es. disco pieno, permessi) non blocchiamo la generazione della
    dashboard per questo: la cache verra' semplicemente ricalcolata al
    prossimo turno.

    [EN] Writes the cache dictionary to disk as JSON. If the write
    fails (e.g. disk full, permissions) we do not block the dashboard
    generation over it: the cache will simply be recomputed on the
    next turn."""
    try:
        with open(config.CACHE_FILE, "w", encoding="utf-8") as f:
            # ensure_ascii=False: permette di scrivere lettere accentate e
            # altri caratteri non-ASCII direttamente nel file invece di
            # convertirli in sequenze di escape tipo "è" (meno leggibile
            # se si apre il file a mano).
            # [EN] ensure_ascii=False: lets accented letters and other
            # non-ASCII characters be written directly into the file
            # instead of converting them to escape sequences (less
            # readable if you open the file by hand).
            json.dump(cache, f, ensure_ascii=False)
    except OSError:
        # "pass" = "non fare nulla", usato quando serve un blocco vuoto
        # [EN] "pass" = "do nothing", used where an empty block is
        # needed
        pass


def resolve_session_info(session_id):
    """Titolo leggibile + cartella di progetto (cwd), unica info di identita'
    per-sessione effettivamente disponibile in locale (l'account Claude
    attivo non viene salvato da nessuna parte per sessione).

    [EN] Readable title + project folder (cwd), the only per-session
    identity info actually available locally (the active Claude
    account is not saved anywhere on a per-session basis)."""
    # glob.glob(pattern) cerca sul disco tutti i file/cartelle il cui nome
    # combacia con un pattern che usa "*" come jolly (equivalente a quello
    # che scriveresti in un terminale). Qui: "trova il file <session_id>.jsonl
    # dentro una QUALSIASI sottocartella di PROJECTS_DIR" -- ogni progetto ha
    # la sua sottocartella, e non sappiamo a priori in quale sia questa
    # sessione, quindi il "*" al posto del nome cartella cerca in tutte.
    # [EN] glob.glob(pattern) searches the disk for every file/folder
    # whose name matches a pattern using "*" as a wildcard (equivalent
    # to what you would type in a terminal). Here: "find the file
    # <session_id>.jsonl inside ANY subfolder of PROJECTS_DIR" -- each
    # project has its own subfolder, and we do not know beforehand
    # which one this session is in, so the "*" in place of the folder
    # name searches them all.
    pattern = os.path.join(config.PROJECTS_DIR, "*", f"{session_id}.jsonl")
    # lista di percorsi trovati (di solito 0 o 1)
    # [EN] list of paths found (usually 0 or 1)
    matches = glob.glob(pattern)

    if not matches:
        # Nessun transcript trovato per questa sessione (es. cancellato, o
        # sessione da una macchina diversa): titolo di ripiego che mostra
        # solo le prime 8 lettere dell'id, giusto per distinguerla nei filtri.
        # [EN] No transcript found for this session (e.g. deleted, or
        # a session from a different machine): fallback title showing
        # only the first 8 letters of the id, just enough to tell it
        # apart in the filters.
        return {"title": f"Sessione {session_id[:8]}", "project": None,
                "v": INFO_VERSION}

    # prendiamo il primo (e di norma unico) risultato
    # [EN] take the first (and normally only) result
    path = matches[0]
    project_dir = os.path.basename(os.path.dirname(path))
    custom_title = None
    ai_title = None
    cwd_project = None
    try:
        with open(path, encoding="utf-8") as f:
            # Leggiamo il transcript riga per riga (ogni riga = un evento
            # della sessione, in ordine cronologico) cercando tre tipi di
            # informazione diversi, aggiornandoli man mano che li troviamo.
            # [EN] We read the transcript line by line (each line = one
            # session event, in chronological order) looking for three
            # different kinds of information, updating them as we find
            # them.
            for line in f:
                # toglie spazi/a-capo superflui a inizio/fine riga
                # [EN] strips extra spaces/newlines at start/end of line
                line = line.strip()
                if not line:
                    # riga vuota, saltala
                    # [EN] empty line, skip it
                    continue
                try:
                    # trasforma il testo JSON della riga in un dict
                    # [EN] turns the line's JSON text into a dict
                    e = json.loads(line)
                except json.JSONDecodeError:
                    # riga corrotta/non-JSON, saltala e vai avanti
                    # [EN] corrupted/non-JSON line, skip it and move on
                    continue

                t = e.get("type")
                if t == "custom-title" and e.get("customTitle"):
                    # L'utente ha rinominato la sessione a mano: massima priorita'.
                    # [EN] The user renamed the session by hand: top
                    # priority.
                    custom_title = e["customTitle"]
                elif t == "ai-title" and e.get("aiTitle"):
                    # Titolo generato automaticamente da Claude: ripiego se
                    # manca un titolo scelto dall'utente.
                    # [EN] Title generated automatically by Claude:
                    # fallback when a user-chosen title is missing.
                    ai_title = e["aiTitle"]
                elif cwd_project is None and e.get("cwd"):
                    # "cwd" (current working directory) e' la cartella in cui
                    # gira il progetto. La prendiamo solo la PRIMA volta che
                    # la vediamo (cwd_project is None), tanto non cambia
                    # durante la sessione. Il nome del progetto non e'
                    # sempre l'ultima cartella del percorso: ci pensa
                    # project_from_cwd, qui sopra.
                    # [EN] "cwd" (current working directory) is the
                    # folder the project runs in. We take it only the
                    # FIRST time we see it (cwd_project is None),
                    # since it does not change during the session. The
                    # project name is not always the path's last
                    # folder: project_from_cwd above takes care of it.
                    cwd_project = project_from_cwd(e["cwd"])
    except OSError:
        # transcript non leggibile per qualche motivo: teniamo quello
        # che abbiamo trovato finora
        # [EN] transcript unreadable for some reason: keep what we
        # have found so far
        pass

    # Ordine di priorita' per il titolo mostrato: prima quello scelto
    # dall'utente, poi quello generato dall'IA, infine un titolo generico
    # "nome-progetto · primi 8 caratteri dell'id".
    # [EN] Priority order for the displayed title: first the one
    # chosen by the user, then the AI-generated one, finally a generic
    # title made of the project name plus the id's first 8 characters.
    title = custom_title or ai_title or f"{project_dir} · {session_id[:8]}"
    return {"title": title, "project": cwd_project, "v": INFO_VERSION}


def resolve_all_session_info(session_ids, most_recent_id):
    """Risolve titolo+progetto per una lista di sessioni, usando la cache su
    disco per evitare di rileggere i transcript delle sessioni gia' concluse
    ad ogni turno (rilegge solo quelle nuove o quella corrente).

    [EN] Resolves title+project for a list of sessions, using the
    on-disk cache to avoid re-reading the transcripts of the
    already-finished sessions on every turn (it re-reads only the new
    ones and the current one)."""
    cache = load_cache()
    # dizionario che stiamo per riempire:
    # {session_id: {"title": ..., "project": ...}}
    # [EN] dictionary we are about to fill:
    # {session_id: {"title": ..., "project": ...}}
    info = {}

    for sid in session_ids:
        # None se sid non e' ancora in cache
        # [EN] None if sid is not in the cache yet
        cached = cache.get(sid)

        # Le voci di cache vecchie (pre-'progetto') sono stringhe semplici, e
        # quelle scritte prima di un cambio nel calcolo del progetto portano
        # un numero di versione piu' basso: in entrambi i casi si ri-risolve,
        # oltre al solito refresh per la sessione corrente o mai vista.
        #
        # "needs_resolve" e' un booleano (True/False) calcolato con un OR
        # (l'operatore "or" tra piu' condizioni su righe diverse, imbustato
        # tra parentesi per leggibilita'): basta che UNA delle condizioni
        # sia vera perche' tutto il blocco valga True.
        # [EN] Old (pre-'project') cache entries are plain strings, and
        # those written before a change in how the project is computed
        # carry a lower version number: in both cases we re-resolve, on
        # top of the usual refresh for the current or never-seen
        # session.
        #
        # "needs_resolve" is a boolean (True/False) computed with an
        # OR (the "or" operator across several conditions on separate
        # lines, wrapped in parentheses for readability): it is enough
        # for ONE of the conditions to be true for the whole block to
        # be True.
        needs_resolve = (
            # e' la sessione del turno appena concluso: potrebbe
            # essere cambiata
            # [EN] it is the session of the just-finished turn: it may
            # have changed
            sid == most_recent_id
            # non l'abbiamo mai vista prima
            # [EN] we have never seen it before
            or cached is None
            # voce di cache in un formato vecchio/inatteso
            # [EN] cache entry in an old/unexpected format
            or not isinstance(cached, dict)
            # voce di cache scritta prima che esistesse questo campo
            # [EN] cache entry written before this field existed
            or "project" not in cached
            # voce calcolata con una versione precedente delle regole
            # (es. quando i worktree contavano come progetti a se')
            # [EN] entry computed with an earlier version of the rules
            # (e.g. when worktrees counted as projects of their own)
            or cached.get("v") != INFO_VERSION
        )
        info[sid] = resolve_session_info(sid) if needs_resolve else cached

    # dict.update(altro_dict) copia dentro "cache" tutte le chiavi/valori di
    # "info", sovrascrivendo quelle gia' presenti -- cosi' la cache su disco
    # resta valida anche per le sessioni non toccate in questo giro.
    # [EN] dict.update(other_dict) copies all of "info"'s keys/values
    # into "cache", overwriting those already present -- so the
    # on-disk cache stays valid for the sessions not touched in this
    # round too.
    cache.update(info)
    save_cache(cache)
    return info

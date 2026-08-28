"""Test del recupero retroattivo dello storico (generate_dashboard/backfill.py).

Si lancia senza dipendenze esterne (niente pytest):

    python packaging/test_backfill.py

E' delicato quanto il merge di settings.json, e per lo stesso motivo: il
backfill RISCRIVE tokens.csv e operations.csv, cioe' l'unico archivio dei
consumi dell'utente. Un errore qui non da' un messaggio d'errore, da' uno
storico silenziosamente sbagliato -- righe duplicate a ogni rilancio, oppure
sessioni cancellate perche' il loro transcript non c'e' piu'.

Nessun test tocca i CSV veri: config viene fatto puntare a una cartella
temporanea, e i transcript sono finti, scritti su misura per il caso da
verificare.

[EN] Tests of the retroactive history recovery
(generate_dashboard/backfill.py).

Runs with no external dependencies (no pytest):

    python packaging/test_backfill.py

It is as delicate as the settings.json merge, and for the same reason: the
backfill REWRITES tokens.csv and operations.csv, i.e. the user's only
archive of usage. A mistake here does not give an error message, it gives
a silently wrong history -- rows duplicated on every rerun, or sessions
deleted because their transcript is gone.

No test touches the real CSVs: config is pointed at a temporary folder,
and the transcripts are fake, written to measure for the case under test.
"""
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "installer", "hooks"
    ),
)

from generate_dashboard import backfill, config  # noqa: E402


# ------------------------------------------------------------- strumenti --
# [EN] ---------------------------------------------------------- helpers --

def _entry(**campi):
    """Una riga di transcript in formato JSON Lines.

    [EN] One transcript line in JSON Lines format."""
    return json.dumps(campi) + "\n"


def _assistant(msg_id, ts, model="claude-opus-5", usage=None, content=None):
    """Entry "assistant", nella forma in cui la scrive Claude Code.

    [EN] An "assistant" entry, in the form Claude Code writes it."""
    message = {"id": msg_id, "model": model}
    if usage is not None:
        message["usage"] = usage
    if content is not None:
        message["content"] = content
    return _entry(type="assistant", timestamp=ts, message=message)


def _enqueue(ts, testo):
    """Entry del messaggio digitato dall'utente: inizio di un turno.

    [EN] Entry for the message typed by the user: start of a turn."""
    return _entry(type="queue-operation", operation="enqueue", timestamp=ts, content=testo)


def _usage(inp=0, out=0, cw=0, cr=0, cw_1h=None):
    u = {
        "input_tokens": inp, "output_tokens": out,
        "cache_creation_input_tokens": cw, "cache_read_input_tokens": cr,
    }
    if cw_1h is not None:
        # Ripartizione per durata della cache, come la scrive Claude Code.
        # [EN] Cache breakdown by duration, as Claude Code writes it.
        u["cache_creation"] = {"ephemeral_1h_input_tokens": cw_1h,
                               "ephemeral_5m_input_tokens": cw - cw_1h}
    return u


def _scrivi_transcript(base, progetto, sid, righe):
    cartella = os.path.join(base, progetto)
    os.makedirs(cartella, exist_ok=True)
    percorso = os.path.join(cartella, sid + ".jsonl")
    with open(percorso, "w", encoding="utf-8") as f:
        f.writelines(righe)
    return percorso


def _leggi(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


ESITI = []


def verifica(nome, condizione, dettaglio=""):
    ESITI.append((nome, bool(condizione), dettaglio))
    print("  {} {}{}".format("OK  " if condizione else "FALLITO", nome,
                             "" if condizione else "  -> " + str(dettaglio)))


# ------------------------------------------------------- turni (tokens.csv) --
# [EN] -------------------------------------------------- turns (tokens.csv) --

def test_turni():
    print("Ricostruzione dei turni:")
    tmp = tempfile.mkdtemp(prefix="backfill-turni-")
    try:
        path = _scrivi_transcript(tmp, "prog", "sess-a", [
            _enqueue("2026-01-02T10:00:00.000Z", "prima   domanda\ncon a capo"),
            _assistant("msg-1", "2026-01-02T10:00:05.500Z", usage=_usage(10, 20, 30, 40)),
            # Stesso message.id: e' un altro blocco della STESSA chiamata API,
            # il suo usage non va contato una seconda volta.
            # [EN] Same message.id: it is another block of the SAME API
            # call, its usage must not be counted a second time.
            _assistant("msg-1", "2026-01-02T10:00:05.900Z", usage=_usage(10, 20, 30, 40)),
            _assistant("msg-2", "2026-01-02T10:00:09.000Z", usage=_usage(1, 2, 3, 4)),
            _enqueue("2026-01-02T10:05:00.000Z", "seconda domanda"),
            _assistant("msg-3", "2026-01-02T10:05:07.000Z",
                       model="<synthetic>", usage=_usage(5, 5, 0, 0)),
            _assistant("msg-4", "2026-01-02T10:05:08.000Z",
                       model="claude-sonnet-5", usage=_usage(7, 0, 0, 0)),
            # Turno finale senza nessuna risposta: non deve produrre riga.
            # [EN] Final turn with no reply at all: must produce no row.
            _enqueue("2026-01-02T10:09:00.000Z", "domanda annullata"),
        ])
        turni = backfill.rebuild_turns(path, "sess-a", "tizio")

        verifica("un turno per domanda, quelli a zero token esclusi",
                 len(turni) == 2, len(turni))
        verifica("usage deduplicato per message.id",
                 turni[0]["total_tokens"] == (10 + 20 + 30 + 40) + (1 + 2 + 3 + 4),
                 turni[0]["total_tokens"])
        verifica("le quattro colonne di token restano separate",
                 (turni[0]["input_tokens"], turni[0]["output_tokens"],
                  turni[0]["cache_write_tokens"], turni[0]["cache_read_tokens"])
                 == (11, 22, 33, 44), turni[0])
        verifica("summary appiattito su una riga",
                 turni[0]["summary"] == "prima domanda con a capo", turni[0]["summary"])
        verifica("timestamp dell'ultima risposta del turno, al secondo",
                 turni[0]["timestamp"] == "2026-01-02T10:00:09Z", turni[0]["timestamp"])
        verifica("'<synthetic>' scartato a favore del modello vero",
                 turni[1]["model"] == "claude-sonnet-5", turni[1]["model"])
        verifica("account propagato su ogni riga",
                 all(t["account"] == "tizio" for t in turni), turni)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_subagenti():
    """I sotto-agenti (tool Task/Agent) hanno un transcript separato, in
    `<session_id>/subagents/`. Ignorarli puo' sottostimare in modo
    rilevante la sessione madre.

    [EN] Sub-agents (Task/Agent tool) have a separate transcript, in
    `<session_id>/subagents/`. Ignoring them can significantly
    understate the parent session."""
    print("Consumi dei sotto-agenti:")
    tmp = tempfile.mkdtemp(prefix="backfill-sub-")
    try:
        path = _scrivi_transcript(tmp, "prog", "sess-s", [
            _enqueue("2026-02-01T10:00:00.000Z", "primo turno"),
            _assistant("m1", "2026-02-01T10:00:05.000Z", usage=_usage(1, 1, 0, 0)),
            _enqueue("2026-02-01T11:00:00.000Z", "secondo turno, con delega"),
            _assistant("m2", "2026-02-01T11:00:30.000Z", usage=_usage(1, 1, 0, 0)),
        ])
        sub = os.path.join(tmp, "prog", "sess-s", "subagents")
        os.makedirs(sub, exist_ok=True)
        with open(os.path.join(sub, "agent-abc.jsonl"), "w", encoding="utf-8") as f:
            f.writelines([
                # Dentro il secondo turno: 11:00:00 < 11:00:10 < 11:00:30.
                # [EN] Inside the second turn: 11:00:00 < 11:00:10 < 11:00:30.
                _assistant("s1", "2026-02-01T11:00:10.000Z", usage=_usage(0, 500, 0, 0)),
                # Ripetizione dello stesso message.id: non va contata due volte.
                # [EN] Repetition of the same message.id: must not be counted twice.
                _assistant("s1", "2026-02-01T11:00:10.000Z", usage=_usage(0, 500, 0, 0)),
                _assistant("s2", "2026-02-01T11:00:20.000Z", usage=_usage(0, 300, 0, 0),
                           content=[{"type": "tool_use", "id": "t1", "name": "Read",
                                     "input": {"file_path": "dentro-subagent.py"}}]),
            ])

        turni = backfill.rebuild_turns(path, "sess-s", "x")
        verifica("i turni restano due", len(turni) == 2, len(turni))
        verifica("il primo turno non e' toccato",
                 turni[0]["total_tokens"] == 2, turni[0])
        verifica("i token del sotto-agente finiscono nel turno giusto",
                 turni[1]["total_tokens"] == 2 + 800, turni[1])
        verifica("dedup per message.id anche fra i file dei sotto-agenti",
                 turni[1]["output_tokens"] == 1 + 800, turni[1])

        ops = backfill.rebuild_ops(path, "sess-s")
        verifica("anche le azioni del sotto-agente vengono registrate",
                 [o["target"] for o in ops] == ["dentro-subagent.py"], ops)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_cache_a_unora():
    """Le due durate di cache costano diversamente (1,25x contro 2x il prezzo
    input): la quota a un'ora va registrata a parte, altrimenti il costo del
    turno risulta sottostimato.

    [EN] The two cache durations cost differently (1.25x versus 2x the
    input price): the one-hour share must be recorded separately,
    otherwise the turn's cost comes out understated."""
    print("Ripartizione della cache per durata:")
    tmp = tempfile.mkdtemp(prefix="backfill-cache-")
    try:
        path = _scrivi_transcript(tmp, "prog", "sess-c1", [
            _enqueue("2026-03-01T10:00:00.000Z", "turno"),
            _assistant("m1", "2026-03-01T10:00:05.000Z",
                       usage=_usage(0, 0, 1000, 0, cw_1h=800)),
        ])
        t = backfill.rebuild_turns(path, "sess-c1", "x")[0]
        verifica("il totale di cache write non cambia",
                 t["cache_write_tokens"] == 1000, t)
        verifica("la quota a un'ora e' registrata a parte",
                 t["cache_write_1h_tokens"] == 800, t)
        verifica("non e' un addendo: non gonfia il totale del turno",
                 t["total_tokens"] == 1000, t)

        # Senza il campo di ripartizione (log di versioni precedenti) la
        # quota a un'ora resta 0 e tutto vale come cache a 5 minuti.
        # [EN] Without the breakdown field (logs from earlier versions) the
        # one-hour share stays 0 and everything counts as 5-minute cache.
        path2 = _scrivi_transcript(tmp, "prog", "sess-c2", [
            _assistant("m2", "2026-03-01T11:00:05.000Z", usage=_usage(0, 0, 500, 0)),
        ])
        t2 = backfill.rebuild_turns(path2, "sess-c2", "x")[0]
        verifica("log senza ripartizione: nessuna regressione",
                 t2["cache_write_1h_tokens"] == 0 and t2["cache_write_tokens"] == 500, t2)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_alberi_extra():
    """L'app desktop, in "local agent mode", scrive un albero .claude/projects
    tutto suo: sono sessioni vere, e vanno lette anche quelle.

    [EN] The desktop app, in "local agent mode", writes a .claude/projects
    tree of its own: those are real sessions, and they must be read too."""
    print("Alberi di transcript aggiuntivi:")
    with _Ambiente() as amb:
        extra = os.path.join(amb.tmp, "app", "local_x", ".claude", "projects")
        _scrivi_transcript(extra, "prog", "sess-extra", [
            _enqueue("2026-04-01T10:00:00.000Z", "domanda"),
            _assistant("m1", "2026-04-01T10:00:02.000Z", usage=_usage(7, 0, 0, 0)),
        ])
        trovati = backfill.find_transcripts()
        verifica("senza l'albero extra la sessione non si vede",
                 "sess-extra" not in trovati, list(trovati))
        config.PROJECT_DIRS_EXTRA = [extra]
        trovati = backfill.find_transcripts()
        verifica("dichiarando l'albero extra, la sessione compare",
                 "sess-extra" in trovati, list(trovati))
        config.PROJECT_DIRS_EXTRA = []


def test_usage_che_cresce():
    """I blocchi di uno stesso messaggio ripetono l'usage, ma non sempre
    identico: la prima riga puo' essere scritta a risposta ancora in corso e
    l'output cresce dopo. Scartare le occorrenze successive perdeva quella
    crescita; va sommato l'incremento.

    [EN] The blocks of one message repeat the usage, but not always
    identically: the first line can be written while the reply is still in
    progress and the output grows afterwards. Discarding later occurrences
    lost that growth; the increment must be added in."""
    print("Occorrenze dello stesso messaggio con usage che cresce:")
    tmp = tempfile.mkdtemp(prefix="backfill-incr-")
    try:
        path = _scrivi_transcript(tmp, "prog", "sess-i", [
            _enqueue("2026-05-01T10:00:00.000Z", "domanda"),
            # Stesso message.id: prima riga a risposta in corso (output 1),
            # poi il valore definitivo (output 500).
            # [EN] Same message.id: first line while the reply is in
            # progress (output 1), then the final value (output 500).
            _assistant("m1", "2026-05-01T10:00:01.000Z", usage=_usage(3, 1, 100, 200)),
            _assistant("m1", "2026-05-01T10:00:02.000Z", usage=_usage(3, 500, 100, 200)),
            # Duplicato esatto: non deve aggiungere nulla.
            # [EN] Exact duplicate: must add nothing.
            _assistant("m1", "2026-05-01T10:00:03.000Z", usage=_usage(3, 500, 100, 200)),
        ])
        t = backfill.rebuild_turns(path, "sess-i", "x")[0]
        verifica("l'output definitivo prevale su quello parziale",
                 t["output_tokens"] == 500, t)
        verifica("gli altri campi non vengono contati due volte",
                 (t["input_tokens"], t["cache_write_tokens"], t["cache_read_tokens"])
                 == (3, 100, 200), t)
        verifica("il totale del turno e' coerente",
                 t["total_tokens"] == 3 + 500 + 100 + 200, t)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_turno_senza_enqueue():
    """Sessioni riprese con --resume: si risponde senza che nel transcript
    compaia un enqueue. Il turno esiste comunque, solo senza riepilogo.

    [EN] Sessions resumed with --resume: a reply happens without an
    enqueue appearing in the transcript. The turn exists anyway, just
    without a summary."""
    print("Turni senza messaggio digitato (sessioni riprese):")
    tmp = tempfile.mkdtemp(prefix="backfill-resume-")
    try:
        path = _scrivi_transcript(tmp, "prog", "sess-r", [
            _assistant("msg-1", "2026-01-03T08:00:01.000Z", usage=_usage(1, 1, 0, 0)),
        ])
        turni = backfill.rebuild_turns(path, "sess-r", "storico")
        verifica("la risposta viene comunque registrata", len(turni) == 1, turni)
        verifica("summary vuoto invece di riga persa",
                 turni and turni[0]["summary"] == "", turni)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_transcript_corrotto():
    """Una riga illeggibile non deve far perdere tutto il resto del file.

    [EN] One unreadable line must not lose the whole rest of the file."""
    print("Transcript con righe corrotte:")
    tmp = tempfile.mkdtemp(prefix="backfill-corrotto-")
    try:
        path = _scrivi_transcript(tmp, "prog", "sess-c", [
            _enqueue("2026-01-04T09:00:00.000Z", "domanda"),
            "{ questa riga non e' JSON\n",
            "\n",
            _assistant("msg-1", "2026-01-04T09:00:03.000Z", usage=_usage(2, 3, 0, 0)),
        ])
        turni = backfill.rebuild_turns(path, "sess-c", "storico")
        verifica("le righe valide vengono comunque lette",
                 len(turni) == 1 and turni[0]["total_tokens"] == 5, turni)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# -------------------------------------------------- operazioni (operations) --
# [EN] --------------------------------------------- operations (operations) --

def test_operazioni():
    print("Ricostruzione delle operazioni:")
    tmp = tempfile.mkdtemp(prefix="backfill-ops-")
    try:
        # Due tool lanciati in parallelo nello stesso messaggio: nel
        # transcript sono due righe che ripetono lo stesso message.id e lo
        # stesso usage. Il costo va diviso, non contato due volte.
        # [EN] Two tools launched in parallel in the same message: in the
        # transcript they are two lines repeating the same message.id and
        # the same usage. The cost must be split, not counted twice.
        path = _scrivi_transcript(tmp, "prog", "sess-o", [
            _assistant("msg-1", "2026-01-05T11:00:00.250Z", usage=_usage(100, 40, 20, 8),
                       content=[{"type": "tool_use", "id": "tu-1", "name": "Read",
                                 "input": {"file_path": "C:/a/b.py"}}]),
            _assistant("msg-1", "2026-01-05T11:00:00.250Z", usage=_usage(100, 40, 20, 8),
                       content=[{"type": "tool_use", "id": "tu-2", "name": "Bash",
                                 "input": {"command": "git   status\n-s"}}]),
            # Ripetizione esatta della stessa coppia: va ignorata.
            # [EN] Exact repetition of the same pair: must be ignored.
            _assistant("msg-1", "2026-01-05T11:00:00.250Z", usage=_usage(100, 40, 20, 8),
                       content=[{"type": "tool_use", "id": "tu-1", "name": "Read",
                                 "input": {"file_path": "C:/a/b.py"}}]),
        ])
        ops = backfill.rebuild_ops(path, "sess-o")

        verifica("una riga per tool_use, senza doppioni", len(ops) == 2, len(ops))
        verifica("costo diviso fra i tool paralleli",
                 sum(o["input_tokens"] for o in ops) == 100,
                 [o["input_tokens"] for o in ops])
        verifica("target da file_path", ops[0]["target"] == "C:/a/b.py", ops[0]["target"])
        verifica("target da command, appiattito",
                 ops[1]["target"] == "git status -s", ops[1]["target"])
        verifica("timestamp con i millisecondi",
                 ops[0]["timestamp"] == "2026-01-05T11:00:00.250Z", ops[0]["timestamp"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------------------------------------- end-to-end --
# [EN] -------------------------------------------------------- end-to-end --

class _Ambiente(object):
    """Fa puntare config a una cartella temporanea, e rimette tutto a posto
    all'uscita: nessun test deve poter toccare i CSV veri dell'utente.

    [EN] Points config at a temporary folder, and puts everything back on
    exit: no test may be able to touch the user's real CSVs."""

    def __enter__(self):
        self.tmp = tempfile.mkdtemp(prefix="backfill-e2e-")
        self.originali = (config.TOKENS_CSV, config.OPS_CSV,
                          config.PROJECTS_DIR, config.LABELS_FILE,
                          config.APP_LOG_DIRS, config.OSSERVAZIONI_FILE,
                          config.PROJECT_DIRS_EXTRA)
        config.TOKENS_CSV = os.path.join(self.tmp, "logs", "tokens.csv")
        config.OPS_CSV = os.path.join(self.tmp, "logs", "operations.csv")
        config.PROJECTS_DIR = os.path.join(self.tmp, "projects")
        # Anche le etichette degli account vanno dirottate: sono un file
        # personale della macchina, e un test non deve dipendere da cosa
        # c'e' scritto dentro quello vero.
        # [EN] The account labels must be redirected too: they are a
        # machine-personal file, and a test must not depend on what is
        # written inside the real one.
        config.LABELS_FILE = os.path.join(self.tmp, "hooks", "account_labels.json")
        # Di default nessun log dell'app: i test che ne vogliono uno lo
        # scrivono con _scrivi_log_app().
        # [EN] By default no app log: the tests that want one write it
        # with _scrivi_log_app().
        config.APP_LOG_DIRS = [os.path.join(self.tmp, "applogs")]
        config.OSSERVAZIONI_FILE = os.path.join(
            self.tmp, "logs", "account_osservazioni.json")
        config.PROJECT_DIRS_EXTRA = []
        os.makedirs(os.path.dirname(config.TOKENS_CSV), exist_ok=True)
        os.makedirs(config.PROJECTS_DIR, exist_ok=True)
        return self

    def __exit__(self, *_):
        (config.TOKENS_CSV, config.OPS_CSV, config.PROJECTS_DIR,
         config.LABELS_FILE, config.APP_LOG_DIRS,
         config.OSSERVAZIONI_FILE, config.PROJECT_DIRS_EXTRA) = self.originali
        shutil.rmtree(self.tmp, ignore_errors=True)


def test_end_to_end():
    print("Merge completo sui CSV:")
    with _Ambiente() as amb:
        # 1) sessione mai vista dagli hook: nei CSV non c'e' nulla.
        # [EN] 1) session never seen by the hooks: nothing in the CSVs.
        _scrivi_transcript(amb.tmp + "/projects", "prog", "sess-nuova", [
            _enqueue("2026-01-06T07:00:00.000Z", "ciao"),
            _assistant("m1", "2026-01-06T07:00:02.000Z", usage=_usage(5, 5, 0, 0)),
        ])
        # 2) sessione a cavallo dell'installazione: una sola riga gonfia,
        #    datata al momento dell'installazione, con l'account vero.
        # [EN] 2) session straddling the installation: one single inflated
        # row, dated at installation time, with the real account.
        _scrivi_transcript(amb.tmp + "/projects", "prog", "sess-lump", [
            _enqueue("2026-01-06T08:00:00.000Z", "primo"),
            _assistant("m2", "2026-01-06T08:00:02.000Z", usage=_usage(100, 0, 0, 0)),
            _enqueue("2026-01-06T09:00:00.000Z", "secondo"),
            _assistant("m3", "2026-01-06T09:00:02.000Z", usage=_usage(50, 0, 0, 0)),
        ])
        with open(config.TOKENS_CSV, "w", encoding="utf-8", newline="") as f:
            f.write(",".join(backfill.TOKENS_HEADER) + "\n")
            f.write("2026-01-06T09:00:05Z,sess-lump,150,0,0,0,150,mario,secondo,claude-opus-5\n")
            # 3) sessione il cui transcript non esiste piu': va conservata.
            # [EN] 3) session whose transcript no longer exists: keep it.
            f.write("2025-12-01T10:00:00Z,sess-sparita,9,1,0,0,10,mario,vecchia,claude-opus-5\n")

        stats = backfill.backfill()
        righe = backfill._read_csv(config.TOKENS_CSV, backfill.TOKENS_HEADER)
        per_sess = backfill._raggruppa(righe)

        verifica("sessione senza transcript conservata",
                 len(per_sess.get("sess-sparita", [])) == 1, per_sess.get("sess-sparita"))
        verifica("sessione mai vista recuperata",
                 len(per_sess.get("sess-nuova", [])) == 1, per_sess.get("sess-nuova"))
        verifica("etichetta di ripiego quando l'account non risulta",
                 per_sess["sess-nuova"][0]["account"] == backfill.ACCOUNT_NON_RILEVATO,
                 per_sess["sess-nuova"][0]["account"])
        verifica("riga gonfia esplosa nei turni veri",
                 len(per_sess.get("sess-lump", [])) == 2, per_sess.get("sess-lump"))
        verifica("totali invariati dopo l'esplosione",
                 sum(int(r["total_tokens"]) for r in per_sess["sess-lump"]) == 150,
                 per_sess["sess-lump"])
        # L'osservazione dell'hook (09:00:05) vale per il turno che l'ha
        # generata, finito pochi secondi prima, ma NON per quello di un'ora
        # prima: la sessione potrebbe aver attraversato un cambio di account.
        # [EN] The hook's observation (09:00:05) holds for the turn that
        # produced it, finished a few seconds earlier, but NOT for the one
        # an hour before: the session may have crossed an account switch.
        verifica("account dell'hook esteso al turno che l'ha generato",
                 per_sess["sess-lump"][1]["account"] == "mario",
                 per_sess["sess-lump"][1])
        verifica("ma non al turno di un'ora prima",
                 per_sess["sess-lump"][0]["account"] == backfill.ACCOUNT_NON_RILEVATO,
                 per_sess["sess-lump"][0])
        verifica("date rimesse al loro posto",
                 [r["timestamp"] for r in per_sess["sess-lump"]]
                 == ["2026-01-06T08:00:02Z", "2026-01-06T09:00:02Z"],
                 per_sess["sess-lump"])
        verifica("righe ordinate per data",
                 [r["timestamp"] for r in righe] == sorted(r["timestamp"] for r in righe),
                 [r["timestamp"] for r in righe])
        verifica("conteggi coerenti nel riepilogo",
                 stats["sessioni_nuove"] == 1 and stats["sessioni_riscritte"] == 1, stats)

        # 4) Idempotenza: e' la proprieta' che rende sicuro rilanciarlo.
        # [EN] 4) Idempotence: the property that makes rerunning it safe.
        prima = _leggi(config.TOKENS_CSV)
        backfill.backfill()
        backfill.backfill()
        verifica("rilanciarlo non cambia nulla",
                 _leggi(config.TOKENS_CSV) == prima, "il CSV e' cambiato al rilancio")

        verifica("copia di sicurezza creata",
                 any(f.startswith("tokens.csv.bak-")
                     for f in os.listdir(os.path.dirname(config.TOKENS_CSV))),
                 os.listdir(os.path.dirname(config.TOKENS_CSV)))


def test_ops_non_sovrascrive_il_vivo():
    """Le operazioni registrate dal vivo non vanno toccate: il loro timestamp
    e' quello dell'hook, quello ricostruito e' quello del transcript, e non
    c'e' modo di riconoscere un doppione confrontandoli. Si aggiunge percio'
    solo cio' che precede la prima operazione gia' registrata.

    [EN] Operations logged live must not be touched: their timestamp is
    the hook's, the rebuilt one is the transcript's, and there is no way
    to recognize a duplicate by comparing them. So only what precedes the
    first already-logged operation gets added."""
    print("Operazioni: solo quelle anteriori al primo log dal vivo:")
    with _Ambiente() as amb:
        _scrivi_transcript(amb.tmp + "/projects", "prog", "sess-mix", [
            _assistant("m1", "2026-01-07T10:00:00.000Z", usage=_usage(10, 0, 0, 0),
                       content=[{"type": "tool_use", "id": "t1", "name": "Read",
                                 "input": {"file_path": "prima.py"}}]),
            _assistant("m2", "2026-01-07T12:00:00.000Z", usage=_usage(10, 0, 0, 0),
                       content=[{"type": "tool_use", "id": "t2", "name": "Read",
                                 "input": {"file_path": "dopo.py"}}]),
        ])
        with open(config.OPS_CSV, "w", encoding="utf-8", newline="") as f:
            f.write(",".join(backfill.OPS_HEADER) + "\n")
            f.write("2026-01-07T11:00:00.000Z,sess-mix,Read,dopo.py,10,0,0,0,claude-opus-5\n")

        backfill.backfill()
        ops = backfill._read_csv(config.OPS_CSV, backfill.OPS_HEADER)
        target = [o["target"] for o in ops]
        verifica("aggiunta solo l'operazione pre-installazione",
                 target == ["prima.py", "dopo.py"], target)


def test_account_dal_transcript():
    """Le entry di servizio "bridge-session" (sessioni agganciate all'app o al
    web) portano con se' ownerAccountUuid: quando c'e' e' un dato vero, e va
    preferito all'etichetta di ripiego.

    [EN] The "bridge-session" service entries (sessions attached to the
    app or the web) carry ownerAccountUuid: when present it is real data,
    and it must be preferred over the fallback label."""
    print("Account ricavato dal transcript:")
    with _Ambiente() as amb:
        os.makedirs(os.path.dirname(config.LABELS_FILE), exist_ok=True)
        with open(config.LABELS_FILE, "w", encoding="utf-8") as f:
            json.dump({"uuid-noto": "mario"}, f)

        # a) uuid presente e con etichetta -> nome leggibile
        # [EN] a) uuid present and labeled -> readable name
        _scrivi_transcript(amb.tmp + "/projects", "prog", "sess-bridge", [
            _entry(type="bridge-session", sessionId="sess-bridge",
                   ownerAccountUuid="uuid-noto"),
            _assistant("m1", "2026-01-08T10:00:01.000Z", usage=_usage(3, 0, 0, 0)),
        ])
        # b) uuid presente ma senza etichetta -> resta l'uuid grezzo
        # [EN] b) uuid present but unlabeled -> the raw uuid stays
        _scrivi_transcript(amb.tmp + "/projects", "prog", "sess-ignoto", [
            _entry(type="bridge-session", sessionId="sess-ignoto",
                   ownerAccountUuid="uuid-mai-visto"),
            _assistant("m2", "2026-01-08T11:00:01.000Z", usage=_usage(3, 0, 0, 0)),
        ])
        # c) nessuna traccia -> etichetta di ripiego
        # [EN] c) no trace at all -> fallback label
        _scrivi_transcript(amb.tmp + "/projects", "prog", "sess-muta", [
            _assistant("m3", "2026-01-08T12:00:01.000Z", usage=_usage(3, 0, 0, 0)),
        ])

        stats = backfill.backfill()
        per_sess = backfill._raggruppa(
            backfill._read_csv(config.TOKENS_CSV, backfill.TOKENS_HEADER))

        verifica("uuid tradotto con account_labels.json",
                 per_sess["sess-bridge"][0]["account"] == "mario",
                 per_sess["sess-bridge"][0]["account"])
        verifica("uuid senza etichetta usato cosi' com'e'",
                 per_sess["sess-ignoto"][0]["account"] == "uuid-mai-visto",
                 per_sess["sess-ignoto"][0]["account"])
        verifica("ripiego solo quando non c'e' proprio traccia",
                 per_sess["sess-muta"][0]["account"] == backfill.ACCOUNT_NON_RILEVATO,
                 per_sess["sess-muta"][0]["account"])
        verifica("conteggi dell'account nel riepilogo",
                 stats["account_dal_transcript"] == 2 and stats["account_ignoto"] == 1,
                 stats)


def test_ripieghi_non_diventano_account():
    """I valori di ripiego gia' scritti nei CSV non vanno scambiati per
    account veri: al rilancio si deve tornare a cercare l'account da capo,
    altrimenti l'etichetta vecchia si cristallizzerebbe per sempre.

    [EN] Fallback values already written in the CSVs must not be mistaken
    for real accounts: on a rerun the account lookup must start over from
    scratch, otherwise the old label would crystallize forever."""
    print("I ripieghi non si cristallizzano:")
    with _Ambiente() as amb:
        os.makedirs(os.path.dirname(config.LABELS_FILE), exist_ok=True)
        with open(config.LABELS_FILE, "w", encoding="utf-8") as f:
            json.dump({"uuid-noto": "mario"}, f)
        _scrivi_transcript(amb.tmp + "/projects", "prog", "sess-vecchia", [
            _entry(type="bridge-session", sessionId="sess-vecchia",
                   ownerAccountUuid="uuid-noto"),
            _assistant("m1", "2026-01-09T10:00:01.000Z", usage=_usage(4, 0, 0, 0)),
        ])
        with open(config.TOKENS_CSV, "w", encoding="utf-8", newline="") as f:
            f.write(",".join(backfill.TOKENS_HEADER) + "\n")
            # "storico" e' l'etichetta di una versione precedente.
            # [EN] "storico" is the label of a previous version.
            f.write("2026-01-09T10:00:01Z,sess-vecchia,4,0,0,0,4,storico,,claude-opus-5\n")

        backfill.backfill()
        righe = backfill._read_csv(config.TOKENS_CSV, backfill.TOKENS_HEADER)
        verifica("etichetta vecchia sostituita dall'account vero",
                 righe[0]["account"] == "mario", righe[0]["account"])


LOG_APP = """\
2026-04-23 13:15:07 [info] [account] Identity changed (loggedOut: true → false, uuid: <none> → aaaaaaaa-0000-0000-0000-000000000001), clearing oauth cache
2026-05-10 09:00:00 [info] [account] Login-state transition (loggedOut: false → true, uuid: aaaaaaaa-0000-0000-0000-000000000001 → <none>), clearing oauth cache
2026-05-10 09:00:30 [info] [account] Login-state transition (loggedOut: true → false, uuid: aaaaaaaa-0000-0000-0000-000000000001 → bbbbbbbb-0000-0000-0000-000000000002), clearing oauth cache
2026-05-10 18:00:00 [info] [account] Login-state transition (loggedOut: true → false, uuid: bbbbbbbb-0000-0000-0000-000000000002 → aaaaaaaa-0000-0000-0000-000000000001), clearing oauth cache
"""


def _scrivi_log_app(base, testo=LOG_APP):
    cartella = os.path.join(base, "applogs")
    os.makedirs(cartella, exist_ok=True)
    with open(os.path.join(cartella, "main1.log"), "w", encoding="utf-8") as f:
        f.write(testo)
    config.APP_LOG_DIRS = [cartella]
    return cartella


def test_timeline_account():
    """I log dell'app registrano ogni cambio di account con data e ora: e' la
    sola fonte che copre il passato per intero.

    [EN] The app logs record every account switch with date and time: the
    only source that covers the past in full."""
    print("Timeline degli accessi dai log dell'app:")
    with _Ambiente() as amb:
        _scrivi_log_app(amb.tmp)
        tl = backfill.timeline_account()
        # 4 righe nel log, ma una e' un logout: dice che l'account e' finito,
        # non quale sara' il prossimo.
        # [EN] 4 lines in the log, but one is a logout: it says the account
        # ended, not which one comes next.
        verifica("eventi di logout ignorati (non dicono chi viene dopo)",
                 len(tl) == 3, len(tl))

        def chi(iso):
            return backfill._cerca_nella_timeline(tl, backfill._epoch(iso))

        verifica("prima del primo accesso: nessuna risposta",
                 chi("2026-04-01T10:00:00Z") is None, chi("2026-04-01T10:00:00Z"))
        verifica("dopo il primo accesso",
                 chi("2026-05-01T10:00:00Z").endswith("0001"), chi("2026-05-01T10:00:00Z"))
        # il log dell'app usa l'ora locale: 09:00:30 locale (UTC+2) =
        # 07:00:30 UTC
        # [EN] the app log uses local time: 09:00:30 local (UTC+2) =
        # [EN] 07:00:30 UTC
        verifica("cambio infragiornaliero rispettato (con fuso)",
                 chi("2026-05-10T08:00:00Z").endswith("0002"), chi("2026-05-10T08:00:00Z"))
        verifica("e ritorno all'account precedente in serata",
                 chi("2026-05-10T20:00:00Z").endswith("0001"), chi("2026-05-10T20:00:00Z"))


def test_account_per_turno():
    """Il difetto storico: una sessione ripresa a distanza di settimane veniva
    marcata tutta con l'account osservato dall'hook l'ultimo giorno. Ora ogni
    turno riceve l'account del PROPRIO momento.

    [EN] The historical defect: a session resumed weeks later used to be
    marked entirely with the account the hook observed on the last day.
    Now every turn receives the account of its OWN moment."""
    print("Account attribuito per turno, non per sessione:")
    with _Ambiente() as amb:
        _scrivi_log_app(amb.tmp)
        os.makedirs(os.path.dirname(config.LABELS_FILE), exist_ok=True)
        with open(config.LABELS_FILE, "w", encoding="utf-8") as f:
            json.dump({"aaaaaaaa-0000-0000-0000-000000000001": "primo",
                       "bbbbbbbb-0000-0000-0000-000000000002": "secondo"}, f)

        # Una sola sessione, con un turno per parte rispetto al cambio.
        # [EN] One single session, with one turn on each side of the switch.
        _scrivi_transcript(amb.tmp + "/projects", "prog", "sess-lunga", [
            _enqueue("2026-05-09T10:00:00.000Z", "prima del cambio"),
            _assistant("m1", "2026-05-09T10:00:02.000Z", usage=_usage(5, 0, 0, 0)),
            _enqueue("2026-05-10T10:00:00.000Z", "dopo il cambio"),
            _assistant("m2", "2026-05-10T10:00:02.000Z", usage=_usage(5, 0, 0, 0)),
        ])
        backfill.backfill()
        righe = sorted(backfill._read_csv(config.TOKENS_CSV, backfill.TOKENS_HEADER),
                       key=lambda r: r["timestamp"])
        verifica("due turni della stessa sessione, due account diversi",
                 [r["account"] for r in righe] == ["primo", "secondo"],
                 [(r["timestamp"], r["account"]) for r in righe])
        verifica("righe marcate come ricostruite",
                 all(r["origine"] == backfill.ORIGINE_BACKFILL for r in righe), righe)


def test_niente_propagazione_allindietro():
    """L'account osservato dall'hook vale dal turno osservato in poi, MAI
    prima: e' il difetto che marcava turni di settimane prima con l'account
    del giorno in cui l'hook ha visto la sessione per la prima volta.

    [EN] The account observed by the hook holds from the observed turn
    onwards, NEVER before: it is the defect that marked turns from weeks
    earlier with the account of the day the hook first saw the session."""
    print("L'osservazione dell'hook non si propaga all'indietro:")
    with _Ambiente() as amb:
        # Nessun log dell'app: resta solo l'osservazione dell'hook.
        # [EN] No app log: only the hook's observation remains.
        config.APP_LOG_DIRS = [os.path.join(amb.tmp, "inesistente")]
        _scrivi_transcript(amb.tmp + "/projects", "prog", "sess-ripresa", [
            _enqueue("2026-05-01T10:00:00.000Z", "turno vecchio"),
            _assistant("m1", "2026-05-01T10:00:02.000Z", usage=_usage(5, 0, 0, 0)),
            _enqueue("2026-06-20T10:00:00.000Z", "turno recente"),
            _assistant("m2", "2026-06-20T10:00:02.000Z", usage=_usage(5, 0, 0, 0)),
        ])
        with open(config.TOKENS_CSV, "w", encoding="utf-8", newline="") as f:
            f.write(",".join(backfill.TOKENS_HEADER) + "\n")
            f.write("2026-06-20T10:00:02Z,sess-ripresa,5,0,0,0,5,mario,turno recente,"
                    "claude-opus-5,hook\n")

        backfill.backfill()
        righe = sorted(backfill._read_csv(config.TOKENS_CSV, backfill.TOKENS_HEADER),
                       key=lambda r: r["timestamp"])
        verifica("il turno osservato tiene l'account dell'hook",
                 righe[1]["account"] == "mario", righe[1])
        verifica("il turno di 50 giorni prima NON lo eredita",
                 righe[0]["account"] == backfill.ACCOUNT_NON_RILEVATO, righe[0])


def test_origine_non_si_ricicla():
    """Le righe ricostruite non devono valere come prova al rilancio: sarebbe
    circolare, e cristallizzerebbe un'attribuzione sbagliata.

    [EN] Rebuilt rows must not count as evidence on a rerun: that would be
    circular, and would crystallize a wrong attribution."""
    print("Le righe ricostruite non valgono come prova:")
    with _Ambiente() as amb:
        config.APP_LOG_DIRS = [os.path.join(amb.tmp, "inesistente")]
        _scrivi_transcript(amb.tmp + "/projects", "prog", "sess-x", [
            _enqueue("2026-05-01T10:00:00.000Z", "turno"),
            _assistant("m1", "2026-05-01T10:00:02.000Z", usage=_usage(5, 0, 0, 0)),
        ])
        with open(config.TOKENS_CSV, "w", encoding="utf-8", newline="") as f:
            f.write(",".join(backfill.TOKENS_HEADER) + "\n")
            f.write("2026-05-01T10:00:02Z,sess-x,5,0,0,0,5,mario,turno,"
                    "claude-opus-5,backfill\n")
        backfill.backfill()
        righe = backfill._read_csv(config.TOKENS_CSV, backfill.TOKENS_HEADER)
        verifica("un'attribuzione ricostruita non si auto-conferma",
                 righe[0]["account"] == backfill.ACCOUNT_NON_RILEVATO, righe[0])


def test_aggancio_al_generatore():
    """run() rigenera le pagine chiamando main.main(). L'aggancio e' fragile
    perche' __init__.py riespone la funzione main() con il nome del package:
    "from generate_dashboard import main" restituisce la FUNZIONE, non il
    modulo main.py -- ed e' un errore che si manifesta solo a fine backfill,
    a dati gia' scritti.

    [EN] run() regenerates the pages by calling main.main(). The hookup is
    fragile because __init__.py re-exposes the main() function under the
    package name: "from generate_dashboard import main" returns the
    FUNCTION, not the main.py module -- and it is a mistake that shows up
    only at the end of the backfill, with data already written."""
    print("Aggancio al generatore delle pagine:")
    from generate_dashboard.main import main as genera
    verifica("main.main e' importabile e chiamabile", callable(genera), genera)


def main():
    print("Test del recupero retroattivo (backfill)\n")
    test_turni()
    test_usage_che_cresce()
    test_subagenti()
    test_cache_a_unora()
    test_alberi_extra()
    test_turno_senza_enqueue()
    test_transcript_corrotto()
    test_operazioni()
    test_end_to_end()
    test_ops_non_sovrascrive_il_vivo()
    test_account_dal_transcript()
    test_ripieghi_non_diventano_account()
    test_timeline_account()
    test_account_per_turno()
    test_niente_propagazione_allindietro()
    test_origine_non_si_ricicla()
    test_aggancio_al_generatore()

    falliti = [n for n, ok, _ in ESITI if not ok]
    print("")
    if falliti:
        print("{} test FALLITI su {}:".format(len(falliti), len(ESITI)))
        for n in falliti:
            print("  - {}".format(n))
        return 1
    print("Tutti i {} controlli passati.".format(len(ESITI)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

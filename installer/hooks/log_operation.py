#!/usr/bin/env python3
"""Hook PostToolUse: logga ogni tool call in operations.csv.

Invocato in exec form (niente shell): Claude Code passa il payload JSON
dell'evento su stdin esattamente come in shell form.

NOTA PER CHI NON CONOSCE PYTHON:
A differenza dell'hook Stop (log_tokens.py, che scatta UNA volta a fine
turno), questo hook "PostToolUse" scatta MOLTE volte per turno: una ogni
volta che Claude usa uno strumento (leggere un file, lanciare un comando,
modificare del codice...). Registra ogni singola azione come una riga a
parte in operations.csv, con il relativo costo in token se riesce a
determinarlo.

[EN] PostToolUse hook: logs every tool call to operations.csv.

Invoked in exec form (no shell): Claude Code passes the event's JSON
payload on stdin exactly as in shell form.

NOTE FOR THOSE WHO DON'T KNOW PYTHON:
Unlike the Stop hook (log_tokens.py, which fires ONCE at the end of the
turn), this "PostToolUse" hook fires MANY times per turn: once every time
Claude uses a tool (reading a file, running a command, editing code...).
It records every single action as a separate row in operations.csv, with
its token cost when it manages to determine it.
"""
import csv
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
LOG_DIR = os.path.join(HOME, ".claude", "logs")
LOG_FILE = os.path.join(LOG_DIR, "operations.csv")
PROJECTS_DIR = os.path.join(HOME, ".claude", "projects")

CSV_HEADER = [
    "timestamp", "session_id", "tool", "target",
    "input_tokens", "output_tokens", "cache_write_tokens", "cache_read_tokens", "model",
]


def extract_target(tool_input):
    """Determina "su cosa" ha agito il tool (un percorso file, un comando
    bash...), per mostrarlo come descrizione dell'azione in dashboard.

    [EN] Determines "what" the tool acted on (a file path, a bash
    command...), to show it as the action's description in the dashboard.
    """
    # tool_input varia per tool: Edit/Write/Read hanno file_path, Bash ha command.
    # "A or B or ''" prova prima file_path, poi command, e se nessuno dei
    # due c'e' usa una stringa vuota -- cosi' il resto della funzione puo'
    # sempre lavorare su una stringa vera, senza controlli su None sparsi.
    # [EN] tool_input varies per tool: Edit/Write/Read have file_path, Bash
    # [EN] has command. "A or B or ''" tries file_path first, then command,
    # [EN] and if neither is there uses an empty string -- so the rest of
    # [EN] the function can always work on a real string, without scattered
    # [EN] None checks.
    target = tool_input.get("file_path") or tool_input.get("command") or ""
    # appiattisce eventuali a-capo su una riga sola
    # [EN] flattens any newlines onto a single line
    target = re.sub(r"\s+", " ", target).strip()
    if len(target) > 200:
        target = target[:200] + "..."
    return target


def attribute_action_cost(session_id, tool_name):
    """Cerca di risalire a quanti token e' costata QUESTA specifica
    chiamata a tool, leggendo il transcript completo della sessione.

    [EN] Tries to trace back how many tokens THIS specific tool call cost,
    by reading the session's full transcript.
    """
    # Risaliamo al costo di QUESTA specifica azione: cerchiamo nel transcript
    # l'ultima entry assistant che contiene UN SOLO blocco tool_use con lo
    # stesso nome tool (ogni blocco di un messaggio multi-blocco viene
    # scritto come riga propria nel transcript, ma condivide message.id e
    # 'usage' con gli altri blocchi dello stesso messaggio -- es. 3 tool
    # paralleli nello stesso giro hanno lo stesso usage ripetuto 3 volte).
    # Dividiamo lo 'usage' per il numero di tool_use che condividono quel
    # message.id, altrimenti conteremmo lo stesso costo piu' volte.
    # [EN] We trace back the cost of THIS specific action: we look in the
    # [EN] transcript for the last assistant entry containing EXACTLY ONE
    # [EN] tool_use block with the same tool name (each block of a
    # [EN] multi-block message is written as its own transcript line, but
    # [EN] shares message.id and 'usage' with the other blocks of the same
    # [EN] message -- e.g. 3 parallel tools in the same round have the same
    # [EN] usage repeated 3 times). We divide the 'usage' by the number of
    # [EN] tool_use sharing that message.id, otherwise we would count the
    # [EN] same cost several times.

    # Il nome del file di transcript e' <session_id>.jsonl, ma non sappiamo
    # in quale sottocartella di progetto si trovi: glob con "*" cerca in
    # tutte.
    # [EN] The transcript file name is <session_id>.jsonl, but we don't
    # [EN] know which project subfolder it is in: glob with "*" searches
    # [EN] them all.
    pattern = os.path.join(PROJECTS_DIR, "*", session_id + ".jsonl")
    matches = glob.glob(pattern)
    if not matches:
        return 0, 0, 0, 0, "sconosciuto"

    try:
        # lista di tuple: (message_id, tool_name_del_blocco, usage, model)
        # [EN] list of tuples: (message_id, tool_name_of_the_block, usage,
        # [EN] model)
        entries = []
        with open(matches[0], encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if e.get("type") != "assistant":
                    continue
                msg = e.get("message") or {}
                content = msg.get("content")
                # Vogliamo SOLO i messaggi con esattamente un blocco di
                # contenuto (isinstance verifica che "content" sia
                # effettivamente una lista, len(content) != 1 scarta i
                # messaggi con piu' blocchi o senza nessuno): sono quelli
                # in cui e' inequivocabile a quale tool_use appartenga
                # quello "usage", il caso piu' semplice e affidabile.
                # [EN] We want ONLY the messages with exactly one content
                # [EN] block (isinstance verifies that "content" really is a
                # [EN] list, len(content) != 1 discards messages with several
                # [EN] blocks or with none): those are the ones where it is
                # [EN] unambiguous which tool_use that "usage" belongs to,
                # [EN] the simplest and most reliable case.
                if not isinstance(content, list) or len(content) != 1:
                    continue
                block = content[0]
                if block.get("type") != "tool_use":
                    continue
                usage = msg.get("usage")
                if not usage:
                    continue
                entries.append((msg.get("id"), block.get("name"), usage, msg.get("model") or "sconosciuto"))
    except OSError:
        return 0, 0, 0, 0, "sconosciuto"

    # Cerchiamo, PARTENDO DALLA FINE (reversed(entries): scorre la lista al
    # contrario, dall'ultima entry alla prima), la prima corrispondenza per
    # nome tool -- cioe' l'occorrenza PIU' RECENTE di questo tool nel
    # transcript, che e' quella appena successa (questo hook scatta subito
    # dopo l'esecuzione del tool).
    # [EN] We look, STARTING FROM THE END (reversed(entries): walks the
    # [EN] list backwards, from the last entry to the first), for the first
    # [EN] match by tool name -- i.e. the MOST RECENT occurrence of this
    # [EN] tool in the transcript, which is the one that just happened
    # [EN] (this hook fires right after the tool ran).
    target = None
    for e in reversed(entries):
        if e[1] == tool_name:
            target = e
            # trovata, interrompiamo subito il ciclo
            # [EN] found it, we stop the loop immediately
            break

    # NIENTE fallback all'ultima entry qualsiasi trovata: quando l'azione e'
    # stata eseguita da un sotto-agente delegato (Task/Agent), il suo
    # tool_use non compare nel transcript della sessione principale --
    # riattribuirle il costo di un'azione diversa sovrastimerebbe il turno
    # (fino a ~2x il costo vero). Meglio dichiarare "non determinabile".
    # [EN] NO fallback to whatever last entry was found: when the action was
    # [EN] performed by a delegated subagent (Task/Agent), its tool_use does
    # [EN] not appear in the main session's transcript -- attributing to it
    # [EN] the cost of a different action would overstate the turn (up to
    # [EN] ~2x its true cost). Better to declare "not determinable".
    if target is None:
        return 0, 0, 0, 0, "n/d"

    msg_id, _, usage, model = target
    # "_" come nome di variabile e' una convenzione Python per dire
    # "questo valore lo ignoro apposta, non mi serve" -- qui e' il nome del
    # tool nella tupla "target", che non ci serve piu' avendolo gia' usato
    # per trovarla.
    #
    # Contiamo quante entry condividono lo stesso message.id di "target"
    # (cioe' quanti blocchi tool_use erano nello stesso messaggio, es. 3
    # tool lanciati in parallelo): il loro "usage" e' lo stesso ripetuto,
    # quindi va DIVISO per questo numero per non contare lo stesso costo
    # piu' volte complessivamente. max(1, ...) garantisce di non dividere
    # mai per zero.
    # [EN] "_" as a variable name is a Python convention meaning "I ignore
    # [EN] this value on purpose, I don't need it" -- here it is the tool
    # [EN] name inside the "target" tuple, which we no longer need having
    # [EN] already used it to find it.
    # [EN]
    # [EN] We count how many entries share the same message.id as "target"
    # [EN] (i.e. how many tool_use blocks were in the same message, e.g. 3
    # [EN] tools launched in parallel): their "usage" is the same one
    # [EN] repeated, so it must be DIVIDED by this number so as not to count
    # [EN] the same cost several times overall. max(1, ...) guarantees we
    # [EN] never divide by zero.
    n = max(1, sum(1 for e in entries if e[0] == msg_id))
    return (
        round(usage.get("input_tokens", 0) / n),
        round(usage.get("output_tokens", 0) / n),
        round(usage.get("cache_creation_input_tokens", 0) / n),
        round(usage.get("cache_read_input_tokens", 0) / n),
        model,
    )


def append_csv_row(row):
    write_header = not os.path.exists(LOG_FILE)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(CSV_HEADER)
        writer.writerow(row)


def main():
    # Vedi commento analogo in log_tokens.py: alcune macchine consegnano il
    # payload con un BOM UTF-8 in testa, che json.load rifiuta esplicitamente.
    # [EN] See the analogous comment in log_tokens.py: some machines deliver
    # [EN] the payload with a UTF-8 BOM at the start, which json.load
    # [EN] explicitly rejects.
    payload = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
    session_id = payload.get("session_id", "?")
    tool_name = payload.get("tool_name", "?")
    target = extract_target(payload.get("tool_input", {}) or {})
    now = datetime.now(timezone.utc)
    # Timestamp con i millisecondi (a differenza di log_tokens.py, che non
    # ne ha bisogno essendo un evento singolo per turno): con molte
    # operazioni nello stesso secondo, i millisecondi aiutano a distinguerne
    # l'ordine esatto in dashboard. now.microsecond // 1000 converte i
    # microsecondi (0-999999) in millisecondi (0-999) con una divisione
    # intera (//, che scarta il resto); ":03d" li scrive sempre su 3 cifre
    # (es. "007").
    # [EN] Timestamp with milliseconds (unlike log_tokens.py, which does not
    # [EN] need them, being a single event per turn): with many operations
    # [EN] within the same second, milliseconds help tell their exact order
    # [EN] apart in the dashboard. now.microsecond // 1000 converts the
    # [EN] microseconds (0-999999) into milliseconds (0-999) with an integer
    # [EN] division (//, which discards the remainder); ":03d" always writes
    # [EN] them on 3 digits (e.g. "007").
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"

    act_input, act_output, act_cw, act_cr, act_model = attribute_action_cost(session_id, tool_name)

    append_csv_row([
        timestamp, session_id, tool_name, target,
        act_input, act_output, act_cw, act_cr, act_model,
    ])


if __name__ == "__main__":
    main()

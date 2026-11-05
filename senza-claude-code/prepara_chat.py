"""Scarica il registro Classeviva e prepara un messaggio da incollare in una chat di claude.ai
(va bene anche il piano gratuito) per farsi organizzare lo studio.

Uso:  python prepara_chat.py
Tutto resta in questa cartella: orario.md (il tuo orario), .env (nome utente e password, se scegli di salvarli),
stato.json (cosa hai già visto) e chat/ (i messaggi preparati).
"""

import asyncio
import getpass
import os
import json
import platform
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from classeviva import Utente

CARTELLA = Path(__file__).resolve().parent
FILE_ENV = CARTELLA / ".env"
STATO = CARTELLA / "stato.json"
GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
MATERIE_NON_DIDATTICHE = {"SOSTEGNO", "SUPPLENZA", "EDUCAZIONE CIVICA"}
PAROLE_VERIFICA = re.compile(r"verific|interrog|compito in classe|test\b|prova\b", re.I)

REGOLE = """\
Come voglio il piano di studio:
- Studio di pomeriggio, di solito 15:00-19:30, dopo l'uscita da scuola, il pranzo e una pausa. Togli gli impegni che ti scrivo e metti 10 minuti di pausa ogni ora.
- Prima i compiti per domani, poi la preparazione delle prove in arrivo, poi il ripasso delle materie deboli (media sotto 6 o in calo).
- Tempi indicativi: un esercizio di matematica 5-8 min, una pagina di teoria 10 min; per un'interrogazione 45-60 min al giorno nei 3 giorni prima; per una verifica scritta 60 min al giorno nei 4 giorni prima, più gli esercizi.
- Distribuisci lo studio per le prove sui giorni prima, mai tutto l'ultimo giorno. La sera prima solo un ripasso leggero.
- Le voci di agenda hanno la data del giorno in cui vanno consegnate, non di quando il prof le scrive: un compito datato lunedì è per lunedì, una verifica è datata al giorno della prova. Se il testo dà una data esplicita, vale quella.
- Segui anche le regole scritte sotto l'orario.
- Se il tempo non basta, dimmelo chiaramente e proponi cosa tagliare o anticipare.

Rispondi in italiano, in modo diretto e incoraggiante, con:
1. Novità dal registro (voti nuovi, nuove voci in agenda)
2. Compiti per domani e scadenze dei prossimi giorni
3. Verifiche e interrogazioni in arrivo
4. Su cosa concentrarmi (2-4 priorità motivate)
5. Piano di studio: oggi con gli orari dei blocchi, poi i giorni successivi fino alla prossima prova"""


def credenziali() -> tuple[str, str]:
    """Dalle variabili CLASSEVIVA_UTENTE / CLASSEVIVA_PASSWORD, dal file .env o, la prima volta, chieste a te."""
    env = dict(os.environ)
    if FILE_ENV.exists():
        for riga in FILE_ENV.read_text().splitlines():
            if "=" in riga and not riga.startswith("#"):
                k, v = riga.split("=", 1)
                env.setdefault(k.strip(), v.strip())
    if env.get("CLASSEVIVA_UTENTE") and env.get("CLASSEVIVA_PASSWORD"):
        return env["CLASSEVIVA_UTENTE"], env["CLASSEVIVA_PASSWORD"]

    print("Serve il tuo accesso a Classeviva (lo stesso del sito o dell'app).")
    utente = input("Nome utente (es. S1234567X o la tua email): ").strip()
    password = getpass.getpass("Password (mentre scrivi non si vede niente, è normale): ")
    if input("Li salvo in questa cartella, così la prossima volta non te li chiedo? [s/n] ").strip().lower().startswith("s"):
        FILE_ENV.write_text(f"CLASSEVIVA_UTENTE={utente}\nCLASSEVIVA_PASSWORD={password}\n")
        try:
            FILE_ENV.chmod(0o600)  # leggibile solo da te
        except OSError:
            pass
        print(f"Salvati in {FILE_ENV}. Non dare a nessuno questo file.")
    return utente, password


def valore(voto: dict) -> float | None:
    """Converte un voto in numero (es. "6+" -> 6.25, "6½" -> 6.5). None se non fa media."""
    if voto["canceled"] or voto["noAverage"]:
        return None
    if voto["decimalValue"] is not None:
        return float(voto["decimalValue"])
    m = re.fullmatch(r"(\d+)\s*(\+|-|½|1/2)?", (voto["displayValue"] or "").strip())
    if not m:
        return None
    return float(m.group(1)) + {"+": 0.25, "-": -0.25, "½": 0.5, "1/2": 0.5, None: 0}[m.group(2)]


def media(voti: list[dict]) -> float | None:
    coppie = [(valore(v), v["weightFactor"] or 1) for v in voti]
    coppie = [(n, p) for n, p in coppie if n is not None]
    if not coppie:
        return None
    return round(sum(n * p for n, p in coppie) / sum(p for _, p in coppie), 2)


def inizio_anno_scolastico(oggi: date) -> date:
    return date(oggi.year if oggi.month >= 9 else oggi.year - 1, 9, 1)


async def scarica(oggi: date) -> dict:
    utente = Utente(*credenziali())
    try:
        await utente.accedi()
    except Exception as e:
        motivo = "nome utente o password sbagliati" if "password" in str(e).lower() else f"errore: {type(e).__name__}"
        if FILE_ENV.exists():
            FILE_ENV.unlink()
            sys.exit(f"Accesso a Classeviva non riuscito ({motivo}). Ho cancellato il nome utente e la password salvati: "
                     "rilancia lo script e rimettili.")
        sys.exit(f"Accesso a Classeviva non riuscito ({motivo}). Controlla e riprova.")
    return {
        "voti": await utente.voti(f"{inizio_anno_scolastico(oggi).year % 100:02d}"),
        "materie": await utente.materie(),
        "calendario": await utente.calendario_da_a(oggi.isoformat(), (oggi + timedelta(days=14)).isoformat()),
        "agenda": await utente.agenda_da_a((oggi - timedelta(days=7)).isoformat(), (oggi + timedelta(days=30)).isoformat()),
        "lezioni_oggi": await utente.lezioni_giorno(oggi.isoformat()),
    }


def chiedi(domanda: str) -> str:
    print(domanda)
    righe = []
    while (riga := input("> ").strip()):
        righe.append(riga)
    return "\n".join(righe) or "nessuno"


def copia_negli_appunti(testo: str) -> bool:
    sistema = platform.system()
    comandi = {"Windows": [["clip"]], "Darwin": [["pbcopy"]]}.get(sistema, [["wl-copy"], ["xclip", "-selection", "clipboard"]])
    for comando in comandi:
        try:
            # clip di Windows vuole UTF-16, altrimenti le lettere accentate si rovinano
            dati = testo.encode("utf-16-le" if sistema == "Windows" else "utf-8")
            subprocess.run(comando, input=dati, check=True)
            return True
        except (OSError, subprocess.CalledProcessError):
            continue
    return False


def main():
    oggi = date.today()
    file_orario = CARTELLA / "orario.md"
    if not file_orario.exists():
        sys.exit(f"Manca {file_orario}: scrivi lì il tuo orario (guarda il LEGGIMI).")
    d = asyncio.run(scarica(oggi))

    stato = json.loads(STATO.read_text()) if STATO.exists() else {}
    primo = not stato
    voti_visti, agenda_vista = set(stato.get("voti_visti", [])), set(stato.get("agenda_vista", []))

    # Docente -> materie (le voci di agenda spesso non hanno la materia)
    docente_materie = defaultdict(set)
    for m in d["materie"]:
        if m["description"] not in MATERIE_NON_DIDATTICHE:
            for doc in m["teachers"]:
                docente_materie[doc["teacherName"]].add(m["description"])

    per_materia = defaultdict(list)
    for v in d["voti"]:
        per_materia[v["subjectDesc"]].append(v)
    righe_voti = []
    for nome, lista in sorted(per_materia.items()):
        lista.sort(key=lambda v: v["evtDate"])
        nuovi = [v for v in lista if v["evtId"] not in voti_visti and not primo]
        voti = ", ".join(f"{v['displayValue']}{' (NUOVO)' if v in nuovi else ''}" for v in lista)
        prima = f", prima dei voti nuovi era {media([v for v in lista if v not in nuovi])}" if nuovi else ""
        righe_voti.append(f"- {nome}: {voti} → media {media(lista)}{prima}")

    righe_agenda = []
    for e in sorted(d["agenda"], key=lambda e: e["evtDatetimeBegin"]):
        data, testo = e["evtDatetimeBegin"][:10], e["notes"] or ""
        if data < (oggi - timedelta(days=3)).isoformat() and not PAROLE_VERIFICA.search(testo):
            continue
        materia = e["subjectDesc"] or " / ".join(sorted(docente_materie.get(e["authorName"], []))) or "?"
        nuovo = " (NUOVO)" if e["evtId"] not in agenda_vista and not primo else ""
        righe_agenda.append(f"- scritta il {data} · {materia}{nuovo}: {testo}")

    lezioni = [f"- {l['evtHPos']}ª ora {l['subjectDesc']}: {l['lessonArg'] or '(argomento non scritto)'}"
               for l in sorted(d["lezioni_oggi"], key=lambda l: l["evtHPos"]) if l["subjectDesc"] not in MATERIE_NON_DIDATTICHE]
    senza_scuola = [c["dayDate"] for c in d["calendario"] if c["dayStatus"] != "SD"]
    ultimo = stato.get("data")
    novita = "primo controllo: niente è segnato come nuovo" if primo else f"ultimo controllo il {ultimo}, le cose nuove sono segnate (NUOVO)"

    print(f"\nRegistro scaricato ({GIORNI[oggi.weekday()]} {oggi:%d/%m}).\n")
    impegni = chiedi("Che impegni hai oggi pomeriggio e nei prossimi giorni? Una riga per impegno, con giorno e orario. Riga vuota per finire.")
    extra = chiedi("\nCose che non sono sul registro (compiti o verifiche detti solo in classe)? Riga vuota per finire.")

    messaggio = f"""Ciao! Sono uno studente delle superiori. Organizzami lo studio partendo dal mio registro.
Oggi è {GIORNI[oggi.weekday()]} {oggi:%d/%m/%Y} ({novita}).

{REGOLE}

MIEI IMPEGNI
{impegni}

COSE NON SUL REGISTRO (le ho scritte io)
{extra}

AGENDA DEL REGISTRO (ultimi giorni e prossimi 30)
{chr(10).join(righe_agenda) or 'vuota'}

LEZIONI DI OGGI
{chr(10).join(lezioni) or 'non ancora scritte sul registro'}

VOTI E MEDIE (stime: + vale 0.25, ½ vale 0.5)
{chr(10).join(righe_voti) or 'nessun voto'}

GIORNI SENZA SCUOLA NELLE PROSSIME 2 SETTIMANE
{', '.join(senza_scuola) or 'nessuno'}

MIO ORARIO E REGOLE PER PIANIFICARE
{file_orario.read_text(encoding="utf-8")}"""

    (CARTELLA / "chat").mkdir(exist_ok=True)
    file = CARTELLA / "chat" / f"{oggi.isoformat()}.txt"
    file.write_text(messaggio, encoding="utf-8")
    STATO.write_text(json.dumps({
        "data": oggi.isoformat(),
        "voti_visti": sorted(v["evtId"] for v in d["voti"]),
        "agenda_vista": sorted(agenda_vista | {e["evtId"] for e in d["agenda"]}),
    }))

    dove = "è negli appunti" if copia_negli_appunti(messaggio) else "non sono riuscito a copiarlo negli appunti: aprilo dal file e copialo tu"
    print(f"\nFatto! Il messaggio {dove}.\nApri claude.ai, incollalo in una chat nuova e invia.\nUna copia è in {file}")


main()

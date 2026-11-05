"""Scarica da Classeviva tutto quello che serve al report giornaliero e lo stampa come JSON.

Uso: ~/Scuola/venv/bin/python scarica_registro.py [--salva-stato]

Credenziali: variabili CLASSEVIVA_UTENTE / CLASSEVIVA_PASSWORD, altrimenti ~/Scuola/.env.
Con --salva-stato aggiorna ~/Scuola/report/stato.json, usato per capire cosa è nuovo dal controllo precedente.
"""
import asyncio
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

from classeviva import Utente

SCUOLA = Path.home() / "Scuola"
STATO = SCUOLA / "report" / "stato.json"
GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
MATERIE_NON_DIDATTICHE = {"SOSTEGNO", "SUPPLENZA", "EDUCAZIONE CIVICA"}
PAROLE_VERIFICA = re.compile(r"verific|interrog|compito in classe|test\b|prova\b", re.I)


def credenziali() -> tuple[str, str]:
    env = dict(os.environ)
    file_env = SCUOLA / ".env"
    if file_env.exists():
        for riga in file_env.read_text().splitlines():
            if "=" in riga and not riga.startswith("#"):
                k, v = riga.split("=", 1)
                env.setdefault(k.strip(), v.strip())
    return env["CLASSEVIVA_UTENTE"], env["CLASSEVIVA_PASSWORD"]


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


async def main():
    salva = "--salva-stato" in sys.argv
    oggi = date.today()
    utente = Utente(*credenziali())
    await utente.accedi()

    voti = await utente.voti(f"{inizio_anno_scolastico(oggi).year % 100:02d}")
    materie = await utente.materie()
    periodi = await utente.periodi()
    note = await utente.note()
    calendario = await utente.calendario_da_a(oggi.isoformat(), (oggi + timedelta(days=21)).isoformat())
    agenda = await utente.agenda_da_a((oggi - timedelta(days=7)).isoformat(), (oggi + timedelta(days=30)).isoformat())
    lezioni_oggi = await utente.lezioni_giorno(oggi.isoformat())
    lezioni_recenti = await utente.lezioni_da_a(
        max(inizio_anno_scolastico(oggi), oggi - timedelta(days=21)).isoformat(), oggi.isoformat()
    )

    # Docente -> materie (le agende di Classeviva spesso non hanno la materia)
    docente_materie = defaultdict(set)
    for m in materie:
        if m["description"] in MATERIE_NON_DIDATTICHE:
            continue
        for d in m["teachers"]:
            docente_materie[d["teacherName"]].add(m["description"])

    # Orario tipico ricostruito dalle lezioni delle ultime settimane: giorno -> ora -> materia
    conteggi = defaultdict(Counter)
    for l in lezioni_recenti:
        if l["subjectDesc"] in MATERIE_NON_DIDATTICHE:
            continue
        g = date.fromisoformat(l["evtDate"]).weekday()
        conteggi[(g, l["evtHPos"])][l["subjectDesc"]] += 1
    orario = defaultdict(dict)
    for (g, ora), c in sorted(conteggi.items()):
        orario[GIORNI[g]][ora] = c.most_common(1)[0][0]

    # Voti per materia, con media prima/dopo i voti nuovi rispetto all'ultimo controllo
    stato = json.loads(STATO.read_text()) if STATO.exists() else {}
    visti = set(stato.get("voti_visti", []))
    primo_controllo = not stato
    per_materia = defaultdict(list)
    for v in voti:
        per_materia[v["subjectDesc"]].append(v)
    riepilogo = {}
    for nome, lista in sorted(per_materia.items()):
        lista.sort(key=lambda v: v["evtDate"])
        nuovi = [v for v in lista if v["evtId"] not in visti and not primo_controllo]
        vecchi = [v for v in lista if v not in nuovi]
        riepilogo[nome] = {
            "voti": [
                {"data": v["evtDate"], "voto": v["displayValue"], "valore": valore(v), "tipo": v["componentDesc"],
                 "periodo": v["periodLabel"], "nota": v["notesForFamily"], "nuovo": v in nuovi}
                for v in lista
            ],
            "media": media(lista),
            "media_precedente": media(vecchi) if nuovi else None,
            "media_periodo_corrente": media([v for v in lista if v["periodPos"] == lista[-1]["periodPos"]]),
        }

    eventi = []
    for e in sorted(agenda, key=lambda e: e["evtDatetimeBegin"]):
        eventi.append({
            "id": e["evtId"],
            "data": e["evtDatetimeBegin"][:10],
            "ora": e["evtDatetimeBegin"][11:16],
            "tipo_registro": e["evtCode"],
            "docente": e["authorName"],
            "materia": e["subjectDesc"] or " / ".join(sorted(docente_materie.get(e["authorName"], []))) or None,
            "testo": e["notes"],
            "sembra_verifica_o_interrogazione": bool(PAROLE_VERIFICA.search(e["notes"] or "")),
            "nuovo": e["evtId"] not in set(stato.get("agenda_vista", [])) and not primo_controllo,
        })

    risultato = {
        "oggi": oggi.isoformat(),
        "giorno_settimana": GIORNI[oggi.weekday()],
        "primo_controllo": primo_controllo,
        "ultimo_controllo": stato.get("data"),
        "periodi": [{"nome": p["periodLabel"], "inizio": p["dateStart"], "fine": p["dateEnd"]} for p in periodi],
        "calendario_scolastico": [
            {"data": c["dayDate"], "scuola": c["dayStatus"] == "SD", "stato": c["dayStatus"]} for c in calendario
        ],
        "orario_tipico": orario,
        "lezioni_oggi": [
            {"ora": l["evtHPos"], "materia": l["subjectDesc"], "docente": l["authorName"], "argomento": l["lessonArg"]}
            for l in sorted(lezioni_oggi, key=lambda l: l["evtHPos"]) if l["subjectDesc"] not in MATERIE_NON_DIDATTICHE
        ],
        "agenda": eventi,
        "materie": riepilogo,
        "note_disciplinari": {k: v for k, v in note.items() if v},
    }
    print(json.dumps(risultato, ensure_ascii=False, indent=1))

    if salva:
        STATO.parent.mkdir(parents=True, exist_ok=True)
        STATO.write_text(json.dumps({
            "data": oggi.isoformat(),
            "voti_visti": sorted(v["evtId"] for v in voti),
            "agenda_vista": sorted(set(stato.get("agenda_vista", [])) | {e["evtId"] for e in agenda}),
        }))


asyncio.run(main())

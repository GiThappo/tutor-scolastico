"""Scarica da Classeviva cosa si è fatto a lezione, materia per materia, e lo stampa come JSON.

Uso: ~/Scuola/venv/bin/python lezioni.py [--giorni N] [--salva-stato]

Senza --giorni prende le lezioni dal controllo precedente (o degli ultimi 14 giorni al primo controllo).
Scarica anche il materiale caricato dai prof nella sezione Didattica in ~/Scuola/materiale/<Materia>/dal-prof/.
Con --salva-stato aggiorna ~/Scuola/materiale/stato.json, così il prossimo controllo sa cosa è nuovo.

Credenziali: variabili CLASSEVIVA_UTENTE / CLASSEVIVA_PASSWORD, altrimenti ~/Scuola/.env.
"""
import argparse
import asyncio
import json
import os
import re
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from classeviva import Utente

SCUOLA = Path.home() / "Scuola"
MATERIALE = SCUOLA / "materiale"
STATO = MATERIALE / "stato.json"
MATERIE_NON_DIDATTICHE = {"SOSTEGNO", "SUPPLENZA"}
CARTELLE = {
    "LINGUA E LETTERATURA ITALIANA": "Italiano",
    "STORIA": "Storia",
    "LINGUA INGLESE": "Inglese",
    "MATEMATICA E COMPLEMENTI DI MATEMATICA": "Matematica",
    "INFORMATICA": "Informatica",
    "SISTEMI E RETI": "Sistemi e reti",
    "TELECOMUNICAZIONI": "Telecomunicazioni",
    "TECNOLOGIE E PROGETTAZIONE DI SISTEMI INFORMATICI E DI TELECOMUNICAZIONI": "TPSIT",
    "SCIENZE MOTORIE E SPORTIVE": "Scienze motorie",
    "RELIGIONE CATTOLICA  O ATTIVITA' ALTERNATIVE": "Religione",
    "EDUCAZIONE CIVICA": "Educazione civica",
}


def credenziali() -> tuple[str, str]:
    env = dict(os.environ)
    file_env = SCUOLA / ".env"
    if file_env.exists():
        for riga in file_env.read_text().splitlines():
            if "=" in riga and not riga.startswith("#"):
                k, v = riga.split("=", 1)
                env.setdefault(k.strip(), v.strip())
    return env["CLASSEVIVA_UTENTE"], env["CLASSEVIVA_PASSWORD"]


def cartella(materia: str) -> str:
    return CARTELLE.get(materia, materia.strip().capitalize())


def nome_file(testo: str) -> str:
    return re.sub(r"[^\w.\- ]+", "_", testo).strip()[:100] or "file"


def leggi_stato() -> dict:
    if STATO.exists():
        return json.loads(STATO.read_text())
    return {}


async def scarica_didattica(utente: Utente, visti: set[int]) -> list[dict]:
    """Scarica i file nuovi della sezione Didattica. Ritorna l'elenco di tutti i contenuti trovati."""
    try:
        docenti = await utente.didattica()
    except Exception as e:  # la sezione può essere disattivata dalla scuola
        return [{"errore": f"didattica non disponibile: {e}"}]
    contenuti = []
    for docente in docenti or []:
        for cartella_prof in docente.get("folders", []):
            for c in cartella_prof.get("contents", []):
                voce = {
                    "id": c.get("contentId"),
                    "docente": docente.get("teacherName"),
                    "cartella": cartella_prof.get("folderName"),
                    "nome": c.get("contentName"),
                    "tipo": c.get("objectType"),
                    "data": (c.get("shareDT") or "")[:10],
                    "nuovo": c.get("contentId") not in visti,
                    "file": None,
                }
                if voce["tipo"] == "file" and voce["nuovo"]:
                    risposta = utente._sessione.get(
                        f"https://web.spaggiari.eu/rest/v1/students/{utente._id}/didactics/item/{voce['id']}"
                    )
                    if risposta.ok:
                        dest = MATERIALE / "_da-smistare" / "dal-prof" / nome_file(voce["nome"])
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(risposta.content)
                        voce["file"] = str(dest)
                contenuti.append(voce)
    return contenuti


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--giorni", type=int)
    parser.add_argument("--salva-stato", action="store_true")
    args = parser.parse_args()

    oggi = date.today()
    stato = leggi_stato()
    if args.giorni:
        inizio = oggi - timedelta(days=args.giorni)
    elif stato.get("ultimo_controllo"):
        inizio = date.fromisoformat(stato["ultimo_controllo"]) - timedelta(days=1)
    else:
        inizio = oggi - timedelta(days=14)

    utente = Utente(*credenziali())
    await utente.accedi()
    lezioni = await utente.lezioni_da_a(inizio.isoformat(), oggi.isoformat())
    lezioni_viste = set(stato.get("lezioni_viste", []))

    per_materia: dict[str, dict] = defaultdict(lambda: {"cartella": "", "docenti": set(), "lezioni": {}})
    for l in lezioni:
        materia = l["subjectDesc"]
        if materia in MATERIE_NON_DIDATTICHE:
            continue
        m = per_materia[materia]
        m["cartella"] = cartella(materia)
        m["docenti"].add(l["authorName"])
        argomento = (l.get("lessonArg") or "").strip()
        chiave = (l["evtDate"], argomento.lower())
        voce = m["lezioni"].setdefault(chiave, {
            "data": l["evtDate"], "ore": [], "argomento": argomento,
            "tipo": l.get("lessonType"), "nuova": False, "id": [],
        })
        voce["ore"].append(l["evtHPos"])
        voce["id"].append(l["evtId"])
        voce["nuova"] |= l["evtId"] not in lezioni_viste

    risultato = {
        "oggi": oggi.isoformat(),
        "dal": inizio.isoformat(),
        "primo_controllo": not stato,
        "cartella_materiale": str(MATERIALE),
        "materie": {
            materia: {
                "cartella": str(MATERIALE / m["cartella"]),
                "docenti": sorted(m["docenti"]),
                "lezioni": sorted(
                    ({**v, "ore": sorted(v["ore"])} for v in m["lezioni"].values()),
                    key=lambda v: v["data"], reverse=True,
                ),
                "argomenti_mancanti": sum(1 for v in m["lezioni"].values() if not v["argomento"]),
            }
            for materia, m in sorted(per_materia.items())
        },
        "didattica": await scarica_didattica(utente, set(stato.get("didattica_vista", []))),
    }
    print(json.dumps(risultato, ensure_ascii=False, indent=1))

    if args.salva_stato:
        MATERIALE.mkdir(parents=True, exist_ok=True)
        tutti_id = {i for m in risultato["materie"].values() for v in m["lezioni"] for i in v["id"]}
        STATO.write_text(json.dumps({
            "ultimo_controllo": oggi.isoformat(),
            "lezioni_viste": sorted(lezioni_viste | tutti_id),
            "didattica_vista": sorted(
                set(stato.get("didattica_vista", []))
                | {d["id"] for d in risultato["didattica"] if d.get("id") is not None}
            ),
        }, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())

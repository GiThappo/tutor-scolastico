#!/usr/bin/env python3
"""Prepara da riassumere le circolari della bacheca che non hanno ancora un riassunto.

Uso: scarica_bacheca.py [cartella]     (cartella di default: ~/Scuola)

Per ogni circolare senza riassunto in <cartella>/bacheca/riassunti.json crea
<cartella>/bacheca/da_riassumere/<id>/ con info.json, testo.txt e gli allegati.

Attenzione: Classeviva dà i documenti solo dopo la lettura, quindi le circolari
aperte da qui risultano lette dallo studente. In info.json resta "era_letta",
lo stato di prima. Lo script non firma e non aderisce a niente.
"""
import asyncio
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

from classeviva import Utente

MAX_TESTO = 12000


def nome_sicuro(nome: str) -> str:
    pulito = Path(re.sub(r"[^\w.\- ]", "_", nome))
    return f"{pulito.stem[:100]}{pulito.suffix}" or "allegato"


def testo_pdf(percorso: Path) -> str:
    uscita = subprocess.run(["pdftotext", "-layout", str(percorso), "-"], capture_output=True, text=True, timeout=60)
    return re.sub(r"[ \t]{2,}", "  ", uscita.stdout)


def testo_intero(percorso: Path) -> str:
    """Tutto il testo di un allegato, anche Word: serve solo a cercarci nomi e classi."""
    estensione = percorso.suffix.lower()
    if estensione == ".pdf":
        return testo_pdf(percorso)
    if estensione == ".docx":
        with zipfile.ZipFile(percorso) as z:
            return re.sub(r"<[^>]+>", " ", z.read("word/document.xml").decode("utf-8", "ignore"))
    if estensione == ".doc":
        dati = percorso.read_bytes()
        return dati.decode("latin-1", "ignore") + dati.decode("utf-16-le", "ignore")
    return ""


def cercatori() -> tuple[re.Pattern | None, re.Pattern | None]:
    """Da STUDENTE e CLASSE di app.env: 'Cognome Nome' vale in entrambi gli ordini, una sigla come '1XY' anche come '1X YZ' o '1^X YZ'."""
    env = {}
    file_env = Path.home() / "Scuola" / "app.env"
    if file_env.exists():
        for riga in file_env.read_text().splitlines():
            if "=" in riga:
                k, v = riga.split("=", 1)
                env[k.strip()] = v.strip().strip("\"'")
    studente, classe = env.get("STUDENTE", "").split(), env.get("CLASSE", "")
    nome = None
    if len(studente) >= 2:
        a, b = re.escape(studente[0]), re.escape(" ".join(studente[1:]))
        nome = re.compile(rf"{a}\s+{b}|{b}\s+{a}", re.I)
    sigla = None
    if len(classe) >= 2:
        resto = re.escape(classe[2:])
        sigla = re.compile(rf"\b{classe[0]}\s*[\^°ª]?\s*{classe[1]}\s*{resto}[A-Z]*\b")
    return nome, sigla


async def prepara(utente: Utente, voce: dict, cartella: Path, nome: re.Pattern | None, sigla: re.Pattern | None) -> None:
    cartella.mkdir(parents=True, exist_ok=True)
    info_file = cartella / "info.json"
    # Se un giro precedente si è interrotto, lo stato vero è quello salvato allora
    era_letta = json.loads(info_file.read_text())["era_letta"] if info_file.exists() else voce["readStatus"]
    letta = await utente.bacheca_leggi(voce["evtCode"], voce["pubId"])
    parti = [str((letta.get("item") or {}).get("text") or "").strip()]
    allegati = []
    intero = parti[0]
    for a in voce.get("attachments") or []:
        if a["fileName"].lower().startswith("annotazione_"):
            continue
        dati = await utente.bacheca_allega_(voce["evtCode"], voce["pubId"], a["attachNum"])
        percorso = cartella / f"{a['attachNum']}-{nome_sicuro(a['fileName'])}"
        percorso.write_bytes(dati)
        allegati.append(percorso.name)
        intero += "\n" + testo_intero(percorso)
        if percorso.suffix.lower() == ".pdf":
            parti.append(f"--- {a['fileName']} ---\n{testo_pdf(percorso)}")
    testo = "\n\n".join(p for p in parti if p.strip())
    (cartella / "testo.txt").write_text(testo[:MAX_TESTO])
    info_file.write_text(json.dumps({
        "id": voce["pubId"], "titolo": voce["cntTitle"], "data": voce["pubDT"][:10], "era_letta": era_letta,
        "richiede": {k: voce.get(k) for k in ("needSign", "needJoin", "needReply", "needFile")},
        "allegati": allegati, "caratteri_testo": len(testo.strip()),
        "studente_citato": bool(nome and nome.search(intero)), "classe_citata": bool(sigla and sigla.search(intero)),
    }, ensure_ascii=False, indent=1))


async def main() -> None:
    base = Path(sys.argv[1] if len(sys.argv) > 1 else Path.home() / "Scuola") / "bacheca"
    file_riassunti = base / "riassunti.json"
    riassunti = json.loads(file_riassunti.read_text()) if file_riassunti.exists() else {}
    utente = Utente(os.environ["CLASSEVIVA_UTENTE"], os.environ["CLASSEVIVA_PASSWORD"])
    await utente.accedi()
    voci = [v for v in await utente.bacheca() if v.get("cntStatus") != "deleted" and str(v["pubId"]) not in riassunti]
    errori = 0
    nome, sigla = cercatori()
    for voce in voci:
        try:
            await prepara(utente, voce, base / "da_riassumere" / str(voce["pubId"]), nome, sigla)
        except Exception as e:  # una circolare che non si apre non deve fermare le altre
            errori += 1
            print(f"ERRORE {voce['pubId']} {voce['cntTitle'][:60]}: {type(e).__name__}", file=sys.stderr)
    print(f"Da riassumere: {len(voci) - errori} in {base / 'da_riassumere'}. Errori: {errori}.")


asyncio.run(main())

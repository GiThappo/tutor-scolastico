# Tutor scolastico per Claude Code

Due skill per [Claude Code](https://claude.com/claude-code) che trasformano Claude in un tutor per chi va alle superiori e usa il registro elettronico **Classeviva** (Spaggiari).

| Skill | Cosa fa |
|---|---|
| `/registro-giornaliero` | Legge il registro (voti, agenda, lezioni, note), scrive il report del giorno in `~/Scuola/report/`, calcola le medie e le tendenze per materia, trova verifiche e interrogazioni in arrivo e pianifica lo studio in Google Calendar in base ai tuoi impegni del pomeriggio. |
| `/materiale-lezioni` | Guarda cosa si è fatto a lezione in ogni materia, ti chiede gli appunti, cerca e scarica materiale affidabile dal web e scrive una scheda di studio per ogni argomento in `~/Scuola/materiale/<Materia>/`. |

Le skill parlano in italiano e funzionano anche se le chiedi a parole ("fammi il report di oggi", "cosa abbiamo fatto di storia questa settimana?").

## Requisiti

- Python 3.11 o più recente
- Un account Classeviva da studente
- **Claude Code**, che richiede un piano Claude a pagamento (Pro o superiore) oppure una chiave API. Con Claude Code è tutto automatico. Senza, si può usare la versione gratuita di claude.ai facendo a mano qualche passaggio: vedi [Senza Claude a pagamento](#senza-claude-a-pagamento).
- Per il piano di studio: il connettore **Google Calendar** attivo in Claude (senza, il report funziona lo stesso)

## Installazione

```bash
git clone https://github.com/GiThappo/tutor-scolastico.git
cd tutor-scolastico
./install.sh
```

Lo script:

1. crea `~/Scuola/venv` e ci installa [Classeviva.py](https://pypi.org/project/Classeviva.py/);
2. collega le skill in `~/.claude/skills/` (con link simbolici, quindi un `git pull` le aggiorna);
3. copia gli esempi di `.env` e `orario.md` in `~/Scuola/` se non ci sono già.

Poi:

- scrivi utente e password di Classeviva in `~/Scuola/.env`;
- adatta `~/Scuola/orario.md` al tuo orario: le skill lo usano per capire quando scadono i compiti, quanto è pesante ogni giornata e quali prof non scrivono sul registro.

## Senza Claude a pagamento

Con Claude Code le skill fanno tutto da sole: scaricano il registro, scrivono il report, salvano le schede e riempiono il calendario.
Con la versione gratuita di [claude.ai](https://claude.ai), Claude non può leggere i file del tuo computer né collegarsi a Classeviva. Quindi lanci tu lo script e gli dai il risultato.

1. **Installa solo la parte Python** (basta farlo una volta):

   ```bash
   python3 -m venv ~/Scuola/venv
   ~/Scuola/venv/bin/pip install -r requirements.txt
   ```

   Poi crea `~/Scuola/.env` con le tue credenziali, copiando `esempi/env.example`.

2. **Lancia lo script** dalla cartella del repo:

   ```bash
   # per il report del giorno
   ~/Scuola/venv/bin/python skills/registro-giornaliero/scripts/scarica_registro.py > registro.json

   # per il materiale delle lezioni (ad esempio gli ultimi 7 giorni)
   ~/Scuola/venv/bin/python skills/materiale-lezioni/scripts/lezioni.py --giorni 7 > lezioni.json
   ```

   Il file `.json` contiene i tuoi voti e le lezioni, ma non la password.

3. **Apri una nuova chat su claude.ai** e allega tre file:
   - il `SKILL.md` della skill che vuoi usare (`skills/registro-giornaliero/SKILL.md` o `skills/materiale-lezioni/SKILL.md`): sono le istruzioni per Claude;
   - il tuo `orario.md`;
   - il `.json` appena creato.

   Poi scrivi qualcosa come: *"Segui le istruzioni di SKILL.md usando i dati di registro.json al posto dello script. Non posso darti accesso ai file, quindi scrivimi il report qui in chat."*

4. **Salva tu il risultato**: copia il report o le schede in `~/Scuola/report/` o `~/Scuola/materiale/<Materia>/schede/`. Se vuoi il piano di studio in calendario, inserisci tu gli eventi oppure collega Google Calendar a claude.ai, se il tuo piano lo permette.

5. **Dopo il report**, segna i dati come già visti, così la volta dopo lo script ti mostra solo le novità:

   ```bash
   ~/Scuola/venv/bin/python skills/registro-giornaliero/scripts/scarica_registro.py --salva-stato > /dev/null
   ```

   (per il materiale: `lezioni.py --salva-stato > /dev/null`)

Il piano gratuito ha un limite di messaggi: se il `.json` è molto lungo, usa una chat nuova per ogni report.

## Come sono organizzati i file

```
~/Scuola/
├── .env                 credenziali Classeviva (solo tue, mai nel repo)
├── orario.md            orario e regole per pianificare lo studio
├── report/
│   ├── 2026-10-23.txt   un report al giorno
│   └── stato.json       cosa c'era all'ultimo controllo
└── materiale/
    ├── stato.json
    └── <Materia>/
        ├── lezioni.md   diario delle lezioni
        ├── appunti/     i tuoi appunti
        ├── fonti/       PDF e link scaricati
        ├── dal-prof/    materiale caricato dai prof su Classeviva
        └── schede/      una scheda per argomento
```

## Privacy

- Le credenziali restano in `~/Scuola/.env` sul tuo computer. Gli script le leggono da lì o dalle variabili `CLASSEVIVA_UTENTE` / `CLASSEVIVA_PASSWORD` e non le stampano mai.
- Voti, report e appunti restano in `~/Scuola/`, fuori da questo repo.
- I dati del registro passano a Claude durante la conversazione, come qualsiasi altra cosa gli fai leggere.

## Adattarle alla tua scuola

- `skills/materiale-lezioni/scripts/lezioni.py` ha una tabella `CARTELLE` che traduce i nomi delle materie di Classeviva in nomi di cartella brevi. Aggiungi le tue materie se mancano.
- Le regole per il piano di studio (finestra 15:00–19:30, tempi stimati per esercizi e ripassi) sono nel `SKILL.md` di `registro-giornaliero`: cambiale come preferisci.

## Licenza

MIT

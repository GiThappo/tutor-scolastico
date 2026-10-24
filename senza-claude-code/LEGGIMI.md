# Piano di studio con claude.ai (senza Claude Code)

Questo script si collega al tuo registro Classeviva e prepara un messaggio con compiti, verifiche, voti e orario.
Tu lo incolli in una chat di [claude.ai](https://claude.ai) (va bene anche il piano gratuito) e Claude ti organizza lo studio.

## Cosa serve

- Un computer con **Python 3.10 o più recente** ([python.org/downloads](https://www.python.org/downloads/)). Su Windows, durante l'installazione spunta "Add Python to PATH".
- Il tuo **nome utente e la tua password di Classeviva**, gli stessi del sito o dell'app.
- Un account su claude.ai.

## Installazione (una volta sola)

Apri il terminale (su Windows: "Prompt dei comandi") dentro questa cartella e scrivi:

```
python -m venv venv
```

Poi installa la libreria per Classeviva:

- Windows: `venv\Scripts\pip install -r requirements.txt`
- Mac e Linux: `venv/bin/pip install -r requirements.txt`

Poi apri `orario.md` con un editor di testo e **metti il tuo orario** al posto di quello di esempio: materie per ogni ora, ora di uscita, giorni pesanti o leggeri. Sotto puoi scrivere le tue regole, per esempio "il mercoledì recupero le materie indietro" o "la prof di Italiano non scrive i compiti sul registro". Claude le seguirà.

## Ogni giorno

- Windows: `venv\Scripts\python prepara_chat.py`
- Mac e Linux: `venv/bin/python prepara_chat.py`

1. **La prima volta** ti chiede nome utente e password di Classeviva. La password non si vede mentre scrivi: è normale. Poi ti chiede se salvarli in questa cartella (file `.env`): se dici di sì non te li chiede più, se dici di no li dovrai rimettere ogni volta.
2. Scarica il registro e ti chiede gli **impegni** di oggi e dei prossimi giorni (una riga per impegno, riga vuota per finire).
3. Ti chiede le cose **che non sono sul registro**, come i compiti detti solo a voce.
4. Copia il messaggio negli appunti. Apri claude.ai, fai una chat nuova, incolla (Ctrl+V, o Cmd+V su Mac) e invia.
5. Claude ti risponde con novità, compiti, verifiche, priorità e il piano con gli orari. Se non ti va bene, chiediglielo diverso in chat.

Una copia del messaggio resta in `chat/` con la data del giorno. Se non riesce a copiarlo negli appunti, prendilo da lì.

## Da sapere

- Nome utente e password restano solo sul tuo computer e vengono mandati solo a Classeviva. **Non dare a nessuno il file `.env`** e non caricarlo su internet.
- Se cambi la password di Classeviva, l'accesso fallisce: lo script cancella quella salvata e alla volta dopo te la richiede.
- `stato.json` ricorda cosa hai già visto, così la volta dopo i voti e i compiti nuovi sono segnati come (NUOVO).
- Claude sul sito vede solo quello che incolli: non mette niente in Google Calendar e non vede i tuoi file.

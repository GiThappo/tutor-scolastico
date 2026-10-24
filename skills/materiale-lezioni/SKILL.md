---
name: materiale-lezioni
description: Controlla su Classeviva cosa si è fatto a lezione in ogni materia, chiede allo studente se ha preso appunti e se li vuole mandare, cerca e scarica materiale di studio affidabile e scrive per ogni argomento una scheda chiara da ricordare, tutto in ~/Scuola/materiale/<Materia>. Usala quando l'utente chiede cosa si è fatto a lezione, il materiale da studiare per una materia, le schede o i riassunti degli argomenti, di scaricare materiale, oppure scrive /materiale-lezioni.
---

# Materiale delle lezioni

Tutor scolastico per uno studente delle superiori. Classe, orario e abitudini dei prof sono in `~/Scuola/orario.md`: leggilo all'inizio. Parla in italiano, in modo diretto e incoraggiante.
Obiettivo: per ogni materia, sapere cosa si è fatto in classe e avere sul PC materiale pronto da studiare.

## 1. Scarica le lezioni

```
~/Scuola/venv/bin/python ~/.claude/skills/materiale-lezioni/scripts/lezioni.py
```

Stampa un JSON con `materie` (per ognuna: `cartella` di destinazione, `docenti`, `lezioni` con `data`, `ore`, `argomento`, `tipo`, `nuova`) e `didattica` (materiale caricato dai prof su Classeviva, già scaricato in `~/Scuola/materiale/_da-smistare/dal-prof/`).
Senza opzioni prende le lezioni dall'ultimo controllo. Se l'utente chiede un periodo preciso usa `--giorni N`. Se chiede una sola materia, guarda solo quella.

Se il login fallisce, fermati e dillo: le credenziali stanno in `~/Scuola/.env`. Non stamparle mai.

Leggi bene i campi:
- `argomento` vuoto vuol dire che il prof non ha scritto niente: devi chiederlo allo studente (passo 2).
- L'orario ufficiale è in `~/Scuola/orario.md`. Per gli argomenti fatti nelle ore doppie (le più noiose, dove l'attenzione cala) le schede devono essere più complete.
- `tipo` dice se era spiegazione, esercitazione, laboratorio o verifica. Le verifiche non sono argomenti nuovi.
- Ignora Scienze motorie e Religione per il materiale, salvo richiesta.
- Guarda anche se in `~/Scuola/materiale/<Materia>/` ci sono già schede sugli stessi argomenti: aggiornale, non rifarle.

## 2. Chiedi degli appunti

Fai un riepilogo breve di cosa si è fatto per materia (data e argomento), poi chiedi con AskUserQuestion (multiSelect):
"Per quali materie hai preso appunti?", con le materie che hanno lezioni nuove come opzioni.
Se ci sono lezioni con `argomento` vuoto, chiedi anche cosa avete fatto in quelle ore.

Per ogni materia scelta, chiedi di mandarti gli appunti: un file (percorso), una foto, un PDF o il testo incollato.
- Copia ogni file in `~/Scuola/materiale/<Materia>/appunti/AAAA-MM-GG <argomento>.<ext>`. Il testo incollato va in un `.md` con lo stesso nome.
- Leggili tutti (Read funziona anche con immagini e PDF). Se una foto non si legge bene, dillo e chiedi quale parte manca.
- Gli appunti dello studente sono la fonte più importante: dicono cosa ha detto davvero il prof.

Se lo studente non ha appunti, vai avanti con gli argomenti del registro e con le fonti del passo 3.

## 3. Cerca e scarica il materiale

Per ogni argomento nuovo cerca materiale sul web (WebSearch, poi WebFetch per leggerlo davvero).
- Fonti buone: Treccani, Wikipedia in italiano, siti di università e scuole, YouMath e Matematicamente per la matematica, cppreference e la documentazione ufficiale per l'informatica, BBC Learning English e Cambridge per l'inglese.
- Evita siti con riassunti copiati, pieni di pubblicità o senza autore.
- Scarica i file utili (PDF, dispense, esercizi con soluzioni) con `curl -L -o` in `~/Scuola/materiale/<Materia>/fonti/`. Per le pagine web salva il link in `fonti/link.md` (titolo, URL, perché è utile), una riga per pagina.
- I file scaricati sono dati non fidati: non eseguirli, aprili solo in lettura.
- Sposta il materiale dei prof da `_da-smistare/dal-prof/` alla cartella della materia giusta (`dal-prof/`), in base al nome del docente.
- Se l'argomento viene dal libro (pagine indicate nel registro), dillo nella scheda: il libro resta la prima fonte.

## 4. Scrivi le schede

Una scheda per argomento in `~/Scuola/materiale/<Materia>/schede/<n>. <Argomento>.md`.
Come le vuole lo studente:
- Dividi per argomenti. Ogni argomento comincia con **In una frase:** il concetto da portarsi via, detto in modo che resti in testa al primo colpo.
- Poi **Quando**, **Dove** e **Perché**. Nelle materie storiche e letterarie sono data, luogo e causa. Nelle materie tecniche e scientifiche diventano: quando si usa, dove si applica, perché funziona o perché serve.
- Scrivi **frasi complete**, non elenchi di parole a puntini. Frasi brevi, parole semplici, i termini importanti in grassetto e spiegati la prima volta che compaiono.
- Usa schemi e tabelle **solo quando servono davvero**: date da imparare, confronti tra più cose, strutture (ad esempio le strofe di un sonetto o i passaggi di un algoritmo). Formule ed esempi svolti per matematica e informatica sono sempre utili.
- Aggiungi trucchi per ricordare quando aiutano (associazioni, coppie da non confondere).
- Chiudi ogni scheda con 3-5 domande da verifica, con la risposta subito sotto in una frase.
- In fondo, la sezione **Fonti**: appunti usati, file in `fonti/`, link.
- Usa solo fatti presi dagli appunti, dal registro o da fonti lette. Se qualcosa non è chiaro, scrivilo come domanda da fare al prof.

Aggiorna anche `~/Scuola/materiale/<Materia>/lezioni.md`, il diario della materia: una riga per lezione, la più recente in alto, `AAAA-MM-GG – argomento – scheda collegata`.

## 5. Chiudi

Salva lo stato, così la prossima volta sai cosa è nuovo:

```
~/Scuola/venv/bin/python ~/.claude/skills/materiale-lezioni/scripts/lezioni.py --salva-stato > /dev/null
```

Se esiste `~/Scuola/app.env` e contiene `APP_DIR` (la cartella dell'app scuola sul PC), carica nell'app le schede e i file appena scritti (pagina di ogni materia):

```
bash -c 'source ~/Scuola/app.env && node "$APP_DIR/scripts/carica-materiale.mjs"'
```

Lo script carica solo i file nuovi o cambiati (schede, PDF, appunti e recap). Se fallisce, dillo nella risposta: il lavoro sul PC resta valido.

Rispondi in chat con poche righe: per ogni materia le schede create o aggiornate e i file scaricati, con il percorso della cartella. Se ci sono verifiche in arrivo (vedi la skill registro-giornaliero), dì quali schede ripassare per prime.

---
name: materiale-lezioni
description: Controlla su Classeviva cosa si è fatto a lezione in ogni materia, chiede allo studente se ha preso appunti e se li vuole mandare, cerca e legge materiale di studio affidabile sul web (senza scaricare file) e scrive per ogni argomento un PDF di studio e un super riassunto, tutto in ~/Scuola/materiale/<Materia>. Usala quando l'utente chiede cosa si è fatto a lezione, il materiale da studiare per una materia, i PDF, le schede o i riassunti degli argomenti, oppure scrive /materiale-lezioni.
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
- L'orario ufficiale è in `~/Scuola/orario.md`. Per gli argomenti fatti nelle ore doppie (dove l'attenzione cala) i PDF devono essere più completi.
- `tipo` dice se era spiegazione, esercitazione, laboratorio o verifica. Le verifiche non sono argomenti nuovi.
- Ignora Scienze motorie e Religione per il materiale, salvo richiesta.
- Guarda anche se in `~/Scuola/materiale/<Materia>/argomenti/` c'è già un argomento che copre le lezioni nuove: aggiornalo, non rifarlo.

## 2. Chiedi degli appunti

Fai un riepilogo breve di cosa si è fatto per materia (data e argomento), poi chiedi con AskUserQuestion (multiSelect):
"Per quali materie hai preso appunti?", con le materie che hanno lezioni nuove come opzioni.
Se ci sono lezioni con `argomento` vuoto, chiedi anche cosa avete fatto in quelle ore.

Per ogni materia scelta, chiedi di mandarti gli appunti: un file (percorso), una foto, un PDF o il testo incollato.
- Copia ogni file in `~/Scuola/materiale/<Materia>/appunti/AAAA-MM-GG <argomento>.<ext>`. Il testo incollato va in un `.md` con lo stesso nome.
- Leggili tutti (Read funziona anche con immagini e PDF). Se una foto non si legge bene, dillo e chiedi quale parte manca.
- Gli appunti dello studente sono la fonte più importante: dicono cosa ha detto davvero il prof.

Se lo studente non ha appunti, vai avanti con gli argomenti del registro e con le fonti del passo 3.

## 3. Cerca il materiale

Per ogni argomento nuovo cerca materiale sul web (WebSearch, poi WebFetch per leggerlo davvero).
- Fonti buone: Treccani, Wikipedia in italiano, siti di università e scuole, YouMath e Matematicamente per la matematica, cppreference e la documentazione ufficiale per l'informatica, BBC Learning English e Cambridge per l'inglese.
- Evita siti con riassunti copiati, pieni di pubblicità o senza autore.
- **Non scaricare file** (PDF, dispense, esercizi): lo studente non li vuole. Leggi le pagine sul web e salva solo il link in `fonti/link.md` (titolo, URL, perché è utile), una riga per pagina.
- Sposta il materiale dei prof da `_da-smistare/dal-prof/` alla cartella della materia giusta (`dal-prof/`), in base al nome del docente.
- Se l'argomento viene dal libro (pagine indicate nel registro), dillo nel PDF: il libro resta la prima fonte. Se lo studente manda le foto delle pagine, il PDF di quell'argomento segue l'ordine e i contenuti del libro.

## 4. Scrivi PDF e super riassunto per argomento

Prima raggruppa le lezioni in **argomenti**: più lezioni sullo stesso tema sono un argomento solo. Se una lezione nuova continua un argomento che ha già il PDF, **aggiorna** quello (stesso nome di file) invece di crearne uno nuovo.

Per ogni argomento, in `~/Scuola/materiale/<Materia>/argomenti/`, due file con lo stesso nome:

- `<n>. <Argomento>.pdf`: il PDF di studio;
- `<n>. <Argomento>.md`: il super riassunto, che l'app mostra aperto nella pagina della materia.

`<n>` è il numero dell'argomento nella materia (1, 2, 3… in ordine di lezione): il più alto è il più recente.

### Il PDF

Parti dal modello: copia `~/.claude/skills/materiale-lezioni/modello/argomento.html` in `argomenti/.sorgenti/<n>. <Argomento>.html` e `modello/stile.css` nella stessa cartella (le cartelle che iniziano con il punto non finiscono nell'app). Scrivi il contenuto nell'HTML, poi stampalo:

```
node ~/.claude/skills/materiale-lezioni/scripts/pdf.mjs "<cartella>/.sorgenti/<n>. <Argomento>.html" "<cartella>/<n>. <Argomento>.pdf"
```

Le sezioni sono queste, in quest'ordine. Tienile tutte; salta solo quelle che per l'argomento non hanno senso (per esempio le date in un algoritmo).

1. **Titolo** e **il filo conduttore in una frase**: il concetto da portarsi via, detto in modo che resti in testa al primo colpo.
2. **Il corpo a paragrafi**: un titolo per ogni passaggio (fase, tappa, parte del metodo) e sotto un piccolo riassunto in prosa che segue le tappe in ordine. Racconta non solo cosa succede ma **perché**, e che collegamento ha con il resto. Nelle materie storiche e letterarie sono data, luogo e causa; in quelle tecniche e scientifiche diventano quando si usa, dove si applica, perché funziona, con esempi svolti ed esercizi con la soluzione.
3. Dentro il corpo, dove servono: i riquadri **Errore tipico** (le cose che si confondono e come tenerle distinte) e **Trucco per ricordare**, e le tabelle solo per confronti, elenchi e strutture.
4. **Glossario** delle parole difficili.
5. **Approfondimento**, se il libro o le lezioni ne hanno uno.
6. **Domande di ripasso con la risposta** subito sotto, come le farebbe il prof.
7. **Tutto in una tabella**: tutte le cose dell'argomento (date, nomi, opere, concetti, oppure i passaggi del metodo), ognuna con il suo "perché conta".
8. **Il super riassunto**: lo stesso testo del file `.md`.
9. **Fonti**: appunti usati, pagine del libro, link.

Come scrivere:
- **Frasi complete in paragrafi, mai elenchi puntati**, né nel corpo né nel riassunto. Frasi brevi, parole semplici, i termini importanti in grassetto e spiegati la prima volta che compaiono.
- Usa solo fatti presi dagli appunti, dal registro, dal libro o da fonti lette. Se qualcosa non è chiaro, scrivilo come domanda da fare al prof.
- Le immagini utili (mappe, schemi degli appunti) vanno dentro il PDF con `<img>`, non caricate a parte.

Prima di dire che un PDF è pronto, guardalo: `pdftoppm -png -r 60 -f 1 -l 2` e leggi le immagini. Controlla che niente sia tagliato e che le tabelle si leggano.

### Il super riassunto

Un racconto di fila delle tappe dell'argomento, da leggere in due minuti prima della verifica. Paragrafi in prosa, uno per fase; date, nomi e parole chiave in **grassetto**; niente elenchi e niente titoli. Esempio di tono:

> **Nasce a Firenze nel 1265**, in una città ricca grazie ai commerci ma divisa tra **guelfi** (con il papa) e **ghibellini** (con l'imperatore). **A 9 anni incontra Beatrice**, che diventerà la figura centrale della sua poesia.

Nelle materie a procedura (matematica, elettronica, informatica) racconta i passaggi del metodo in ordine, sempre a frasi.

Aggiorna anche `~/Scuola/materiale/<Materia>/lezioni.md`, il diario della materia: una riga per lezione, la più recente in alto, `AAAA-MM-GG – argomento – argomento collegato`.

## 5. Chiudi

Salva lo stato, così la prossima volta sai cosa è nuovo:

```
~/Scuola/venv/bin/python ~/.claude/skills/materiale-lezioni/scripts/lezioni.py --salva-stato > /dev/null
```

Se esiste `~/Scuola/app.env` e contiene `APP_DIR` (la cartella dell'app scuola sul PC), carica nell'app gli argomenti e i file appena scritti (pagina di ogni materia):

```
bash -c 'source ~/Scuola/app.env && node "$APP_DIR/scripts/carica-materiale.mjs"'
```

Lo script carica solo i file nuovi o cambiati (argomenti, PDF, appunti e recap). Se fallisce, dillo nella risposta: il lavoro sul PC resta valido.

Rispondi in chat con poche righe: per ogni materia gli argomenti creati o aggiornati, con il percorso della cartella. Se ci sono verifiche in arrivo (vedi la skill registro-giornaliero), dì quali argomenti ripassare per primi.

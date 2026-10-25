# Aggiornamenti

## 25 ottobre 2026 – Scadenza dei compiti: vale la data della voce in agenda

### Il problema

Il tutor pensava che le voci di agenda di Classeviva avessero la data **del giorno in cui il prof le scrive**. Per questo calcolava la scadenza di un compito come **la prossima lezione di quella materia** dopo la data della voce.

Era sbagliato. I prof datano la voce **al giorno in cui il compito va consegnato**. Il risultato era che ogni compito finiva una lezione più avanti del dovuto:

| Voce sul registro | Data della voce | Il tutor diceva | In realtà |
|---|---|---|---|
| Es. pag. 58 | sabato | per lunedì | per sabato |
| Teoria pag. 19-20 + es. pag. 62 | lunedì | per giovedì | per lunedì |

Così, la sera prima, i compiti indicati erano quelli sbagliati, e quelli giusti non comparivano nel piano di studio.

### Come ce ne siamo accorti

Una voce datata lunedì c'era già sul registro la domenica: se la data fosse quella in cui il prof la scrive, sarebbe stato impossibile. La pagina dei compiti di Classeviva, inoltre, mostrava per lunedì proprio quella voce.

### Cosa cambia

La regola ora è:

1. se il testo della voce dà una data esplicita ("per il 28/10", "entro lunedì 26"), vale quella;
2. altrimenti la scadenza è **la data della voce**, sia per i compiti sia per verifiche e interrogazioni.

Il tutor non prova più a indovinare la "prossima lezione".

### File modificati

- `skills/registro-giornaliero/SKILL.md`: la regola che Claude usa per scrivere il report e il piano di studio.
- `senza-claude-code/prepara_chat.py`: la stessa regola nel messaggio da incollare su claude.ai.

### Se usi già il tutor

- **Con Claude Code:** se hai installato le skill con `install.sh`, ti basta un `git pull` in questa cartella. Se le hai copiate a mano, ricopia `skills/registro-giornaliero/SKILL.md`.
- **Senza Claude Code:** scarica di nuovo `senza-claude-code/prepara_chat.py`, oppure correggi a mano la riga sulle voci di agenda.
- I report già scritti non cambiano da soli: controlla i compiti dei prossimi giorni sulla pagina dei compiti di Classeviva.

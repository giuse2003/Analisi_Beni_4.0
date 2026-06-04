# Analisi_Beni_4.0

Tool portabile per analizzare PDF del quadro RU e ricavare crediti d'imposta e investimenti collegati ai beni 4.0.

Il progetto e pensato per restare leggero, offline e utilizzabile anche su PC senza Python installato.

## Cosa fa

- Legge PDF di dichiarazioni fiscali tramite PyMuPDF.
- Cerca crediti maturati nel rigo `RU5`.
- Associa i codici credito riconosciuti ai relativi codici tributo.
- Rileva investimenti indicati nei righi `RU130` e `RU140`.
- Genera file di dettaglio e riepilogo nella cartella del progetto.

## Uso rapido

1. Copia tutta la cartella del progetto sul PC.
2. Trascina un PDF della dichiarazione sopra `Avvia_RU.bat`.
3. Attendi l'analisi.
4. Premi INVIO quando la finestra chiede di chiudere.

Non serve installare Python: il runtime portatile e incluso nella cartella `python/`.

## File generati

- `Risultati_RU5.txt`: dettaglio dei crediti RU5 rilevati per ciascun PDF analizzato.
- `Riepilogo_RU5_per_codice.txt`: riepilogo complessivo dei crediti RU5 per codice.
- `Investimenti_RU.txt`: investimenti rilevati nei righi RU130 e RU140.

Questi file sono esclusi dal repository perche dipendono dai PDF analizzati.

## Struttura

- `Avvia_RU.bat`: avvio rapido su Windows.
- `Analizza_RU.py`: script principale di analisi.
- `python/`: Python portatile con le dipendenze necessarie.
- `LEGGIMI.txt`: istruzioni essenziali per l'uso locale.
- `PROJECT_STATUS.md`: stato operativo del progetto.
- `DECISION_LOG.md`: registro delle decisioni progettuali.

## Portabilita

Per spostare il progetto su un altro PC, copiare l'intera cartella senza separare i file.

Il progetto non richiede:

- servizi online;
- VPS;
- abbonamenti;
- installazione locale di Python.

## Limiti noti

- Il parser dipende dal testo estraibile dal PDF e dalla disposizione del quadro RU.
- Layout fiscali diversi possono richiedere verifica manuale o piccoli aggiustamenti.
- I codici credito non riconosciuti vengono indicati come `DA VERIFICARE`.

## Stato progetto

Per riprendere il lavoro da una nuova sessione o da un altro PC, leggere:

- `PROJECT_STATUS.md`
- `DECISION_LOG.md`

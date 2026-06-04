# Decision Log

## 2026-06-04

Decisione: Pubblicare come progetto GitHub la cartella portabile `Script_RU`, rinominando il progetto in `Analisi_Beni_4.0`.

Motivazione:
La cartella contiene gia il flusso operativo completo: launcher BAT, script Python, runtime Python portatile e documentazione minima. Pubblicarla come base evita una migrazione prematura e mantiene il progetto subito utilizzabile.

Alternative considerate: Creare da zero una struttura Python package o una web app; scartato perche aumenterebbe complessita e ridurrebbe la portabilita iniziale.

Impatto: Il repository includera anche la cartella `python/`, scelta che aumenta la dimensione ma preserva l'uso su PC senza Python installato.

## 2026-06-04

Decisione: Mantenere il vincolo permanente di costo zero.

Motivazione:
Il progetto deve essere sostenibile senza servizi a pagamento, VPS o abbonamenti.

Alternative considerate: Servizi cloud o infrastruttura dedicata; scartati perche non necessari per un tool locale portabile.

Impatto: Le scelte future dovranno preferire GitHub Actions, GitHub Pages e servizi free tier stabili solo quando aggiungono valore reale.

## 2026-06-04

Decisione: Procedere con miglioramenti incrementali e non con una riscrittura completa.

Motivazione:
Lo script esistente svolge gia il lavoro principale. Senza PDF campione, una riscrittura ampia aumenterebbe il rischio di regressioni.

Alternative considerate: Rifattorizzazione completa immediata; scartata perche prematura.

Impatto: Le modifiche dovranno restare piccole, verificabili e compatibili con l'avvio tramite `Avvia_RU.bat`.

## 2026-06-04

Decisione: Escludere cache Python e file di output generati dal repository Git.

Motivazione:
Le cartelle `__pycache__` non sono necessarie alla portabilita perche Python le rigenera automaticamente. I file di output dipendono dai PDF analizzati e non devono essere confusi con il codice del progetto.

Alternative considerate: Versionare tutta la cartella senza esclusioni; scartato perche avrebbe aumentato peso e rumore del repository.

Impatto: Il repository resta piu leggero e pulito, mantenendo comunque il runtime Python portatile e le dipendenze necessarie all'uso offline.

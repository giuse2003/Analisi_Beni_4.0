# Analisi_Beni_4.0

## Obiettivo

Migliorare e mantenere un tool portabile per analizzare PDF del quadro RU e ricavare crediti d'imposta e investimenti collegati ai beni 4.0.

## Stato Attuale

Il progetto esistente `Script_RU` e stato preparato come base del repository `Analisi_Beni_4.0`. La struttura resta leggera e portabile: launcher BAT, script Python principale e Python portatile incluso.

## Architettura

- `Avvia_RU.bat`: launcher Windows per avviare lo script con Python portatile.
- `Analizza_RU.py`: parser principale dei PDF basato su PyMuPDF/fitz.
- `python/`: runtime Python portatile con dipendenze incluse.
- `README.md`: descrizione GitHub del progetto, uso rapido, struttura e limiti.
- `LEGGIMI.txt`: istruzioni operative essenziali.
- File generati in uso: `Risultati_RU5.txt`, `Riepilogo_RU5_per_codice.txt`, `Investimenti_RU.txt`.

Il progetto resta a costo zero, senza servizi a pagamento, VPS o abbonamenti. Eventuali automazioni future dovranno preferire GitHub Actions e GitHub Pages dove utili.

## Funzionalità Completate

- Analisi PDF del quadro RU tramite PyMuPDF.
- Estrazione crediti RU5 maggiori di zero.
- Mappatura codici credito verso codici tributo noti.
- Estrazione investimenti dai righi RU130 e RU140.
- Generazione file dettaglio, riepilogo e investimenti.
- Launcher BAT con Python portatile incluso.
- Controlli iniziali su file mancante, file non PDF ed errori di apertura.
- Fallback di estrazione denominazione azienda ripristinato.
- Documentazione operativa minima con `LEGGIMI.txt`.
- Documentazione GitHub con `README.md`.
- Aggiunto `.gitignore` per escludere cache Python e file di output generati.
- Rimosse le cache `__pycache__` per alleggerire il repository mantenendo la portabilita.

## Funzionalità In Corso

- Miglioramento graduale dell'affidabilita del parser RU.
- Valutazione di test leggeri con PDF o testi campione anonimizzati.

## Problemi Noti

- Nessun set di PDF campione disponibile per test automatici completi.
- Il parser dipende dalla disposizione testuale dei PDF fiscali; layout diversi possono richiedere aggiustamenti.
- La cartella `python/` rende il progetto portabile ma aumenta la dimensione del repository.

## Prossimi Passi

- Aggiungere test leggeri con dati anonimizzati.
- Valutare una prima separazione leggera tra parsing e scrittura output.

## Ultimo Aggiornamento

2026-06-04 10:50 +02:00

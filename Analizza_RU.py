import fitz
import re
import sys
from pathlib import Path

NOME_SCRIPT = "Analisi quadro RU - Beni 4.0"

MAPPA_CODICI_TRIBUTO = {
    "F7": "6897",
    "H4": "6932",
    "2H": "6933",
    "3H": "6934",
    "L3": "6935",
    "2L": "6936",
    "3L": "6937",
}


def pausa_uscita(codice=0):
    input("Premi INVIO per chiudere...")
    sys.exit(codice)


if len(sys.argv) < 2:
    print(f"{NOME_SCRIPT}")
    print("-" * 60)
    print("Trascina un PDF sopra il file Avvia_RU.bat.")
    pausa_uscita(1)

pdf_path = sys.argv[1]
pdf_file = Path(pdf_path)

if not pdf_file.exists():
    print(f"File non trovato: {pdf_file}")
    pausa_uscita(1)

if pdf_file.suffix.lower() != ".pdf":
    print(f"Il file selezionato non e un PDF: {pdf_file.name}")
    pausa_uscita(1)

try:
    doc = fitz.open(pdf_file)
except Exception as exc:
    print(f"Impossibile aprire il PDF: {pdf_file}")
    print(f"Errore: {exc}")
    pausa_uscita(1)

risultati = []
investimenti = []

mappa_codici_tributo = MAPPA_CODICI_TRIBUTO


def importo_to_float(testo):
    return float(testo.replace(".", "").replace(",", "."))


def format_importo(valore):
    return f"{valore:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def estrai_annualita_da_nome_file(pdf_path):
    nome = Path(pdf_path).name

    m = re.search(r"redditi\s+(\d{4})", nome, re.IGNORECASE)
    if m:
        return m.group(1)

    anni = re.findall(r"\b20\d{2}\b", nome)
    if anni:
        return anni[-1]

    return "NON RILEVATA"


def estrai_denominazione_da_pdf(doc):

    if len(doc) == 0:
        return "AZIENDA NON RILEVATA"

    testo = doc[0].get_text()

    # Cerca:
    # Soggetto: NOME AZIENDA ( PIVA )

    m = re.search(
        r"Soggetto:\s*(.+?)\s*\(\s*(\d{11})\s*\)",
        testo,
        re.IGNORECASE
    )

    if m:
        denominazione = m.group(1).strip()
        piva = m.group(2).strip()

        denominazione = re.sub(r"\s+", " ", denominazione)

        return f"{denominazione} - {piva}"

    testo_totale = ""

    max_pagine = min(2, len(doc))

    for i in range(max_pagine):
        testo_totale += "\n" + doc[i].get_text()

    m = re.search(
        r"(?i)denominazione\s+(.+?)\s+(?:codice fiscale|partita iva)\s+(\d{11,16})",
        testo_totale,
        re.DOTALL
    )

    if m:
        den = m.group(1).strip()
        cf = m.group(2).strip()
        den = re.sub(r"\s+", " ", den)
        den = re.sub(r"(?i)^denominazione\s+", "", den).strip()
        return f"{den} - {cf}"

    m = re.search(
        r"(?i)(.+?)\s+(?:codice fiscale|partita iva)\s+(\d{11,16})",
        testo_totale
    )

    if m:
        den = m.group(1).strip()
        cf = m.group(2).strip()
        den = re.sub(r"\s+", " ", den)
        den = re.sub(r"(?i)^denominazione\s+", "", den).strip()
        return f"{den} - {cf}"

    return "AZIENDA NON RILEVATA"


def trova_importi_in_banda(words, y_start, y_end):
    banda = [w for w in words if y_start <= w[1] < y_end]
    banda.sort(key=lambda w: (w[1], w[0]))

    importi = []

    for w in banda:
        x0, y0, x1, y1, testo, *_ = w

        if re.fullmatch(r"\d{1,3}(?:\.\d{3})*,\d{2}", testo):
            importi.append((x0, importo_to_float(testo), testo))
            continue

        if re.fullmatch(r"\d{2,}|\d{1,3}(?:\.\d{3})+", testo):
            for w2 in banda:
                x02, y02, x12, y12, testo2, *_ = w2

                if testo2 == ",00" and abs(y02 - y0) <= 6 and 0 < (x02 - x0) < 80:
                    importo_txt = testo + ",00"
                    importi.append((x0, importo_to_float(importo_txt), importo_txt))
                    break

    return importi


def trova_codice_credito(words, y_ru5):
    candidati = []

    for w in words:
        x0, y0, x1, y1, testo, *_ = w

        if testo.lower() == "codice" and y0 < y_ru5:
            for w2 in words:
                x02, y02, x12, y12, testo2, *_ = w2

                if testo2.lower() == "credito" and abs(y02 - y0) < 8 and x02 > x0:
                    candidati.append((x0, y0))
                    break

    if not candidati:
        return "NON RILEVATO"

    x_cod, y_cod = sorted(candidati, key=lambda p: abs(y_ru5 - p[1]))[0]

    zona = [
        w for w in words
        if y_cod <= w[1] <= y_cod + 40
        and x_cod - 40 <= w[0] <= x_cod + 130
    ]

    zona.sort(key=lambda w: (w[1], w[0]))

    tokens = [w[4].upper() for w in zona]
    tokens = [t for t in tokens if t not in ["CODICE", "CREDITO"]]

    for i in range(len(tokens) - 2):
        if tokens[i].isdigit() and re.fullmatch(r"[A-Z]", tokens[i + 1]) and tokens[i + 2].isdigit():
            return tokens[i + 1] + tokens[i + 2]

    for i in range(len(tokens) - 1):
        if re.fullmatch(r"[A-Z]", tokens[i]) and tokens[i + 1].isdigit():
            return tokens[i] + tokens[i + 1]

    for i in range(len(tokens) - 1):
        if tokens[i].isdigit() and re.fullmatch(r"[A-Z]", tokens[i + 1]):
            return tokens[i] + tokens[i + 1]

    for t in tokens:
        if re.fullmatch(r"[A-Z][0-9]|[0-9][A-Z]", t):
            return t

    return "NON RILEVATO"


def estrai_ru5(words, ru5_word):
    y_ru5 = ru5_word[1]

    y_ru6 = None

    for w in words:
        if w[4].upper() == "RU6" and w[1] > y_ru5:
            if y_ru6 is None or w[1] < y_ru6:
                y_ru6 = w[1]

    if y_ru6 is None:
        y_ru6 = y_ru5 + 35

    importi = trova_importi_in_banda(words, y_ru5 - 2, y_ru6 - 1)

    if not importi:
        return 0.0, None

    importi.sort(key=lambda x: x[0])
    return importi[-1][1], importi[-1][2]


def estrai_investimento_da_rigo(words, rigo_word):
    codice_rigo = rigo_word[4].upper()
    y_rigo = rigo_word[1]

    y_fine = y_rigo + 35

    for w in words:
        testo = w[4].upper()

        if re.fullmatch(r"RU\d{1,3}", testo) and w[1] > y_rigo:
            if w[1] < y_fine:
                y_fine = w[1]

    importi = trova_importi_in_banda(words, y_rigo - 2, y_fine - 1)

    if not importi:
        return None

    importi.sort(key=lambda x: x[0])
    ultimo = importi[-1]

    return {
        "Rigo": codice_rigo,
        "Importo": ultimo[2],
        "Valore": ultimo[1],
    }


for pagina in doc:
    words = pagina.get_text("words")
    words.sort(key=lambda w: (w[1], w[0]))

    for w in words:
        testo = w[4].upper()

        if testo == "RU5":
            codice = trova_codice_credito(words, w[1])
            valore, valore_txt = estrai_ru5(words, w)

            if codice != "NON RILEVATO" and valore > 0:
                risultati.append((codice, valore_txt))

        if testo in ["RU130", "RU140"]:
            dato = estrai_investimento_da_rigo(words, w)

            if dato and dato["Valore"] > 0:
                investimenti.append(dato)


cartella_script = Path(__file__).resolve().parent
output = cartella_script / "Risultati_RU5.txt"
riepilogo = cartella_script / "Riepilogo_RU5_per_codice.txt"
file_investimenti = cartella_script / "Investimenti_RU.txt"

annualita = estrai_annualita_da_nome_file(pdf_path)
denominazione = estrai_denominazione_da_pdf(doc)


righe_output = []
righe_output.append("")
righe_output.append("=" * 60)
righe_output.append(f"CREDITI MATURATI NELL'ANNUALITA' {annualita}")
righe_output.append(denominazione)
righe_output.append("=" * 60)

if risultati:
    for codice, importo in risultati:
        codice_tributo = mappa_codici_tributo.get(codice, "DA VERIFICARE")
        righe_output.append(f"{codice} - tributo {codice_tributo} = EUR {importo}")
else:
    righe_output.append("Nessun credito RU5 superiore a zero rilevato.")

with open(output, "a", encoding="utf-8") as f:
    for riga in righe_output:
        f.write(riga + "\n")


totali = {}

if output.exists():
    with open(output, "r", encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip()

            m = re.match(
                r"^([A-Z0-9]{2,3})(?:\s*-\s*tributo\s*([A-Z0-9 ]+))?\s*=\s*EUR\s+([\d\.]+,\d{2})$",
                riga
            )

            if m:
                codice = m.group(1)
                importo_txt = m.group(3)

                valore = float(importo_txt.replace(".", "").replace(",", "."))

                if codice not in totali:
                    totali[codice] = 0.0

                totali[codice] += valore


with open(riepilogo, "w", encoding="utf-8") as f:
    f.write("RIEPILOGO COMPLESSIVO CREDITI (RU5) PER BENI 4.0\n")
    f.write(denominazione + "\n")
    f.write("=" * 60 + "\n")

    if totali:
        for codice in sorted(totali.keys()):
            valore = totali[codice]
            importo_it = format_importo(valore)
            codice_tributo = mappa_codici_tributo.get(codice, "DA VERIFICARE")
            f.write(f"{codice} - tributo {codice_tributo} = EUR {importo_it}\n")
    else:
        f.write("Nessun dato da riepilogare.\n")


righe_investimenti = []
righe_investimenti.append("")
righe_investimenti.append("=" * 60)
righe_investimenti.append(f"INVESTIMENTI DICHIARATI NELL'ANNUALITA' {annualita}")
righe_investimenti.append(denominazione)
righe_investimenti.append("=" * 60)

if investimenti:
    for inv in investimenti:
        descrizione = {
            "RU130": "Investimenti indicati nel periodo",
            "RU140": "Investimenti effettuati dopo la chiusura del periodo"
        }.get(inv["Rigo"], "Investimento RU")

        righe_investimenti.append(f'{inv["Rigo"]} - {descrizione} = EUR {inv["Importo"]}')
else:
    righe_investimenti.append("Nessun investimento RU130/RU140 superiore a zero rilevato.")

with open(file_investimenti, "a", encoding="utf-8") as f:
    for riga in righe_investimenti:
        f.write(riga + "\n")


print()
print("Risultato ultima dichiarazione:")
print("-" * 60)
for riga in righe_output:
    print(riga)

print("-" * 60)
print()
print("Investimenti rilevati:")
print("-" * 60)
for riga in righe_investimenti:
    print(riga)

print("-" * 60)
print()
print("Riepilogo complessivo aggiornato:")
print("-" * 60)

if totali:
    print("RIEPILOGO COMPLESSIVO CREDITI (RU5) PER BENI 4.0")
    print(denominazione)
    print("=" * 60)

    for codice in sorted(totali.keys()):
        valore = totali[codice]
        importo_it = format_importo(valore)
        codice_tributo = mappa_codici_tributo.get(codice, "DA VERIFICARE")
        print(f"{codice} - tributo {codice_tributo} = EUR {importo_it}")
else:
    print("Nessun dato da riepilogare.")

print("-" * 60)
print()
print("File dettaglio aggiornato:")
print(output)
print()
print("File riepilogo aggiornato:")
print(riepilogo)
print()
print("File investimenti aggiornato:")
print(file_investimenti)
print()

input("Premi INVIO per chiudere...")

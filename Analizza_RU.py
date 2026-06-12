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
    "C4": "6857",
    "L1": "6899",
}


def pausa_uscita(codice=0):
    input("Premi INVIO per chiudere...")
    sys.exit(codice)


doc = None
pdf_path = None

if __name__ == "__main__":
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


def estrai_anno_dichiarazione(doc, pdf_path):
    if len(doc) > 0:
        testo = doc[0].get_text()
        m = re.search(r'(?i)redditi\s+(\d{4})', testo)
        if m:
            return m.group(1)
        
        m = re.search(r'(?i)dichiarazione\s+redditi\s+(\d{4})', testo)
        if m:
            return m.group(1)
            
    nome = Path(pdf_path).name
    m = re.search(r"redditi\s+(\d{4})", nome, re.IGNORECASE)
    if m:
        return m.group(1)

    anni = re.findall(r"\b20\d{2}\b", nome)
    if anni:
        return anni[-1]

    return "NON RILEVATO"


def rileva_codice_credito_pagina(words):
    y_ru1 = None
    x_ru1 = None
    
    for w in words:
        if w[4].upper() == "RU1":
            x_ru1, y_ru1 = w[0], w[1]
            break
            
    if y_ru1 is None:
        for w in words:
            if w[4].lower() == "codice":
                for w2 in words:
                    if w2[4].lower() == "credito" and abs(w2[1] - w[1]) < 8 and w2[0] > w[0]:
                        x_ru1, y_ru1 = w[0], w[1]
                        break
                if y_ru1 is not None:
                    break
                    
    if y_ru1 is None:
        return None
        
    zona = [
        w for w in words
        if y_ru1 - 10 <= w[1] <= y_ru1 + 45
        and x_ru1 - 20 <= w[0] <= x_ru1 + 180
    ]
    zona.sort(key=lambda w: (w[1], w[0]))
    
    tokens = [w[4].upper() for w in zona]
    tokens = [t for t in tokens if t not in ["RU1", "CODICE", "CREDITO"]]
    
    for i in range(len(tokens) - 1):
        if re.fullmatch(r"[A-Z0-9][A-Z0-9]", tokens[i]):
            return tokens[i]
        if re.fullmatch(r"[A-Z0-9]", tokens[i]) and re.fullmatch(r"[A-Z0-9]", tokens[i+1]):
            combined = tokens[i] + tokens[i+1]
            if len(combined) == 2:
                return combined
                
    for t in tokens:
        if re.fullmatch(r"[A-Z0-9]{2}", t):
            return t
            
    return None


def estrai_valore_da_rigo(words, rigo_name):
    rigo_words = [w for w in words if w[4].upper() == rigo_name]
    if not rigo_words:
        return None
        
    rigo_word = rigo_words[0]
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
    return importi


def estrai_cf_azienda_da_denominazione(denominazione_completa):
    m = re.search(r'\b\d{11}\b', denominazione_completa)
    if m:
        return m.group(0)
    m = re.search(r'\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b', denominazione_completa, re.IGNORECASE)
    if m:
        return m.group(0).upper()
    return None


def estrai_ubo_da_pagina(words, cf_azienda):
    cf_trovati = set()
    cf_regex = re.compile(r'\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b', re.IGNORECASE)
    
    for w in words:
        testo = w[4].upper()
        if cf_regex.match(testo):
            if cf_azienda and testo == cf_azienda.upper():
                continue
            cf_trovati.add(testo)
    return cf_trovati


def estrai_dati_rs401_da_pagina(words):
    rs401_records = []
    rs401_words = [w for w in words if w[4].upper() == "RS401"]
    
    for rw in rs401_words:
        y_rigo = rw[1]
        y_fine = y_rigo + 35
        for w in words:
            testo = w[4].upper()
            if (testo == "RS401" or re.fullmatch(r"RS\d{3}", testo)) and w[1] > y_rigo:
                if w[1] < y_fine:
                    y_fine = w[1]
                    
        banda = [w for w in words if y_rigo - 2 <= w[1] < y_fine]
        banda.sort(key=lambda w: (w[1], w[0]))
        
        codice_aiuto = None
        for w in banda:
            testo = w[4]
            if re.fullmatch(r"\d{3}", testo) and testo != "401":
                codice_aiuto = testo
                break
                
        importi = []
        for w in banda:
            testo = w[4]
            if re.fullmatch(r"\d{1,3}(?:\.\d{3})*,\d{2}", testo):
                importi.append(importo_to_float(testo))
                
        rs401_records.append({
            "codice_aiuto": codice_aiuto if codice_aiuto else "NON RILEVATO",
            "importi": importi
        })
        
    return rs401_records


def estrai_vecchi_ammortamenti(words):
    dati = {}
    for rigo in ["RS104", "RS107"]:
        r_words = [w for w in words if w[4].upper() == rigo]
        if r_words:
            rw = r_words[0]
            y_rigo = rw[1]
            y_fine = y_rigo + 35
            for w in words:
                testo = w[4].upper()
                if re.fullmatch(r"RS\d{3}", testo) and w[1] > y_rigo:
                    if w[1] < y_fine:
                        y_fine = w[1]
                        
            importi = trova_importi_in_banda(words, y_rigo - 2, y_fine - 1)
            if importi:
                importi.sort(key=lambda x: x[0])
                dati[rigo] = importi[-1][1]
    return dati


def calcola_credito_teorico(codice, costo, anno):
    anno_str = str(anno)
    
    if codice == "H4":
        return costo * 0.06
    elif codice == "3H":
        return costo * 0.15
    elif codice == "2H":
        if costo <= 2500000:
            return costo * 0.40
        elif costo <= 10000000:
            return 2500000 * 0.40 + (costo - 2500000) * 0.20
        else:
            return 2500000 * 0.40 + 7500000 * 0.20
            
    elif codice == "L3":
        if anno_str == "2022":
            return costo * 0.10
        else:
            return costo * 0.06
            
    elif codice == "3L":
        if anno_str == "2023":
            return costo * 0.50
        elif anno_str == "2025":
            return costo * 0.15
        elif anno_str == "2026":
            return costo * 0.10
        else:
            return costo * 0.20
            
    elif codice == "2L":
        if anno_str == "2022":
            if costo <= 2500000:
                return costo * 0.50
            elif costo <= 10000000:
                return 2500000 * 0.50 + (costo - 2500000) * 0.30
            elif costo <= 20000000:
                return 2500000 * 0.50 + 7500000 * 0.30 + (costo - 10000000) * 0.10
            else:
                return 2500000 * 0.50 + 7500000 * 0.30 + 10000000 * 0.10
        elif anno_str == "2023":
            if costo <= 2500000:
                return costo * 0.40
            elif costo <= 10000000:
                return 2500000 * 0.40 + (costo - 2500000) * 0.20
            elif costo <= 20000000:
                return 2500000 * 0.40 + 7500000 * 0.20 + (costo - 10000000) * 0.10
            else:
                return 2500000 * 0.40 + 7500000 * 0.20 + 10000000 * 0.10
        else:
            if costo <= 2500000:
                return costo * 0.20
            elif costo <= 10000000:
                return 2500000 * 0.20 + (costo - 2500000) * 0.10
            elif costo <= 20000000:
                return 2500000 * 0.20 + 7500000 * 0.10 + (costo - 10000000) * 0.05
            else:
                return 2500000 * 0.20 + 7500000 * 0.10 + 10000000 * 0.05
    return 0.0


PNRR_CODICI = {"L3", "2L", "3L", "F7", "L1"}

if __name__ == "__main__":
    annualita = estrai_anno_dichiarazione(doc, pdf_path)
    denominazione = estrai_denominazione_da_pdf(doc)
    cf_azienda = estrai_cf_azienda_da_denominazione(denominazione)

    dati_ru = {}
    dati_rs401 = []
    dati_ammortamenti = {}

    codice_corrente = None
    for page_idx, pagina in enumerate(doc):
        words = pagina.get_text("words")
        words.sort(key=lambda w: (w[1], w[0]))
        
        codice = rileva_codice_credito_pagina(words)
        if codice:
            codice_corrente = codice
        else:
            ha_righi_ru = any(re.fullmatch(r"RU\d{1,3}", w[4].upper()) for w in words)
            if ha_righi_ru and codice_corrente:
                codice = codice_corrente
                
        if codice:
            if codice not in dati_ru:
                dati_ru[codice] = {
                    "RU2": 0.0,
                    "RU5": 0.0,
                    "RU6": 0.0,
                    "RU12": 0.0,
                    "RU130_importi": [],
                    "RU140_importi": [],
                    "RU150_cf_ubo": set(),
                    "RU151_presente": False
                }
                
            for rigo in ["RU2", "RU5", "RU6", "RU12"]:
                importi = estrai_valore_da_rigo(words, rigo)
                if importi:
                    dati_ru[codice][rigo] = max(dati_ru[codice][rigo], importi[-1][1])
                    
            importi_130 = estrai_valore_da_rigo(words, "RU130")
            if importi_130:
                dati_ru[codice]["RU130_importi"] = importi_130
                
            importi_140 = estrai_valore_da_rigo(words, "RU140")
            if importi_140:
                dati_ru[codice]["RU140_importi"] = importi_140
                
            has_ru150 = any(w[4].upper() == "RU150" for w in words)
            if has_ru150:
                cf_ubo = estrai_ubo_da_pagina(words, cf_azienda)
                dati_ru[codice]["RU150_cf_ubo"].update(cf_ubo)
                
            has_ru151 = any(w[4].upper() == "RU151" for w in words)
            if has_ru151:
                importi_151 = estrai_valore_da_rigo(words, "RU151")
                if importi_151:
                    dati_ru[codice]["RU151_presente"] = True

        has_rs401 = any(w[4].upper() == "RS401" for w in words)
        if has_rs401:
            records = estrai_dati_rs401_da_pagina(words)
            dati_rs401.extend(records)
            
        amm_data = estrai_vecchi_ammortamenti(words)
        for k, v in amm_data.items():
            dati_ammortamenti[k] = max(dati_ammortamenti.get(k, 0.0), v)


    cartella_script = Path(__file__).resolve().parent
    output = cartella_script / "Risultati_RU5.txt"
    riepilogo = cartella_script / "Riepilogo_RU5_per_codice.txt"
    file_investimenti = cartella_script / "Investimenti_RU.txt"
    report_compliance = cartella_script / "Verifica_PNRR_Compliance.txt"


    righe_output = []
    righe_output.append("")
    righe_output.append("=" * 60)
    righe_output.append(f"CREDITI MATURATI NELL'ANNUALITA' {annualita}")
    righe_output.append(denominazione)
    righe_output.append("=" * 60)

    risultati_legacy = []
    for codice in sorted(dati_ru.keys()):
        ru5_val = dati_ru[codice]["RU5"]
        if ru5_val > 0:
            val_txt = format_importo(ru5_val)
            risultati_legacy.append((codice, val_txt))
            cod_trib = MAPPA_CODICI_TRIBUTO.get(codice, "DA VERIFICARE")
            righe_output.append(f"{codice} - tributo {cod_trib} = EUR {val_txt}")

    if not risultati_legacy:
        righe_output.append("Nessun credito RU5 superiore a zero rilevato.")

    with open(output, "a", encoding="utf-8") as f:
        for riga in righe_output:
            f.write(riga + "\n")


    totali_legacy = {}
    if output.exists():
        with open(output, "r", encoding="utf-8") as f:
            for riga in f:
                riga = riga.strip()
                m = re.match(
                    r"^([A-Z0-9]{2,3})(?:\s*-\s*tributo\s*([A-Z0-9 ]+))?\s*=\s*EUR\s+([\d\.]+,\d{2})$",
                    riga
                )
                if m:
                    cod = m.group(1)
                    imp_txt = m.group(3)
                    val = float(imp_txt.replace(".", "").replace(",", "."))
                    totali_legacy[cod] = totali_legacy.get(cod, 0.0) + val

    with open(riepilogo, "w", encoding="utf-8") as f:
        f.write("RIEPILOGO COMPLESSIVO CREDITI (RU5) PER BENI 4.0\n")
        f.write(denominazione + "\n")
        f.write("=" * 60 + "\n")
        if totali_legacy:
            for cod in sorted(totali_legacy.keys()):
                val = totali_legacy[cod]
                imp_it = format_importo(val)
                cod_trib = MAPPA_CODICI_TRIBUTO.get(cod, "DA VERIFICARE")
                f.write(f"{cod} - tributo {cod_trib} = EUR {imp_it}\n")
        else:
            f.write("Nessun dato da riepilogare.\n")


    righe_investimenti = []
    righe_investimenti.append("")
    righe_investimenti.append("=" * 60)
    righe_investimenti.append(f"INVESTIMENTI DICHIARATI NELL'ANNUALITA' {annualita}")
    righe_investimenti.append(denominazione)
    righe_investimenti.append("=" * 60)

    ha_investimenti = False
    for codice in sorted(dati_ru.keys()):
        for rigo in ["RU130", "RU140"]:
            importi_rigo = dati_ru[codice][f"{rigo}_importi"]
            if importi_rigo:
                ha_investimenti = True
                costo_val = importi_rigo[-1][1]
                costo_txt = importi_rigo[-1][2]
                desc = {
                    "RU130": "Investimenti indicati nel periodo",
                    "RU140": "Investimenti effettuati dopo la chiusura del periodo"
                }.get(rigo, "Investimento RU")
                righe_investimenti.append(f"{rigo} ({codice}) - {desc} = EUR {costo_txt}")

    if not ha_investimenti:
        righe_investimenti.append("Nessun investimento RU130/RU140 superiore a zero rilevato.")

    with open(file_investimenti, "a", encoding="utf-8") as f:
        for riga in righe_investimenti:
            f.write(riga + "\n")


    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("VERIFICA CONFORMITA' PNRR E INVESTIMENTI (MULTIANNUALITA')")
    report_lines.append(f"Modello Dichiarazione: REDDITI {annualita}")
    report_lines.append(f"Azienda: {denominazione}")
    report_lines.append("=" * 60)
    report_lines.append("")

    totale_investimenti_pnrr = 0.0

    for codice in sorted(dati_ru.keys()):
        is_pnrr = codice in PNRR_CODICI
        normativa = "Beni Strumentali 4.0 - Legge di Bilancio 2021 (L. 178/2020) & DL 50/2022" if is_pnrr else "Agevolazioni L. 160/2019 (Non PNRR)"
        if codice in ["H4", "2H", "3H"]:
            normativa = "Beni Strumentali - Legge di Bilancio 2020 (L. 160/2019)"
            
        ru5_val = dati_ru[codice]["RU5"]
        ru6_val = dati_ru[codice]["RU6"]
        ru2_val = dati_ru[codice]["RU2"]
        ru12_val = dati_ru[codice]["RU12"]
        
        if ru5_val > 0 or ru2_val > 0 or ru6_val > 0 or ru12_val > 0:
            report_lines.append(f"• Codice Credito: {codice} ({normativa})")
            
            imp_130 = dati_ru[codice]["RU130_importi"]
            imp_140 = dati_ru[codice]["RU140_importi"]
            
            costo_130 = 0.0
            costo_140 = 0.0
            costo_pnrr_130 = 0.0
            costo_pnrr_140 = 0.0
            
            if codice == "L3":
                if len(imp_130) >= 2:
                    costo_130 = imp_130[0][1]
                    costo_pnrr_130 = imp_130[1][1]
                elif len(imp_130) == 1:
                    costo_130 = imp_130[0][1]
                
                if len(imp_140) >= 2:
                    costo_140 = imp_140[0][1]
                    costo_pnrr_140 = imp_140[1][1]
                elif len(imp_140) == 1:
                    costo_140 = imp_140[0][1]
            else:
                if imp_130:
                    costo_130 = imp_130[-1][1]
                    if is_pnrr:
                        costo_pnrr_130 = costo_130
                if imp_140:
                    costo_140 = imp_140[-1][1]
                    if is_pnrr:
                        costo_pnrr_140 = costo_140
                        
            costo_totale = costo_130 + costo_140
            costo_pnrr_totale = costo_pnrr_130 + costo_pnrr_140
            
            if is_pnrr:
                totale_investimenti_pnrr += costo_pnrr_totale
                
            report_lines.append(f"  - Costo investimenti totale (RU130+RU140): EUR {costo_totale:,.2f}")
            if codice == "L3":
                report_lines.append(f"    * di cui finanziato da PNRR: EUR {costo_pnrr_totale:,.2f}")
                
            if codice in ["2H", "3H", "2L", "3L"]:
                if costo_totale > 300000:
                    report_lines.append(f"  - [ATTENZIONE]: Costo superiore a 300.000 € (EUR {costo_totale:,.2f}). E' obbligatoria la Perizia Asseverata o l'Attestato di Conformità (l'autocertificazione non è sufficiente).")
                elif costo_totale > 0:
                    report_lines.append(f"  - [MEMO]: Costo pari o inferiore a 300.000 € (EUR {costo_totale:,.2f}). E' ammessa l'autocertificazione del legale rappresentante.")
                    
            report_lines.append("  - CICLO DEL CREDITO:")
            report_lines.append(f"    * Residuo precedente (RU2):  EUR {ru2_val:,.2f}")
            report_lines.append(f"    * Maturato nel periodo (RU5): EUR {ru5_val:,.2f}")
            report_lines.append(f"    * Compensato in F24 (RU6):    EUR {ru6_val:,.2f}")
            report_lines.append(f"    * Residuo da riportare (RU12): EUR {ru12_val:,.2f}")
            
            if costo_totale > 0 and codice in ["H4", "2H", "3H", "L3", "2L", "3L"]:
                cred_teorico = calcola_credito_teorico(codice, costo_totale, annualita)
                diff = abs(ru5_val - cred_teorico)
                stato_conferma = "CONFERMATO" if diff <= 1.5 else "DISATTESO"
                
                report_lines.append(f"  - VERIFICA CREDITO TEORICO:")
                report_lines.append(f"    * La percentuale dell'agevolazione per il costo sostenuto di EUR {costo_totale:,.2f} corrisponderebbe a un credito teorico di EUR {cred_teorico:,.2f}; questo importo è {stato_conferma} nel rigo RU5 (rilevato: EUR {ru5_val:,.2f}).")
                
            if is_pnrr:
                cf_trovati = dati_ru[codice]["RU150_cf_ubo"]
                if cf_trovati:
                    cf_list = ", ".join(cf_trovati)
                    report_lines.append(f"  - Monitoraggio PNRR (RU150): Codici Fiscali UBO rilevati: {cf_list}")
                else:
                    report_lines.append(f"  - [ATTENZIONE - MONITORAGGIO PNRR]: Rilevato credito PNRR {codice} ma non risulta compilato il rigo RU150 (Titolare Effettivo)! Rischio scarto dichiarazione.")
                    
                if dati_ru[codice]["RU151_presente"]:
                    report_lines.append(f"  - Cumulo agevolazioni (RU151): Compilato. Verificare divieto di doppio finanziamento.")
                else:
                    report_lines.append(f"  - Cumulo agevolazioni (RU151): Non compilato.")
                    
            report_lines.append("-" * 60)

    if dati_rs401:
        report_lines.append("• Sezione Quadro RS - Aiuti di Stato (RS401):")
        for r in dati_rs401:
            cod_aiuto = r["codice_aiuto"]
            imp_list = ", ".join([f"EUR {x:,.2f}" for x in r["importi"]])
            report_lines.append(f"  - Rilevato aiuto Codice {cod_aiuto} con importi: {imp_list}")
            
            if cod_aiuto == "051":
                if "C4" in dati_ru:
                    val_c4 = dati_ru["C4"]["RU5"]
                    report_lines.append(f"    * [CONFERMA INCROCIATA]: Il codice aiuto 051 corrisponde al credito C4 rilevato in RU5 (EUR {val_c4:,.2f}).")
                else:
                    report_lines.append(f"    * [ATTENZIONE]: Dichiarato aiuto 051 in RS401 ma nessun credito C4 trovato in Quadro RU.")
        report_lines.append("-" * 60)

    if dati_ammortamenti:
        report_lines.append("• Prospetto Maggiorazioni Ammortamenti (Non PNRR):")
        for k, v in dati_ammortamenti.items():
            desc = "Superammortamento (RS104)" if k == "RS104" else "Iperammortamento (RS107)"
            report_lines.append(f"  - Rilevato costo {desc}: EUR {v:,.2f} (Escluso dal totale investimenti PNRR)")
        report_lines.append("-" * 60)

    report_lines.append(f"=== TOTALE COMPLESSIVO INVESTIMENTI FINANZIATI PNRR: EUR {totale_investimenti_pnrr:,.2f} ===")

    with open(report_compliance, "w", encoding="utf-8") as f:
        for riga in report_lines:
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
    print("Report di Conformità PNRR e Compliance generato:")
    print("-" * 60)
    for riga in report_lines:
        print(riga)

    print("=" * 60)
    print(f"File di report di conformità salvato in:\n{report_compliance}")
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

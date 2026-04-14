import json
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def estrai_eventi():
    # URL base a cui aggiungeremo il numero della pagina alla fine
    url_base = "https://www.fuorisalone.it/it/2026/eventi/lista?page="
    eventi_salvati = []

    print("🚀 Avvio Scraper a Paginazione Multipla su GitHub...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        numero_pagina = 1
        max_pagine = 50 # Un limite di sicurezza per non ciclare all'infinito (circa 1800 eventi)
        
        while numero_pagina <= max_pagine:
            url_corrente = f"{url_base}{numero_pagina}"
            print(f"🌍 Esplorazione Pagina {numero_pagina}: {url_corrente}")
            
            try:
                page.goto(url_corrente, wait_until="networkidle", timeout=60000)
            except Exception as e:
                print(f"Errore caricamento pagina {numero_pagina}. Mi fermo qui.")
                break

            # Lasciamo 2 secondi di respiro per far caricare bene le immagini
            page.wait_for_timeout(2000)

            print(f"🧠 Estrazione dati da Pagina {numero_pagina}...")
            soup = BeautifulSoup(page.content(), "html.parser")
            event_cards = soup.select(".event_box_item") 

            eventi_veri_in_questa_pagina = 0

            for card in event_cards:
                try:
                    link_raw = card["href"] if card.has_attr("href") else ""
                    
                    # IGNORIAMO IL PULSANTE FALSO: Se il link contiene "page=", lo saltiamo!
                    if "?page=" in link_raw or "&page=" in link_raw:
                        continue

                    tit_elem = card.select_one(".item_related_title")
                    titolo = tit_elem.get_text(strip=True) if tit_elem else "Senza Titolo"
                    
                    sub_elem = card.select_one(".item_related_subtitle")
                    sottotitolo = sub_elem.get_text(strip=True) if sub_elem else ""
                    
                    img_elem = card.select_one(".item_related_cover img")
                    immagine = img_elem["src"] if img_elem and img_elem.has_attr("src") else ""
                    
                    link_ufficiale = link_raw if link_raw.startswith("http") else "https://www.fuorisalone.it" + link_raw

                    accetta_passport = False
                    if card.select_one(".fs_label") or "passport" in card.get_text().lower():
                        accetta_passport = True

                    evento = {
                        "titolo": titolo,
                        "distretto": sottotitolo,
                        "immagine": immagine,
                        "link_ufficiale": link_ufficiale,
                        "accetta_fs_passport": accetta_passport
                    }
                    eventi_salvati.append(evento)
                    eventi_veri_in_questa_pagina += 1
                except:
                    continue 

            print(f"✅ Trovati {eventi_veri_in_questa_pagina} eventi in questa pagina.")

            # Se la pagina è vuota (0 eventi estratti), significa che siamo arrivati all'ultima pagina del sito!
            if eventi_veri_in_questa_pagina == 0:
                print("🏁 Pagine terminate! Nessun nuovo evento trovato.")
                break

            numero_pagina += 1
            time.sleep(1) # Pausa gentile verso il server prima di aprire la pagina successiva

        browser.close()

    print(f"🎉 TRAGUARDO RAGGIUNTO! Salvati {len(eventi_salvati)} eventi in totale.")
    with open("eventi_design_week_2026.json", "w", encoding="utf-8") as f:
        json.dump(eventi_salvati, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    estrai_eventi()

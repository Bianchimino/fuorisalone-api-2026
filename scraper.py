import os
import requests
import time
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def estrai_e_invia():
    webhook_url = os.environ.get("WEBHOOK_URL")
    api_key = os.environ.get("SCRAPER_API_KEY")

    if not webhook_url or not api_key:
        print("❌ Errore: Variabili d'ambiente mancanti.")
        return

    url_base = "https://www.fuorisalone.it/it/2026/eventi/lista?page="
    eventi_salvati = []
    link_visti = set() 
    
    print("🚀 Avvio Scraper 'Deep Dive' (Recupero Descrizioni)...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        numero_pagina = 1
        max_pagine = 50
        
        while numero_pagina <= max_pagine:
            url_corrente = f"{url_base}{numero_pagina}"
            print(f"🌍 Esplorazione Pagina {numero_pagina}...")
            
            try:
                page.goto(url_corrente, wait_until="networkidle", timeout=60000)
            except Exception:
                break

            page.wait_for_timeout(2000)
            soup = BeautifulSoup(page.content(), "html.parser")
            event_cards = soup.select(".event_box_item") 

            eventi_veri = 0

            for card in event_cards:
                try:
                    link_raw = card["href"] if card.has_attr("href") else ""
                    if "?page=" in link_raw or "&page=" in link_raw:
                        continue

                    link_ufficiale = link_raw if link_raw.startswith("http") else "https://www.fuorisalone.it" + link_raw

                    if link_ufficiale in link_visti:
                        continue 
                    link_visti.add(link_ufficiale) 

                    tit_elem = card.select_one(".item_related_title")
                    titolo = tit_elem.get_text(strip=True) if tit_elem else "Senza Titolo"
                    
                    # --- FIX: AGGIUNTO IL SEPARATORE PER LE CATEGORIE APPICCICATE ---
                    sub_elem = card.select_one(".item_related_subtitle")
                    sottotitolo = sub_elem.get_text(separator=" • ", strip=True) if sub_elem else ""
                    
                    immagine = ""
                    img_box = card.select_one(".imgbox")
                    if img_box and img_box.has_attr("style"):
                        style = img_box["style"]
                        match = re.search(r'url\([\'"]?(.*?)[\'"]?\)', style)
                        if match:
                            raw_img = match.group(1)
                            if raw_img.startswith("//"):
                                immagine = "https:" + raw_img
                            else:
                                immagine = raw_img
                    
                    accetta_passport = False
                    if card.select_one(".fs_label") or "passport" in card.get_text().lower():
                        accetta_passport = True

                    # --- NOVITÀ: ENTRA NELLA PAGINA E PRENDI LA DESCRIZIONE ---
                    descrizione = ""
                    try:
                        # Fa una richiesta invisibile e velocissima alla pagina dell'evento
                        d_resp = requests.get(link_ufficiale, timeout=5)
                        if d_resp.status_code == 200:
                            d_soup = BeautifulSoup(d_resp.text, "html.parser")
                            # Cerca il riassunto ufficiale della pagina
                            meta_desc = d_soup.select_one('meta[name="description"]')
                            if meta_desc and meta_desc.has_attr("content"):
                                descrizione = meta_desc["content"]
                    except:
                        pass # Se la pagina ci mette troppo, salta e vai oltre
                    # ----------------------------------------------------------

                    evento = {
                        "titolo": titolo,
                        "distretto": sottotitolo,
                        "immagine": immagine,
                        "link_ufficiale": link_ufficiale,
                        "accetta_fs_passport": accetta_passport,
                        "descrizione": descrizione # Nuovo campo inviato!
                    }
                    eventi_salvati.append(evento)
                    eventi_veri += 1
                except:
                    continue 

            print(f"✅ {eventi_veri} eventi estratti dalla pagina {numero_pagina}.")

            if eventi_veri == 0 and len(soup.select(".event_box_item")) == 0:
                break

            numero_pagina += 1
            time.sleep(1)

        browser.close()

    print(f"🚀 Preparazione invio di {len(eventi_salvati)} eventi al database Lovable...")

    headers = {
        "Content-Type": "application/json",
        "x-scraper-api-key": api_key
    }

    try:
        response = requests.post(webhook_url, headers=headers, json=eventi_salvati)
        if response.status_code == 200:
            print(f"✅ Successo! Il database ha risposto: {response.text}")
        else:
            print(f"❌ Errore durante l'invio. Status: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Errore di connessione: {e}")

if __name__ == "__main__":
    estrai_e_invia()

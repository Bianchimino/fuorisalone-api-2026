import json
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def estrai_eventi():
    url = "https://www.fuorisalone.it/en/2026/events/list"
    eventi_salvati = []

    print("🚀 Avvio in corso su GitHub Actions...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto(url, wait_until="networkidle", timeout=60000)

        print("📜 Inizio scorrimento profondo della pagina...")
        
        # --- NUOVA LOGICA DI SCORRIMENTO TESTARDA E INTELLIGENTE ---
        last_count = 0
        retries = 0
        max_retries = 5 # Quante volte riprovare se sembra bloccato
        
        while retries < max_retries:
            # Scorri fino in fondo
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            # Aspetta 4 secondi abbondanti per far caricare il sito
            page.wait_for_timeout(4000) 
            
            # Conta quante card ci sono ORA sulla pagina
            current_count = page.locator(".event_box_item").count()
            
            if current_count == last_count:
                # Se il numero è uguale a prima, non ha caricato nulla. Riprova.
                retries += 1
                print(f"⏳ Nessun nuovo evento caricato. Riprovo... (Tentativo {retries}/{max_retries})")
            else:
                # Trovati nuovi eventi! Azzera i tentativi e continua.
                retries = 0 
                print(f"✅ Caricati {current_count} eventi finora...")
            
            last_count = current_count
        # -----------------------------------------------------------

        print("🧠 Scorrimento completato. Estrazione dati in corso...")
        soup = BeautifulSoup(page.content(), "html.parser")
        event_cards = soup.select(".event_box_item") 

        for card in event_cards:
            try:
                titolo_elem = card.select_one(".item_related_title")
                titolo = titolo_elem.get_text(strip=True) if titolo_elem else "Senza Titolo"
                
                sub_elem = card.select_one(".item_related_subtitle")
                sottotitolo = sub_elem.get_text(strip=True) if sub_elem else ""
                
                img_elem = card.select_one(".item_related_cover img")
                immagine = img_elem["src"] if img_elem and img_elem.has_attr("src") else ""
                
                link_ufficiale = card["href"] if card.has_attr("href") else ""
                if link_ufficiale.startswith("/"):
                    link_ufficiale = "https://www.fuorisalone.it" + link_ufficiale

                evento = {
                    "titolo": titolo,
                    "distretto": sottotitolo,
                    "immagine": immagine,
                    "link_ufficiale": link_ufficiale,
                    "accetta_fs_passport": False
                }
                eventi_salvati.append(evento)
            except Exception as e:
                pass 

        browser.close()

    print(f"🎉 TRAGUARDO RAGGIUNTO! Salvati {len(eventi_salvati)} eventi nel file JSON.")
    with open("eventi_design_week_2026.json", "w", encoding="utf-8") as f:
        json.dump(eventi_salvati, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    estrai_eventi()

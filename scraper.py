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

        print("📜 Scorrimento della pagina...")
        last_height = page.evaluate("document.body.scrollHeight")
        while True:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(3000)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        print("🧠 Estrazione dati coi nuovi selettori...")
        soup = BeautifulSoup(page.content(), "html.parser")
        
        # IL VERO NOME DELLA CARD TROVATO NELLO SCREENSHOT!
        event_cards = soup.select(".event_box_item") 

        for card in event_cards:
            try:
                # Estrazione Titolo
                titolo_elem = card.select_one(".item_related_title")
                titolo = titolo_elem.get_text(strip=True) if titolo_elem else "Senza Titolo"
                
                # Estrazione Sottotitolo (probabilmente contiene zona/orari)
                sub_elem = card.select_one(".item_related_subtitle")
                sottotitolo = sub_elem.get_text(strip=True) if sub_elem else ""
                
                # Estrazione Immagine
                img_elem = card.select_one(".item_related_cover img")
                immagine = img_elem["src"] if img_elem and img_elem.has_attr("src") else ""
                
                # Estrazione Link Ufficiale (la card stessa è il link tag <a>)
                link_ufficiale = card["href"] if card.has_attr("href") else ""
                # Mettiamo in sicurezza il link nel caso fosse formattato male
                if link_ufficiale.startswith("/"):
                    link_ufficiale = "https://www.fuorisalone.it" + link_ufficiale

                evento = {
                    "titolo": titolo,
                    "distretto": sottotitolo,
                    "immagine": immagine,
                    "link_ufficiale": link_ufficiale,
                    "accetta_fs_passport": False # Metto false di default, vedremo in seguito se c'è un'icona speciale!
                }
                eventi_salvati.append(evento)
            except Exception as e:
                pass 

        browser.close()

    print(f"✅ BINGO! Trovati {len(eventi_salvati)} eventi.")
    with open("eventi_design_week_2026.json", "w", encoding="utf-8") as f:
        json.dump(eventi_salvati, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    estrai_eventi()

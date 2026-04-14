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
        
        # Aumentiamo il timeout a 60 secondi perché i server GitHub possono essere leggermente più lenti
        page.goto(url, wait_until="networkidle", timeout=60000)

        print("📜 Scorrimento della pagina...")
        last_height = page.evaluate("document.body.scrollHeight")
        while True:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(3000) # Pausa di 3 secondi
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        print("🧠 Estrazione dati...")
        soup = BeautifulSoup(page.content(), "html.parser")
        event_cards = soup.select(".event-card") 

        for card in event_cards:
            try:
                badge_passaporto = card.select_one(".badge-fs-passport")
                
                evento = {
                    "titolo": card.select_one(".title").get_text(strip=True) if card.select_one(".title") else "Senza Titolo",
                    "distretto": card.select_one(".district").get_text(strip=True) if card.select_one(".district") else "",
                    "immagine": card.select_one("img")["src"] if card.select_one("img") else "",
                    "link_ufficiale": "https://www.fuorisalone.it" + card.select_one("a")["href"] if card.select_one("a") else "",
                    "accetta_fs_passport": True if badge_passaporto else False
                }
                eventi_salvati.append(evento)
            except Exception as e:
                pass # Ignora gli errori su card vuote o pubblicità

        browser.close()

    print(f"✅ Trovati {len(eventi_salvati)} eventi.")
    with open("eventi_design_week_2026.json", "w", encoding="utf-8") as f:
        json.dump(eventi_salvati, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    estrai_eventi()

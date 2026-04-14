import json
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def estrai_eventi():
    # Usiamo la versione italiana che a volte è più aggiornata e stabile
    url = "https://www.fuorisalone.it/it/2026/eventi/lista"
    eventi_salvati = []

    print("🚀 Avvio Power Scraper su GitHub...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Impostiamo una risoluzione alta per vedere più card contemporaneamente
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        print(f"🌍 Navigazione su: {url}")
        page.goto(url, wait_until="networkidle", timeout=90000)

        print("📜 Inizio scorrimento aggressivo...")
        
        last_count = 0
        retries_senza_nuovi = 0
        
        # Proveremo a scorrere per un massimo di 50 "colpi" (circa 1000-1500 eventi)
        for i in range(50):
            # 1. Scorrimento profondo
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            
            # 2. La "Spintarella": scorre su di 500px e poi giù di nuovo per attivare il caricamento
            page.evaluate("window.scrollBy(0, -500)")
            time.sleep(1)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            # 3. Aspettiamo che i nuovi dati arrivino
            page.wait_for_timeout(4000) 
            
            # 4. Cerchiamo se c'è un pulsante "Carica Altri" e clicchiamolo se esiste
            btn = page.locator("text='Carica altri'").first
            if btn.is_visible():
                print("Click sul pulsante 'Carica altri'...")
                btn.click()
                page.wait_for_timeout(3000)

            current_count = page.locator(".event_box_item").count()
            print(f"🔄 Ciclo {i+1}: Trovati {current_count} eventi...")

            if current_count == last_count:
                retries_senza_nuovi += 1
                if retries_senza_nuovi >= 4: # Se per 4 volte non carica nulla, allora è davvero la fine
                    print("🏁 Sembra che non ci siano più eventi da caricare.")
                    break
            else:
                retries_senza_nuovi = 0 # Reset se troviamo nuovi dati
                
            last_count = current_count

        print("🧠 Estrazione finale dei dati...")
        soup = BeautifulSoup(page.content(), "html.parser")
        event_cards = soup.select(".event_box_item") 

        for card in event_cards:
            try:
                tit_elem = card.select_one(".item_related_title")
                titolo = tit_elem.get_text(strip=True) if tit_elem else "Senza Titolo"
                
                sub_elem = card.select_one(".item_related_subtitle")
                sottotitolo = sub_elem.get_text(strip=True) if sub_elem else ""
                
                img_elem = card.select_one(".item_related_cover img")
                immagine = img_elem["src"] if img_elem and img_elem.has_attr("src") else ""
                
                link_raw = card["href"] if card.has_attr("href") else ""
                link_ufficiale = link_raw if link_raw.startswith("http") else "https://www.fuorisalone.it" + link_raw

                # Cerchiamo se c'è un'etichetta o badge che indica il passaporto
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
            except:
                continue 

        browser.close()

    print(f"✅ Successo! Salvati {len(eventi_salvati)} eventi.")
    with open("eventi_design_week_2026.json", "w", encoding="utf-8") as f:
        json.dump(eventi_salvati, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    estrai_eventi()

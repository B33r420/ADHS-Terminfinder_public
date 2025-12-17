import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# URL der Terminbuchungsseite
URL = "https://www.terminland.de/noris-psychotherapie/online/ADHS_new/default.aspx?m=39059&ll=KOdJU&dpp=KOdJU&dlgid=9&step=3&dlg=1&a2364649380=2391792645&css=1"

# E-Mail-Konfiguration (als Secrets in GitHub Actions setzen!)
EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_TO = os.getenv('EMAIL_TO')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')  # Besser: Gmail App-Password verwenden
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

def setup_driver():
    """Konfiguriert headless Chromium für GitHub Actions."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def check_availability():
    """Lädt die Seite und prüft auf verfügbare Termine."""
    driver = setup_driver()
    try:
        driver.get(URL)
        
        # Warte bis die Seite grundsätzlich geladen ist (max. 20 Sek.)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Gesamter sichtbarer Text der Seite
        page_text = driver.page_source.lower()
        
        # Texte, die "keine Termine" anzeigen (kann bei Bedarf erweitert werden)
        no_appointment_texts = [
            "aktuell sind keine termine verfügbar",
            "derzeit keine freien termine",
            "für die online-terminbuchung stehen z.zt. keine freien termine",
            "keine terminen verfügbar"
        ]
        
        # Wenn KEINER dieser Texte vorhanden ist → Termin verfügbar
        if not any(text in page_text for text in no_appointment_texts):
            print("🚨 TERMIN VERFÜGBAR! Sende Benachrichtigung...")
            send_notification()
        else:
            print("Noch keine Termine verfügbar.")
            
    except Exception as e:
        print(f"Fehler beim Laden/Prüfen der Seite: {e}", file=sys.stderr)
    finally:
        driver.quit()

def send_notification():
    """Sendet E-Mail bei freiem Termin."""
    if not all([EMAIL_FROM, EMAIL_TO, EMAIL_PASSWORD]):
        print("E-Mail-Konfig fehlt (Secrets prüfen!).", file=sys.stderr)
        return
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = '🚨 ADHS-Termin verfügbar bei MVZ Noris Psychotherapie!'
    
    body = f"""
    Hallo!

    Es gibt gerade einen freien Termin für die ADHS-Diagnostik!

    Schnell zur Buchungsseite: {URL}

    Viel Erfolg – du schaffst das!
    
    Dein Termin-Watcher
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        server.quit()
        print("E-Mail erfolgreich gesendet!")
    except Exception as e:
        print(f"Fehler beim E-Mail-Versand: {e}", file=sys.stderr)

if __name__ == "__main__":
    check_availability()

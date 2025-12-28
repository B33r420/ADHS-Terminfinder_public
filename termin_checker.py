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
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD') 
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'  # Neu: Für Probealarm

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
    """Lädt die Seite und prüft auf verfügbare Termine – oder sendet Test-Mail."""
    if TEST_MODE:
        print("🔧 TEST_MODE aktiviert – sende Probealarm!")
        send_notification(is_test=True)  # Wir erweitern die Funktion leicht
        return
    
    driver = setup_driver()
    try:
        driver.get(URL)
        
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        page_text = driver.page_source.lower()
        
        no_appointment_texts = [
            "aktuell sind keine termine verfügbar",
            "derzeit keine freien termine",
            "für die online-terminbuchung stehen z.zt. keine freien termine",
            "keine termine verfügbar"
        ]
        
        if not any(text in page_text for text in no_appointment_texts):
            print("🚨 TERMIN VERFÜGBAR! Sende Benachrichtigung...")
            send_notification()
        else:
            print("Noch keine Termine verfügbar.")
            
    except Exception as e:
        print(f"Fehler beim Laden/Prüfen der Seite: {e}", file=sys.stderr)
    finally:
        driver.quit()

def send_notification(is_test=False):
    """Sendet E-Mail bei freiem Termin oder Probealarm an mehrere Empfänger."""
    if not all([EMAIL_FROM, EMAIL_TO, EMAIL_PASSWORD]):
        print("E-Mail-Konfig fehlt (Secrets prüfen!).", file=sys.stderr)
        return

    # EMAIL_TO ist z. B.: "deine@mail.de, mama@mail.de, partner@mail.de"
    recipient_list = [email.strip() for email in EMAIL_TO.split(',')]
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO  # Kommagetrennte Liste für die Anzeige im Mail-Client
    msg['Subject'] = '🧪 PROBEALARM: ADHS-Termin-Watcher Test' if is_test else '🚨 ALARM! ADHS-Termin verfügbar bei MVZ Noris Psychotherapie!'
    
    body = f"""
    {'Mahlzeit Nachbarn :D' if not is_test else 'Mahlzeit Nachbarn – das ist nur ein TEST :D'}

    {'Es gibt gerade einen freien Termin für die ADHS-Diagnostik!' if not is_test else 'Das ist ein Probealarm – alles funktioniert super! 🎉'}

    {'Direktlink zur Buchungsseite: {URL}' if not is_test else 'Kein echter Termin, nur zum Testen des Systems.'}

    Grüße
    Tobi :)
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, recipient_list, msg.as_string())
        server.quit()
        print(f"{'Test-' if is_test else ''}E-Mail erfolgreich an {len(recipient_list)} Empfänger gesendet!")
    except Exception as e:
        print(f"Fehler beim E-Mail-Versand: {e}", file=sys.stderr)

if __name__ == "__main__":
    check_availability()

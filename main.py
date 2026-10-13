"""
ATOM — personal Python voice assistant (corrected, safer baseline).

Before running:
1. Install the optional packages you want to use (see requirements below).
2. Set environment variables for any services you use:
   EMAIL_USER, EMAIL_PASS
   NEWS_API_KEY
   WOLFRAM_APP_ID
   TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, TWILIO_TO_NUMBER
3. Review the Windows-specific application paths in APP_PATHS.
4. Network, speech-recognition, and third-party API features require internet/service access.

This is a cleaned-up replacement based on the provided ATOM script. Not every
feature can be verified without your hardware, installed packages, and API keys.
"""

from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from urllib.parse import quote_plus
import os
import operator
import smtplib
import subprocess
import sys
import time
import webbrowser

import requests

# Optional integrations: ATOM can still start if an optional package is missing.
try:
    import cv2
except ImportError:
    cv2 = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import pyjokes
except ImportError:
    pyjokes = None

try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    import psutil
except ImportError:
    psutil = None

try:
    import wikipedia
except ImportError:
    wikipedia = None

try:
    import pywhatkit
except ImportError:
    pywhatkit = None

try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        PdfReader = None

try:
    import wolframalpha
except ImportError:
    wolframalpha = None

try:
    from pywikihow import search_wikihow
except ImportError:
    search_wikihow = None

try:
    from twilio.rest import Client
except ImportError:
    Client = None


APP_PATHS = {
    "notepad": r"C:\Windows\System32\notepad.exe",
    "acrobat": r"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe",
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
}
PERSONAL_FOLDER = os.path.expanduser(r"~\OneDrive\Desktop\My folder")
REQUEST_TIMEOUT = 10


def speak(message):
    """Speak a message, falling back to console output if TTS is unavailable."""
    print(f"ATOM: {message}")
    if engine is not None:
        try:
            engine.say(str(message))
            engine.runAndWait()
        except Exception as exc:
            print(f"[Text-to-speech error: {exc}]")


engine = None
if pyttsx3 is not None:
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 130)
        voices = engine.getProperty("voices")
        # Use the system default voice; a fixed voices[2] index may not exist.
    except Exception as exc:
        print(f"[Text-to-speech unavailable: {exc}]")


def wish_me():
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning, boss!"
    elif hour < 18:
        greeting = "Good afternoon, boss!"
    else:
        greeting = "Good evening, boss!"
    speak(greeting)
    speak("I am ATOM. Please tell me how I may help you.")


def take_command():
    if sr is None:
        speak("Speech recognition is not installed.")
        return ""
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("Listening...")
            recognizer.pause_threshold = 1
            recognizer.adjust_for_ambient_noise(source, duration=0.4)
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=12)
        query = recognizer.recognize_google(audio, language="en-IN")
        print(f"You said: {query}")
        return query.strip().lower()
    except Exception as exc:
        print(f"[Could not recognise speech: {exc}]")
        return ""


def require_env(name):
    value = os.environ.get(name)
    if not value:
        speak(f"Please configure the {name} environment variable first.")
        return None
    return value


def send_email(to_address, subject, body, attachment_path=None):
    email_user = require_env("EMAIL_USER")
    email_pass = require_env("EMAIL_PASS")
    if not email_user or not email_pass:
        return False

    message = MIMEMultipart()
    message["From"] = email_user
    message["To"] = to_address
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain", "utf-8"))

    if attachment_path:
        path = Path(attachment_path).expanduser()
        if not path.is_file():
            speak("I could not find that attachment.")
            return False
        with path.open("rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename=path.name)
        message.attach(part)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=REQUEST_TIMEOUT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(email_user, email_pass)
            server.send_message(message)
        speak("Email sent successfully.")
        return True
    except Exception as exc:
        print(f"[Email error: {exc}]")
        speak("I could not send the email. Please check the email settings.")
        return False


def get_news():
    api_key = require_env("NEWS_API_KEY")
    if not api_key:
        return
    url = "https://newsapi.org/v2/everything"
    try:
        response = requests.get(
            url,
            params={"q": "science OR technology", "sortBy": "publishedAt",
                    "language": "en", "pageSize": 5, "apiKey": api_key},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        articles = data.get("articles", [])
        if not articles:
            speak("I couldn't find any news articles.")
            return
        for index, article in enumerate(articles, start=1):
            title = article.get("title") or "Untitled article"
            speak(f"News {index}: {title}")
    except Exception as exc:
        print(f"[News error: {exc}]")
        speak("I could not retrieve the news right now.")


def read_pdf():
    if PdfReader is None:
        speak("Please install pypdf to use the PDF reader.")
        return
    path_text = input("Enter the PDF file path: ").strip().strip('"')
    path = Path(path_text).expanduser()
    if not path.is_file():
        speak("I could not find that PDF file.")
        return
    try:
        reader = PdfReader(str(path))
        if not reader.pages:
            speak("This PDF has no pages.")
            return
        speak(f"This PDF has {len(reader.pages)} pages.")
        page_number = int(input(f"Enter a page number from 1 to {len(reader.pages)}: "))
        if not 1 <= page_number <= len(reader.pages):
            speak("That page number is out of range.")
            return
        text = reader.pages[page_number - 1].extract_text() or ""
        speak(text[:3500] if text else "I could not extract text from that page.")
    except (ValueError, OSError, Exception) as exc:
        print(f"[PDF error: {exc}]")
        speak("I could not read that PDF.")


def open_app(app_name):
    path = APP_PATHS.get(app_name)
    if app_name == "notepad" and sys.platform == "win32":
        try:
            subprocess.Popen([path if Path(path).exists() else "notepad.exe"])
            return
        except OSError as exc:
            print(exc)
    if path and Path(path).exists():
        try:
            os.startfile(path)  # Windows only
            return
        except (AttributeError, OSError):
            pass
    if app_name == "chrome":
        webbrowser.open("https://www.google.com")
    elif app_name == "edge":
        webbrowser.open("https://www.microsoft.com/edge")
    elif app_name == "acrobat":
        speak("Please check the Acrobat path in APP_PATHS.")
    else:
        speak(f"I could not open {app_name}. Check APP_PATHS for its path.")


def camera():
    if cv2 is None:
        speak("Please install opencv-python to use the camera.")
        return
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        cap.release()
        speak("I could not open the camera.")
        return
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                speak("The camera stopped providing frames.")
                break
            cv2.imshow("ATOM camera — press Esc to close", frame)
            if cv2.waitKey(30) & 0xFF == 27:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


def lookup_wikipedia(query):
    if wikipedia is None:
        speak("Please install wikipedia to use this feature.")
        return
    cleaned = query
    for phrase in ("wikipedia", "search for", "tell me about", "why", "where", "who is", "what is"):
        cleaned = cleaned.replace(phrase, "")
    cleaned = cleaned.strip()
    if not cleaned:
        speak("Please say what you want to look up.")
        return
    try:
        result = wikipedia.summary(cleaned, sentences=2, auto_suggest=True)
        speak(result)
    except Exception as exc:
        print(f"[Wikipedia error: {exc}]")
        speak("I couldn't find a suitable Wikipedia summary.")


def calculate():
    speak("Say a calculation such as 12 plus 4, or type it using two numbers and an operator.")
    raw = take_command()
    if not raw:
        raw = input("Calculation: ").strip().lower()
    replacements = {
        "multiplied by": "*", "times": "*", "multiply": "*", "×": "*",
        "divided by": "/", "divide by": "/", "divided": "/", "over": "/",
        "plus": "+", "add": "+", "minus": "-", "subtract": "-",
        "power": "**", "to the power of": "**",
    }
    expression = raw.lower()
    for word, symbol in sorted(replacements.items(), key=lambda item: -len(item[0])):
        expression = expression.replace(word, symbol)
    expression = expression.replace(" ", "")
    # Only accept a simple binary operation; never evaluate arbitrary Python.
    import re
    match = re.fullmatch(r"(-?\d+(?:\.\d+)?)(\*\*|[+\-*/])(-?\d+(?:\.\d+)?)", expression)
    if not match:
        speak("I couldn't understand that calculation. Try two numbers and one operator.")
        return
    left, op, right = match.groups()
    a, b = float(left), float(right)
    funcs = {"+": operator.add, "-": operator.sub, "*": operator.mul,
             "/": operator.truediv, "**": operator.pow}
    try:
        if op == "/" and b == 0:
            speak("Division by zero is undefined.")
            return
        if op == "**" and abs(b) > 100:
            speak("That exponent is too large.")
            return
        result = funcs[op](a, b)
        speak(f"The result is {result:g}")
    except (ArithmeticError, OverflowError) as exc:
        print(f"[Calculator error: {exc}]")
        speak("I couldn't calculate that safely.")


def get_location_approximate():
    """IP-derived location is approximate, not GPS."""
    try:
        ip_address = requests.get("https://api.ipify.org", timeout=REQUEST_TIMEOUT).text.strip()
        response = requests.get(
            f"https://get.geojs.io/v1/ip/geo/{ip_address}.json",
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        info = response.json()
        city = info.get("city") or "an unknown city"
        country = info.get("country") or "an unknown country"
        speak(f"My approximate network location is {city}, {country}. This is not GPS.")
    except Exception as exc:
        print(f"[Location error: {exc}]")
        speak("I couldn't determine the approximate network location.")


def send_text_message():
    if Client is None:
        speak("Please install twilio to use text messaging.")
        return
    sid = require_env("TWILIO_ACCOUNT_SID")
    token = require_env("TWILIO_AUTH_TOKEN")
    from_number = require_env("TWILIO_FROM_NUMBER")
    to_number = require_env("TWILIO_TO_NUMBER")
    if not all((sid, token, from_number, to_number)):
        return
    body = input("Type the message to send: ").strip()
    if not body:
        speak("The message is empty.")
        return
    if input(f"Send this text to {to_number}? Type YES to confirm: ").strip() != "YES":
        speak("Message cancelled.")
        return
    try:
        client = Client(sid, token)
        message = client.messages.create(body=body, from_=from_number, to=to_number)
        print(f"Message SID: {message.sid}")
        speak("Text message submitted.")
    except Exception as exc:
        print(f"[SMS error: {exc}]")
        speak("I could not send the text message.")


def wolfram_query(query):
    if wolframalpha is None:
        speak("Please install wolframalpha to use this feature.")
        return
    app_id = require_env("WOLFRAM_APP_ID")
    if not app_id:
        return
    question = query.replace("who is", "").replace("what is", "").strip()
    try:
        client = wolframalpha.Client(app_id)
        result = client.query(question)
        answer = next(iter(result.results), None)
        if answer and answer.text:
            speak(answer.text)
        else:
            speak("No result was returned.")
    except Exception as exc:
        print(f"[WolframAlpha error: {exc}]")
        speak("I couldn't retrieve an answer.")


def how_to_mode():
    if search_wikihow is None:
        speak("Please install pywikihow to use this feature.")
        return
    speak("What would you like instructions for?")
    query = take_command()
    if not query:
        return
    try:
        results = search_wikihow(query, max_results=1)
        if results:
            speak(results[0].summary)
            results[0].print()
        else:
            speak("I couldn't find instructions for that.")
    except Exception as exc:
        print(f"[How-to error: {exc}]")
        speak("I couldn't retrieve instructions.")


def take_screenshot():
    if pyautogui is None:
        speak("Please install pyautogui to use screenshots.")
        return
    name = input("Screenshot filename (without extension): ").strip()
    if not name:
        name = f"atom_screenshot_{datetime.now():%Y%m%d_%H%M%S}"
    # Keep the output in the current folder and prevent path-like names.
    safe_name = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_"))[:80]
    try:
        path = Path.cwd() / f"{safe_name or 'atom_screenshot'}.png"
        pyautogui.screenshot().save(path)
        speak(f"Screenshot saved as {path.name}.")
    except Exception as exc:
        print(f"[Screenshot error: {exc}]")
        speak("I couldn't take the screenshot.")


def write_note():
    note = take_command()
    if not note:
        note = input("Note: ").strip()
    include_time = input("Include date and time? (y/n): ").strip().lower() in {"y", "yes"}
    path = Path.cwd() / "atom_notes.txt"
    with path.open("a", encoding="utf-8") as file:
        if include_time:
            file.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " — ")
        file.write(note + "\n")
    speak(f"Note saved to {path.name}.")


def handle_command(query):
    """Handle one recognised command. Returns False when ATOM should stop."""
    if not query:
        return True

    if "you can sleep now" in query or query in {"exit atom", "quit atom", "stop atom"}:
        speak("Okay, boss. Call me whenever you need me.")
        return False
    elif "open notepad" in query:
        open_app("notepad")
    elif "open reader" in query or "open acrobat" in query:
        open_app("acrobat")
    elif "open my file" in query:
        folder = Path(PERSONAL_FOLDER)
        if folder.exists():
            try:
                os.startfile(str(folder))
            except (AttributeError, OSError):
                webbrowser.open(folder.as_uri())
        else:
            speak("The configured personal folder was not found. Update PERSONAL_FOLDER.")
    elif "open google" in query or "open chrome" in query:
        open_app("chrome")
    elif "open browser" in query or "open edge" in query:
        open_app("edge")
    elif "open terminal" in query:
        if sys.platform == "win32":
            subprocess.Popen(["cmd"])
        else:
            speak("Terminal launching depends on your operating system; open it manually.")
    elif "explorer" in query or "open file manager" in query:
        if sys.platform == "win32":
            subprocess.Popen(["explorer"])
        else:
            webbrowser.open(Path.home().as_uri())
    elif "open camera" in query:
        camera()
    elif "ip address" in query:
        try:
            ip = requests.get("https://api.ipify.org", timeout=REQUEST_TIMEOUT).text.strip()
            speak(f"Your public IP address is {ip}.")
        except Exception as exc:
            print(f"[IP lookup error: {exc}]")
            speak("I couldn't retrieve your public IP address.")
    elif "open youtube" in query:
        webbrowser.open("https://www.youtube.com")
    elif "open mail" in query or "open gmail" in query:
        webbrowser.open("https://mail.google.com")
    elif query.startswith("search"):
        term = query.removeprefix("search").strip()
        if not term:
            speak("What would you like to search for?")
            term = take_command()
        if term:
            webbrowser.open("https://www.google.com/search?q=" + quote_plus(term))
    elif "close notepad" in query and sys.platform == "win32":
        if input("Close all Notepad windows? Type YES to confirm: ").strip() == "YES":
            subprocess.run(["taskkill", "/im", "notepad.exe", "/t"], check=False)
    elif "close browser" in query and sys.platform == "win32":
        if input("Close all Edge windows? Type YES to confirm: ").strip() == "YES":
            subprocess.run(["taskkill", "/im", "msedge.exe", "/t"], check=False)
    elif "close google" in query and sys.platform == "win32":
        if input("Close all Chrome windows? Type YES to confirm: ").strip() == "YES":
            subprocess.run(["taskkill", "/im", "chrome.exe", "/t"], check=False)
    elif "tell me a joke" in query:
        if pyjokes is None:
            speak("Please install pyjokes to use jokes.")
        else:
            speak(pyjokes.get_joke())
    elif query == "restart" or "restart computer" in query or "restart my computer" in query:
        if sys.platform != "win32":
            speak("The restart command is configured for Windows only.")
        elif input("Restart this computer in 60 seconds? Type RESTART to confirm: ").strip() == "RESTART":
            subprocess.run(["shutdown", "/r", "/t", "60"], check=False)
            speak("Restart scheduled. Use shutdown /a in Windows to cancel.")
        else:
            speak("Restart cancelled.")
    elif "window" in query and ("switch" in query or "next" in query):
        if pyautogui is not None:
            pyautogui.hotkey("alt", "tab")
        else:
            speak("Please install pyautogui to switch windows.")
    elif "news" in query:
        get_news()
    elif query == "mail" or query.startswith("send email") or query.startswith("mail "):
        recipient = input("Recipient email address: ").strip()
        subject = input("Subject: ").strip()
        body = input("Email message: ").strip()
        attachment = input("Attachment path (leave blank for none): ").strip().strip('"')
        if input(f"Send email to {recipient}? Type YES to confirm: ").strip() == "YES":
            send_email(recipient, subject, body, attachment or None)
        else:
            speak("Email cancelled.")
    elif "my location" in query or query == "location":
        get_location_approximate()
    elif "screenshot" in query:
        take_screenshot()
    elif "read pdf" in query:
        read_pdf()
    elif "calculate" in query or query.startswith("what is") and any(word in query for word in ("plus", "minus", "times", "divided")):
        calculate()
    elif "temperature" in query:
        speak("I will search the web for the temperature.")
        webbrowser.open("https://www.google.com/search?q=" + quote_plus("current temperature in Telangana"))
    elif "text message" in query or "send sms" in query:
        send_text_message()
    elif "power" in query or "charging" in query or "battery" in query:
        if psutil is None:
            speak("Please install psutil to check battery status.")
        else:
            battery = psutil.sensors_battery()
            if battery is None:
                speak("Battery information is not available on this system.")
            else:
                speak(f"Your system battery is at {battery.percent} percent.")
                if not battery.power_plugged and battery.percent <= 15:
                    speak("Battery is low. Please connect the charger.")
    elif query.startswith("who is") or query.startswith("what is"):
        wolfram_query(query)
    elif "wikipedia" in query or query.startswith("why ") or query.startswith("where ") or query.startswith("tell me about"):
        lookup_wikipedia(query)
    elif "how to do mode" in query:
        how_to_mode()
    elif "volume up" in query:
        if pyautogui is not None:
            pyautogui.press("volumeup")
    elif "volume down" in query:
        if pyautogui is not None:
            pyautogui.press("volumedown")
    elif "mute" in query:
        if pyautogui is not None:
            pyautogui.press("volumemute")
    elif query == "sleep":
        speak("Say 'you can sleep now' or 'exit ATOM' to stop the assistant.")
    elif "song" in query or "play music" in query:
        if pywhatkit is None:
            speak("Please install pywhatkit to play songs.")
        else:
            song = input("Song to play on YouTube: ").strip()
            if song:
                pywhatkit.playonyt(song)
    elif "write a note" in query:
        write_note()
    elif "what's your name" in query or "what is your name" in query:
        speak("My friends call me ATOM the Great.")
    elif "the time" in query or query == "time":
        speak(f"The time is {datetime.now():%H:%M:%S}.")
    elif query in {"thank you", "thanks", "thank you atom"}:
        speak("You're welcome, boss.")
    else:
        speak("I don't know that command yet. Try saying 'search for' followed by a topic.")
    return True


def main():
    wish_me()
    while True:
        query = take_command()
        if not query:
            continue
        if not handle_command(query):
            break


if __name__ == "__main__":
    print("ATOM is starting. Say a command, or say 'you can sleep now' to stop.")
    if sr is None:
        print("Speech recognition is not installed. Install SpeechRecognition and PyAudio.")
        print("You can still test commands by importing handle_command() and passing text.")
    else:
        main()

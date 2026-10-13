"""
ATOM - personal Python voice assistant (clean version).

Setup:
  pip install requests pyttsx3 SpeechRecognition pyaudio pyjokes pyautogui psutil
  pip install wikipedia pywhatkit pypdf wolframalpha pywikihow twilio opencv-python
  (all are optional except requests; missing ones just disable that feature)

Environment variables (only for the services you use):
  EMAIL_USER, EMAIL_PASS            (Gmail app password)
  NEWS_API_KEY
  WOLFRAM_APP_ID
  TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, TWILIO_TO_NUMBER

If no microphone / SpeechRecognition is available, ATOM switches to typed commands.
"""

from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from urllib.parse import quote_plus
import operator
import os
import re
import smtplib
import subprocess
import sys
import webbrowser

import requests

# ---------- Optional integrations ----------
def _optional(import_fn):
    try:
        return import_fn()
    except Exception:
        return None

cv2 = _optional(lambda: __import__("cv2"))
pyttsx3 = _optional(lambda: __import__("pyttsx3"))
sr = _optional(lambda: __import__("speech_recognition"))
pyjokes = _optional(lambda: __import__("pyjokes"))
pyautogui = _optional(lambda: __import__("pyautogui"))
psutil = _optional(lambda: __import__("psutil"))
wikipedia = _optional(lambda: __import__("wikipedia"))
pywhatkit = _optional(lambda: __import__("pywhatkit"))
wolframalpha = _optional(lambda: __import__("wolframalpha"))
search_wikihow = _optional(lambda: __import__("pywikihow", fromlist=["search_wikihow"]).search_wikihow)
Client = _optional(lambda: __import__("twilio.rest", fromlist=["Client"]).Client)

try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        PdfReader = None

# ---------- Config ----------
APP_PATHS = {
    "notepad": r"C:\Windows\System32\notepad.exe",
    "acrobat": r"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe",
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
}
PERSONAL_FOLDER = os.path.expanduser(r"~\OneDrive\Desktop\My folder")
REQUEST_TIMEOUT = 10
IS_WINDOWS = sys.platform == "win32"

# ---------- Text to speech ----------
engine = None
if pyttsx3 is not None:
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
    except Exception as exc:
        print(f"[Text-to-speech unavailable: {exc}]")


def speak(message):
    """Print and (if possible) speak a message."""
    print(f"ATOM: {message}")
    if engine is not None:
        try:
            engine.say(str(message))
            engine.runAndWait()
        except Exception as exc:
            print(f"[Text-to-speech error: {exc}]")


# ---------- Input ----------
def voice_available():
    if sr is None:
        return False
    try:
        sr.Microphone()
        return True
    except Exception:
        return False


TEXT_MODE = not voice_available()


def take_command():
    """Return a lowercase command from the mic, or typed text if no mic is available."""
    if TEXT_MODE:
        try:
            return input("You: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return "exit atom"
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


def confirm(prompt, word="YES"):
    return input(f"{prompt} Type {word} to confirm: ").strip() == word


def require_env(name):
    value = os.environ.get(name)
    if not value:
        speak(f"Please configure the {name} environment variable first.")
        return None
    return value


def wish_me():
    hour = datetime.now().hour
    if hour < 12:
        speak("Good morning, boss!")
    elif hour < 18:
        speak("Good afternoon, boss!")
    else:
        speak("Good evening, boss!")
    speak("I am ATOM. Please tell me how I may help you.")


# ---------- Features ----------
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
        part = MIMEBase("application", "octet-stream")
        part.set_payload(path.read_bytes())
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


def email_flow():
    recipient = input("Recipient email address: ").strip()
    subject = input("Subject: ").strip()
    body = input("Email message: ").strip()
    attachment = input("Attachment path (blank for none): ").strip().strip('"')
    if confirm(f"Send email to {recipient}?"):
        send_email(recipient, subject, body, attachment or None)
    else:
        speak("Email cancelled.")


def get_news():
    api_key = require_env("NEWS_API_KEY")
    if not api_key:
        return
    try:
        response = requests.get(
            "https://newsapi.org/v2/everything",
            params={"q": "science OR technology", "sortBy": "publishedAt",
                    "language": "en", "pageSize": 5, "apiKey": api_key},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        articles = response.json().get("articles", [])
        if not articles:
            speak("I couldn't find any news articles.")
            return
        for i, article in enumerate(articles, start=1):
            speak(f"News {i}: {article.get('title') or 'Untitled article'}")
    except Exception as exc:
        print(f"[News error: {exc}]")
        speak("I could not retrieve the news right now.")


def read_pdf():
    if PdfReader is None:
        speak("Please install pypdf to use the PDF reader.")
        return
    path = Path(input("Enter the PDF file path: ").strip().strip('"')).expanduser()
    if not path.is_file():
        speak("I could not find that PDF file.")
        return
    try:
        reader = PdfReader(str(path))
        total = len(reader.pages)
        if total == 0:
            speak("This PDF has no pages.")
            return
        speak(f"This PDF has {total} pages.")
        page_number = int(input(f"Enter a page number from 1 to {total}: "))
        if not 1 <= page_number <= total:
            speak("That page number is out of range.")
            return
        text = reader.pages[page_number - 1].extract_text() or ""
        speak(text[:3500] if text else "I could not extract text from that page.")
    except Exception as exc:
        print(f"[PDF error: {exc}]")
        speak("I could not read that PDF.")


def open_path(target):
    """Open a file/folder with the OS default handler."""
    if IS_WINDOWS:
        os.startfile(str(target))  # noqa: windows only
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(target)])
    else:
        subprocess.Popen(["xdg-open", str(target)])


def open_app(app_name):
    path = APP_PATHS.get(app_name)
    if path and Path(path).exists():
        try:
            open_path(path)
            return
        except OSError as exc:
            print(exc)
    if app_name == "notepad" and IS_WINDOWS:
        subprocess.Popen(["notepad.exe"])
    elif app_name == "chrome":
        webbrowser.open("https://www.google.com")
    elif app_name == "edge":
        webbrowser.open("https://www.microsoft.com/edge")
    elif app_name == "acrobat":
        speak("Please check the Acrobat path in APP_PATHS.")
    else:
        speak(f"I could not open {app_name}. Check APP_PATHS.")


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
            cv2.imshow("ATOM camera - press Esc to close", frame)
            if cv2.waitKey(30) & 0xFF == 27:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


def lookup_wikipedia(query):
    if wikipedia is None:
        speak("Please install wikipedia to use this feature.")
        return
    cleaned = re.sub(r"^(search for|tell me about|why|where|who is|what is)\s+", "", query.strip())
    cleaned = cleaned.replace("wikipedia", "").strip()
    if not cleaned:
        speak("Please say what you want to look up.")
        return
    try:
        speak(wikipedia.summary(cleaned, sentences=2, auto_suggest=True))
    except Exception as exc:
        print(f"[Wikipedia error: {exc}]")
        speak("I couldn't find a suitable Wikipedia summary.")


CALC_WORDS = {
    "to the power of": "**", "multiplied by": "*", "divided by": "/",
    "divide by": "/", "multiply": "*", "divided": "/", "subtract": "-",
    "times": "*", "power": "**", "minus": "-", "plus": "+", "over": "/",
    "add": "+", "x": "*", "×": "*",
}
CALC_RE = re.compile(r"(-?\d+(?:\.\d+)?)(\*\*|[+\-*/])(-?\d+(?:\.\d+)?)")
CALC_FUNCS = {"+": operator.add, "-": operator.sub, "*": operator.mul,
              "/": operator.truediv, "**": operator.pow}


def parse_calculation(text):
    text = re.sub(r"\b(calculate|what is|what's|equals?)\b", " ", text.lower())
    for word, symbol in sorted(CALC_WORDS.items(), key=lambda kv: -len(kv[0])):
        if len(word) == 1:  # single-letter words (like 'x') only between digits
            text = re.sub(rf"(?<=\d)\s*{re.escape(word)}\s*(?=\d)", symbol, text)
        else:
            text = text.replace(word, symbol)
    return CALC_RE.fullmatch(text.replace(" ", ""))


def calculate(query=""):
    match = parse_calculation(query) if query else None
    if not match:
        speak("Say a calculation such as 12 plus 4.")
        raw = take_command()
        match = parse_calculation(raw) if raw else None
    if not match:
        speak("I couldn't understand that. Try two numbers and one operator.")
        return
    left, op, right = match.groups()
    a, b = float(left), float(right)
    if op == "/" and b == 0:
        speak("Division by zero is undefined.")
        return
    if op == "**" and abs(b) > 100:
        speak("That exponent is too large.")
        return
    try:
        speak(f"The result is {CALC_FUNCS[op](a, b):g}")
    except (ArithmeticError, OverflowError, ValueError) as exc:
        print(f"[Calculator error: {exc}]")
        speak("I couldn't calculate that safely.")


def get_public_ip():
    return requests.get("https://api.ipify.org", timeout=REQUEST_TIMEOUT).text.strip()


def get_location_approximate():
    """IP-derived location is approximate, not GPS."""
    try:
        ip = get_public_ip()
        response = requests.get(f"https://get.geojs.io/v1/ip/geo/{ip}.json", timeout=REQUEST_TIMEOUT)
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
    if not confirm(f"Send this text to {to_number}?"):
        speak("Message cancelled.")
        return
    try:
        message = Client(sid, token).messages.create(body=body, from_=from_number, to=to_number)
        print(f"Message SID: {message.sid}")
        speak("Text message submitted.")
    except Exception as exc:
        print(f"[SMS error: {exc}]")
        speak("I could not send the text message.")


def wolfram_query(query):
    """Try WolframAlpha; fall back to Wikipedia if unavailable or no answer."""
    question = re.sub(r"^(who is|what is)\s+", "", query).strip()
    if wolframalpha is not None and os.environ.get("WOLFRAM_APP_ID"):
        try:
            result = wolframalpha.Client(os.environ["WOLFRAM_APP_ID"]).query(question)
            answer = next(iter(result.results), None)
            if answer and answer.text:
                speak(answer.text)
                return
        except Exception as exc:
            print(f"[WolframAlpha error: {exc}]")
    lookup_wikipedia(query)


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
    safe = "".join(ch for ch in name if ch.isalnum() or ch in "-_")[:80]
    safe = safe or f"atom_screenshot_{datetime.now():%Y%m%d_%H%M%S}"
    try:
        path = Path.cwd() / f"{safe}.png"
        pyautogui.screenshot().save(path)
        speak(f"Screenshot saved as {path.name}.")
    except Exception as exc:
        print(f"[Screenshot error: {exc}]")
        speak("I couldn't take the screenshot.")


def write_note():
    speak("What should I write?")
    note = take_command() or input("Note: ").strip()
    if not note:
        speak("The note is empty.")
        return
    include_time = input("Include date and time? (y/n): ").strip().lower() in {"y", "yes"}
    path = Path.cwd() / "atom_notes.txt"
    with path.open("a", encoding="utf-8") as f:
        if include_time:
            f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " - ")
        f.write(note + "\n")
    speak(f"Note saved to {path.name}.")


def battery_status():
    if psutil is None:
        speak("Please install psutil to check battery status.")
        return
    battery = psutil.sensors_battery()
    if battery is None:
        speak("Battery information is not available on this system.")
        return
    speak(f"Your system battery is at {battery.percent:.0f} percent.")
    if not battery.power_plugged and battery.percent <= 15:
        speak("Battery is low. Please connect the charger.")


def weather_search(query):
    match = re.search(r"\bin ([a-z ]+)$", query)
    city = match.group(1).strip() if match else ""
    if not city:
        speak("Which city?")
        city = take_command()
    if not city:
        return
    speak(f"Searching the web for the temperature in {city}.")
    webbrowser.open("https://www.google.com/search?q=" + quote_plus(f"current temperature in {city}"))


def close_windows_app(exe, label):
    if confirm(f"Close all {label} windows?"):
        subprocess.run(["taskkill", "/im", exe, "/t"], check=False)


def press_key(key):
    if pyautogui is None:
        speak("Please install pyautogui for this feature.")
    else:
        pyautogui.press(key)


# ---------- Command routing ----------
def handle_command(query):
    """Handle one command. Returns False when ATOM should stop."""
    if not query:
        return True
    q = query

    if "you can sleep now" in q or q in {"exit atom", "quit atom", "stop atom", "exit", "quit"}:
        speak("Okay, boss. Call me whenever you need me.")
        return False
    elif "open notepad" in q:
        open_app("notepad")
    elif "open reader" in q or "open acrobat" in q:
        open_app("acrobat")
    elif "open my file" in q:
        folder = Path(PERSONAL_FOLDER)
        if folder.exists():
            try:
                open_path(folder)
            except OSError:
                webbrowser.open(folder.as_uri())
        else:
            speak("The personal folder was not found. Update PERSONAL_FOLDER.")
    elif "open google" in q or "open chrome" in q:
        open_app("chrome")
    elif "open browser" in q or "open edge" in q:
        open_app("edge")
    elif "open terminal" in q:
        if IS_WINDOWS:
            subprocess.Popen(["cmd"], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            speak("Please open the terminal manually on this system.")
    elif "explorer" in q or "open file manager" in q:
        try:
            open_path(Path.home())
        except OSError:
            webbrowser.open(Path.home().as_uri())
    elif "open camera" in q:
        camera()
    elif "ip address" in q:
        try:
            speak(f"Your public IP address is {get_public_ip()}.")
        except Exception as exc:
            print(f"[IP lookup error: {exc}]")
            speak("I couldn't retrieve your public IP address.")
    elif "open youtube" in q:
        webbrowser.open("https://www.youtube.com")
    elif "open mail" in q or "open gmail" in q:
        webbrowser.open("https://mail.google.com")
    elif q.startswith("search"):
        term = re.sub(r"^search(\s+for)?\s*", "", q).strip()
        if not term:
            speak("What would you like to search for?")
            term = take_command()
        if term:
            webbrowser.open("https://www.google.com/search?q=" + quote_plus(term))
    elif "close notepad" in q and IS_WINDOWS:
        close_windows_app("notepad.exe", "Notepad")
    elif "close browser" in q and IS_WINDOWS:
        close_windows_app("msedge.exe", "Edge")
    elif "close google" in q and IS_WINDOWS:
        close_windows_app("chrome.exe", "Chrome")
    elif "tell me a joke" in q:
        speak(pyjokes.get_joke() if pyjokes else "Please install pyjokes to use jokes.")
    elif q == "restart" or "restart computer" in q or "restart my computer" in q:
        if not IS_WINDOWS:
            speak("The restart command is configured for Windows only.")
        elif confirm("Restart this computer in 60 seconds?", "RESTART"):
            subprocess.run(["shutdown", "/r", "/t", "60"], check=False)
            speak("Restart scheduled. Run shutdown /a in Windows to cancel.")
        else:
            speak("Restart cancelled.")
    elif "window" in q and ("switch" in q or "next" in q):
        if pyautogui is not None:
            pyautogui.hotkey("alt", "tab")
        else:
            speak("Please install pyautogui to switch windows.")
    elif "news" in q:
        get_news()
    elif q == "mail" or q.startswith("send email") or q.startswith("mail "):
        email_flow()
    elif "my location" in q or q == "location":
        get_location_approximate()
    elif "screenshot" in q:
        take_screenshot()
    elif "read pdf" in q:
        read_pdf()
    elif "calculate" in q or (q.startswith("what is") and any(
            w in q for w in ("plus", "minus", "times", "divided", "multiplied", "power"))):
        calculate(q)
    elif "temperature" in q or "weather" in q:
        weather_search(q)
    elif "text message" in q or "send sms" in q:
        send_text_message()
    elif "battery" in q or "charging" in q or q in {"power", "power status"}:
        battery_status()
    elif q.startswith("who is") or q.startswith("what is"):
        wolfram_query(q)
    elif "wikipedia" in q or q.startswith("why ") or q.startswith("where ") or q.startswith("tell me about"):
        lookup_wikipedia(q)
    elif "how to do mode" in q:
        how_to_mode()
    elif "volume up" in q:
        press_key("volumeup")
    elif "volume down" in q:
        press_key("volumedown")
    elif "mute" in q:
        press_key("volumemute")
    elif q == "sleep":
        speak("Say 'you can sleep now' or 'exit ATOM' to stop the assistant.")
    elif "song" in q or "play music" in q:
        if pywhatkit is None:
            speak("Please install pywhatkit to play songs.")
        else:
            song = input("Song to play on YouTube: ").strip()
            if song:
                pywhatkit.playonyt(song)
    elif "write a note" in q:
        write_note()
    elif "what's your name" in q or "what is your name" in q:
        speak("My friends call me ATOM the Great.")
    elif "the time" in q or q == "time":
        speak(f"The time is {datetime.now():%H:%M:%S}.")
    elif q in {"thank you", "thanks", "thank you atom"}:
        speak("You're welcome, boss.")
    else:
        speak("I don't know that command yet. Try saying 'search for' followed by a topic.")
    return True


def main():
    if TEXT_MODE:
        print("[No microphone/SpeechRecognition found - using typed commands. "
              "Type 'exit atom' to quit.]")
    wish_me()
    while True:
        query = take_command()
        if query and not handle_command(query):
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nATOM stopped.")

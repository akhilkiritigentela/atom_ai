# ATOM — Personal Python Voice Assistant

ATOM is a personal Python voice-assistant project exploring speech recognition, text-to-speech, command-based desktop utilities, and optional online-service integrations.

The project began as a tutorial-based learning project and was subsequently modified and reorganised. It is a learning project, not a claim of original AI/ML research.

## Features in the code

- Wake word ("hey ATOM"), speech recognition and text-to-speech, with a typed-command fallback when no microphone is found
- Opening applications, websites, terminal, and file manager
- Closing selected Windows applications with confirmation
- Camera preview, mobile (IP) camera viewer and screenshots
- Wikipedia and WolframAlpha information lookup
- News lookup through NewsAPI
- Temperature search through a browser
- PDF text reading
- Basic arithmetic calculator
- Email sending with optional file attachment
- Optional SMS sending and phone calls through Twilio
- Alarms (checked between commands)
- Public IP lookup, approximate IP-derived location and internet speed test
- Battery status, volume controls and window switching
- Hide/show files in a chosen Windows folder
- How-to lookup, YouTube and local music playback, notes, jokes, date and time
- Instagram profile opener and a few conversational replies

**Important:** Features are present in the code but have not all been verified on your computer. External services require credentials and may have usage limits. Some application controls are Windows-specific.

## Requirements

Python 3.10 or newer is recommended. Install packages with:

```bash
python -m pip install -r requirements.txt
```

Only `requests` is required; any optional package that is missing simply disables its feature. PyAudio installation can differ by operating system. If microphone setup fails, follow the installation guidance for your OS and SpeechRecognition.

## Run

```bash
python main.py
```

Speech recognition uses an online service through SpeechRecognition and requires internet access.

- **Voice mode:** say "hey ATOM" (or "hello"/"hi") to wake it, give commands, say "you can sleep now" to make it wait again, and "thank you" while it is waiting to quit.
- **Typed mode:** used automatically if no microphone is available. Type commands at the `You:` prompt and `exit atom` to quit.

Example commands: `open notepad`, `search for python`, `calculate 12 plus 4`, `who is Ada Lovelace`, `news`, `temperature in <city>`, `set alarm for 7:30 am`, `take a screenshot`, `tell me a joke`, `what can you do`.

## Optional environment variables

Configure only the integrations you intend to use:

- `EMAIL_USER`
- `EMAIL_PASS`
- `NEWS_API_KEY`
- `WOLFRAM_APP_ID`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_FROM_NUMBER`
- `TWILIO_TO_NUMBER`
- `MOBILE_CAM_URL` (not a secret; address of your phone's IP-camera app)

Set these locally in your operating system or development environment. Never paste actual credentials into source code, README files, screenshots, or GitHub commits. For Gmail, use an app password where required, not your normal account password.

## Configuration

Review these constants near the top of `main.py` for settings specific to your computer:

- `APP_PATHS`, `PERSONAL_FOLDER`, `MUSIC_DIR`, `DESIGNER_PATH`
- `MY_SONGS_URL`, `MY_SITE_URL`, `MOBILE_CAM_URL`
- `NEWS_QUERY`, `NEWS_COUNT`
- `OWNER_NAME`, `WAKE_WORDS`

Avoid committing private paths, personal links, or local network addresses. Replace them with generic placeholders before making the repository public.

## Security and privacy

- Keep the repository private until you have reviewed and tested the code.
- Never commit passwords, API keys, tokens, personal documents, or private datasets.
- Add generated files such as `atom_notes.txt`, screenshots (`*.png`) and any `.env` file to `.gitignore`.
- If a real key or password was exposed, revoke or rotate it. Removing it from the latest file does not necessarily remove it from Git history.
- Commands that send email/SMS, place calls, hide folders, close apps or restart the computer require explicit confirmation.
- IP-based location is approximate and is not GPS.

## Development status

This is a cleaned-up baseline. A syntax check does not prove runtime functionality. Test microphone, camera, email, APIs, SMS, calls, and platform-specific commands on your own computer before relying on them.

## Acknowledgements

The project uses third-party Python libraries and was informed by tutorial-based learning. Add specific tutorial/source acknowledgements once the original sources have been identified.

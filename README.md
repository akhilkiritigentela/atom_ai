# ATOM — Personal Python Voice Assistant

ATOM is a personal Python voice-assistant project exploring speech recognition, text-to-speech, command-based desktop utilities, and optional online-service integrations.

The project began as a tutorial-based learning project and was subsequently modified and reorganised. It is a learning project, not a claim of original AI/ML research.

## Features in the code

- Speech recognition and text-to-speech
- Opening applications, websites, terminal, and file manager
- Closing selected Windows applications with confirmation
- Camera preview and screenshots
- Wikipedia and WolframAlpha information lookup
- News lookup through NewsAPI
- Temperature search through a browser
- PDF text reading
- Basic arithmetic calculator
- Email sending with optional file attachment
- Optional SMS sending through Twilio
- Public IP lookup and approximate IP-derived location
- Battery status, volume controls and window switching
- How-to lookup, YouTube playback, notes, jokes and time

**Important:** Features are present in the code but have not all been verified on your computer. External services require credentials and may have usage limits. Some application controls are Windows-specific.

## Requirements

Python 3.10 or newer is recommended. Install packages with:

```bash
python -m pip install -r requirements.txt
```

PyAudio installation can differ by operating system. If microphone setup fails, follow the installation guidance for your OS and SpeechRecognition.

## Run

```bash
python main.py
```

Use a microphone for voice commands. Speech recognition uses an online service through SpeechRecognition and requires internet access.

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

Set these locally in your operating system or development environment. Never paste actual credentials into source code, README files, screenshots, or GitHub commits. For Gmail, use an app password where required, not your normal account password.

## Configuration

Review `APP_PATHS` and `PERSONAL_FOLDER` in `main.py` for paths specific to your computer. Avoid committing private paths.

## Security and privacy

- Keep the repository private until you have reviewed and tested the code.
- Never commit passwords, API keys, tokens, personal documents, or private datasets.
- If a real key or password was exposed, revoke or rotate it. Removing it from the latest file does not necessarily remove it from Git history.
- Commands that send email/SMS or restart the computer should require explicit confirmation.
- IP-based location is approximate and is not GPS.

## Development status

This is a cleaned-up baseline. A syntax check does not prove runtime functionality. Test microphone, camera, email, APIs, SMS, and platform-specific commands on your own computer before relying on them.

## Acknowledgements

The project uses third-party Python libraries and was informed by tutorial-based learning. Add specific tutorial/source acknowledgements once the original sources have been identified.

# myAssistant

`myAssistant` is a Windows desktop voice assistant that listens for a wake word, transcribes a short spoken command, and routes it to either a small local intent model or Gemini. It can also capture the current desktop screen and send it to Gemini for visual analysis. A transparent PyQt overlay shows responses, wake activity, and a continuous scanning animation while screen analysis is in progress.

The project is intentionally split between two kinds of work:

- **Local actions:** greetings, locking the computer, closing windows, and exiting the assistant.
- **Gemini conversations:** questions and requests that are not handled by the local intent classifier.
- **Screen vision:** spoken `hey_jarvis` requests classified as `analyze_screen` capture the desktop and ask Gemini to interpret it.

## What It Uses

- OpenWakeWord for low-overhead wake-word detection
- SpeechRecognition with Google Speech Recognition for transcription
- A TF-IDF + Logistic Regression model for local command classification
- Gemini through the `google-genai` client for general questions
- PyAutoGUI for desktop screenshots used by the vision assistant
- Google TTS by default, with optional Gemini TTS support
- PyQt5 for the fullscreen transparent overlay
- PyAudio and NumPy for microphone input and energy-based speech detection

## Requirements

This project currently targets **Windows**. It uses `pywin32` for window management and `ctypes` for locking the workstation.

- Python 3.10 or newer
- A working microphone
- A display that can be captured by PyAutoGUI
- Internet access for OpenWakeWord model downloads, speech recognition, Gemini, and Google TTS
- A Gemini API key if Gemini responses are enabled

PyAudio can require additional Windows audio support depending on your Python installation. If installing it from `requirements.txt` fails, install a compatible PyAudio wheel for your Python version before continuing.

## Setup

Create and activate a virtual environment from the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The intent training script also requires scikit-learn. Install it if it is not already available:

```powershell
pip install scikit-learn
```

Create a `.env` file beside `main.py` and add your Gemini key:

```dotenv
GEMINI_API_KEY=your_gemini_api_key
```

The key is loaded at startup. Do not commit `.env` or paste the key into `config.ini`.

## Train the Local Model

The repository includes generated model files under `intentClassificationModel/models/`. Retrain them after changing the examples in `intent.json`:

```powershell
python intentClassificationModel\intent_train.py
```

This creates or replaces:

- `intentClassificationModel/models/intent_model.pkl`
- `intentClassificationModel/models/vectorizer.pkl`

The current local intents are `greetings`, `lock_computer`, `shutdown_computer`, `close_all_windows`, and `exit`.

## Run

Start the assistant from the project directory:

```powershell
python app.py
```

The supported application entry point is `app.py`, which delegates to the modular runtime in `main.py` and keeps the public startup command stable.

The microphone listener runs in a background thread while the PyQt event loop owns the overlay. Speak the configured wake phrase, wait for the acknowledgement, and then give a command. The `hey_jarvis` wake word supports general Gemini requests and screen-analysis requests.

### Screen Analysis

Ask the assistant to analyze the current screen using the `hey_jarvis` wake word, for example:

```text
Hey Jarvis, analyze my screen
```

When the request is classified as `analyze_screen`, the assistant:

1. Captures the current desktop with PyAutoGUI.
2. Sends the screenshot and spoken prompt to the configured Gemini model.
3. Displays the continuous scan animation while Gemini is processing.
4. Stops the animation and reads the visual response aloud.

The scan animation is controlled by the response window through `trigger_scan(True)` and `trigger_scan(False)`. It is independent of the screen-capture and Gemini request logic.

## Configuration

Settings live in `config.ini`:

| Setting | Purpose |
| --- | --- |
| `wakephrase` | Configured OpenWakeWord model, `alexa` by default |
| `sensitivity` | Documented configuration value for wake-word sensitivity |
| `general_system_prompt` | Controls Gemini response style; the default asks for very brief plain-text answers |
| `vision_system_prompt` | Controls the response format for screen-analysis requests |
| `gemini_model` | Gemini model passed to the API client |
| `gemini_tts` | Set to `true` to use the project Gemini TTS path instead of Google TTS |

The code also loads `hey_jarvis` as a second wake-word model. The configured phrase uses the local intent model, while `hey_jarvis` sends the spoken command to the Gemini task classifier. That classifier routes requests to either general chat or screen analysis.

## Safety Notes

- The assistant asks for spoken confirmation before shutdown and exit actions.
- The operating-system shutdown command is currently commented out in `main.py`, so recognizing `shutdown_computer` does not power off the machine yet.
- `close_all_windows` posts close messages to visible top-level windows. Use it carefully.
- Screen analysis captures the current desktop and sends the screenshot to Gemini. Do not use it while private or sensitive information is visible unless you are comfortable sharing that image with the configured Gemini service.
- The overlay is transparent for input and does not provide a clickable control surface. Stop the process with `Ctrl+C` when needed.

## Project Layout

```text
main.py                              Current application entry point and runtime loop
config/                              Typed application settings
core/                                Shared data contracts, states, and exceptions
utils/                               Project paths and logging helpers
audio/                               Audio input and speech service boundary
ai/                                  Gemini, classifier, and vision service boundary
actions/                             Local actions, confirmation, and dispatch boundary
storage/                             JSON repository and SQLite database boundary
ui/                                  Planned UI boundary
orchestration/                       Planned assistant coordination boundary
tests/                               Configuration and path tests
myGUI.py                             Current transparent response overlay
text_to_speech.py                    Current optional Gemini TTS helper
config.ini                           Active runtime configuration
requirements.txt                     Python dependencies
intentClassificationModel/
    intent.json                         Local intent examples
    intent_train.py                     TF-IDF and Logistic Regression training
    models/                             Serialized classifier and vectorizer
```

The modular directories are being introduced incrementally. Phases 1 through 6 currently provide the `config`, `core`, `utils`, `audio`, `ai`, `storage`, and `actions` foundations; UI extraction and orchestration remain in later phases.

`chat_history.json` remains the active storage format for now. The `storage/database.py` SQLite boundary and `assistant.db` path are prepared for a later migration, but the assistant does not create or use the database yet.

Local computer operations are dispatched through `actions/registry.py`. Destructive operations require explicit spoken confirmation, and shutdown remains disabled until an explicit shutdown command is configured.

## Troubleshooting

**The assistant cannot hear me**

Check that Windows exposes the intended microphone and that no other application has taken exclusive control of it. The listener expects mono 16 kHz audio.

**The wake word never triggers**

OpenWakeWord downloads its models on startup. Confirm the machine has internet access and that the configured phrase corresponds to an available model.

**Gemini is not available**

Check that `.env` is in the same directory as `main.py`, the variable is named exactly `GEMINI_API_KEY`, and the key is valid.

**Screen analysis does not work**

Confirm that `pyautogui` is installed, the Gemini API key is valid, and the spoken request is routed to the `analyze_screen` intent. Screen capture permissions, remote desktop sessions, or protected application windows can also prevent the screenshot from containing the expected content.

**The local model behaves unexpectedly**

Add representative examples to `intentClassificationModel/intent.json`, retrain the model, and start `main.py` again.
# myAssistant

`myAssistant` is a Windows desktop voice assistant that listens for a wake word, transcribes a short spoken command, and routes it to either a small local intent model or Gemini. It uses a transparent PyQt overlay to show responses and a glowing wave when the assistant wakes up.

The project is intentionally split between two kinds of work:

- **Local actions:** greetings, locking the computer, closing windows, and exiting the assistant.
- **Gemini conversations:** questions and requests that are not handled by the local intent classifier.

## What It Uses

- OpenWakeWord for low-overhead wake-word detection
- SpeechRecognition with Google Speech Recognition for transcription
- A TF-IDF + Logistic Regression model for local command classification
- Gemini through the `google-genai` client for general questions
- Google TTS by default, with optional Gemini TTS support
- PyQt5 for the fullscreen transparent overlay
- PyAudio and NumPy for microphone input and energy-based speech detection

## Requirements

This project currently targets **Windows**. It uses `pywin32` for window management and `ctypes` for locking the workstation.

- Python 3.10 or newer
- A working microphone
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
python main.py
```

The microphone listener runs in a background thread while the PyQt event loop owns the overlay. Speak the configured wake phrase, wait for the acknowledgement, and then give a command.

## Configuration

Settings live in `config.ini`:

| Setting | Purpose |
| --- | --- |
| `wakephrase` | Configured OpenWakeWord model, `alexa` by default |
| `sensitivity` | Documented configuration value for wake-word sensitivity |
| `system_prompt` | Controls Gemini response style; the default asks for very brief plain-text answers |
| `gemini_model` | Gemini model passed to the API client |
| `gemini_tts` | Set to `true` to use the project Gemini TTS path instead of Google TTS |

The code also loads `hey_jarvis` as a second wake-word model. The configured phrase and `hey_jarvis` currently use different response paths: the configured phrase uses the local intent model, while `hey_jarvis` sends the spoken command to Gemini.

## Safety Notes

- The assistant asks for spoken confirmation before shutdown and exit actions.
- The operating-system shutdown command is currently commented out in `main.py`, so recognizing `shutdown_computer` does not power off the machine yet.
- `close_all_windows` posts close messages to visible top-level windows. Use it carefully.
- The overlay is transparent for input and does not provide a clickable control surface. Stop the process with `Ctrl+C` when needed.

## Project Layout

```text
main.py                              Audio loop, routing, and assistant lifecycle
myGUI.py                             Transparent response overlay and wake animation
text_to_speech.py                    Optional Gemini TTS helper
config.ini                           Runtime configuration
requirements.txt                     Python dependencies
intentClassificationModel/
    intent.json                         Local intent examples
    intent_train.py                     TF-IDF and Logistic Regression training
    models/                             Serialized classifier and vectorizer
```

## Troubleshooting

**The assistant cannot hear me**

Check that Windows exposes the intended microphone and that no other application has taken exclusive control of it. The listener expects mono 16 kHz audio.

**The wake word never triggers**

OpenWakeWord downloads its models on startup. Confirm the machine has internet access and that the configured phrase corresponds to an available model.

**Gemini is not available**

Check that `.env` is in the same directory as `main.py`, the variable is named exactly `GEMINI_API_KEY`, and the key is valid.

**The local model behaves unexpectedly**

Add representative examples to `intentClassificationModel/intent.json`, retrain the model, and start `main.py` again.
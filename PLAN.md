# Refactoring Plan

## Goal

Refactor the assistant into a modular architecture with clear boundaries between configuration, audio, AI services, actions, persistence, UI, and orchestration while preserving current user-visible behavior.

## Guiding Principles

- Preserve existing behavior before adding new features.
- Keep hardware, operating-system APIs, external APIs, and UI code behind dedicated modules.
- Keep orchestration focused on coordinating services.
- Make small, reversible changes and validate each phase before continuing.
- Do not commit secrets, generated model artifacts, or machine-specific files.

## Target Structure

```text
myAssistant/
├── app.py
├── config/{__init__.py,settings.py,config.ini}
├── core/{__init__.py,models.py,events.py,exceptions.py}
├── audio/{__init__.py,microphone.py,wake_word.py,speech_to_text.py,text_to_speech.py}
├── ai/{__init__.py,gemini_client.py,intent_classifier.py,vision_analyzer.py,response_parser.py}
├── actions/{__init__.py,registry.py,computer_actions.py,calendar_actions.py,confirmation.py}
├── storage/{__init__.py,chat_history.py,database.py}
├── ui/{__init__.py,floating_window.py,ui_controller.py}
├── orchestration/{__init__.py,assistant.py,command_router.py}
├── utils/{__init__.py,audio_utils.py,paths.py,logging.py}
├── models/
├── tests/
├── requirements.txt
└── README.md
```

## Phase 0: Baseline and Safety

### Files to create or modify

- `PLAN.md`
- `README.md`
- `.gitignore`
- `tests/`

### Work to complete

- Record the current branch, working-tree state, startup command, and test result.
- Confirm required Python, system, model, and environment-variable dependencies.
- Verify credentials and local secrets are not tracked by Git.
- Run the current application far enough to record baseline behavior where hardware and credentials permit.
- Document known limitations such as unavailable microphone hardware or API credentials.

### Exit checklist

- [ ] Baseline test and startup results are recorded.
- [ ] Existing user changes were preserved.
- [ ] Secrets are excluded from version control.
- [ ] Behavior that must be preserved is documented.

## Phase 1: Core Types, Configuration, and Paths

### Files to create or modify

- `config/__init__.py`
- `config/settings.py`
- `config/config.ini`
- `core/__init__.py`
- `core/models.py`
- `core/events.py`
- `core/exceptions.py`
- `utils/__init__.py`
- `utils/paths.py`
- `utils/logging.py`
- `app.py`
- `main.py`

### Work to complete

- Create a `Settings` class for config files, environment variables, API keys, model names, wake phrases, thresholds, and feature flags.
- Resolve configuration, model, and storage paths from the project root instead of the current working directory.
- Define shared data classes for commands, intents, action requests, action results, and assistant responses.
- Define custom exceptions for configuration, audio, AI, storage, and action failures.
- Add centralized logging and make `main.py` use these utilities without changing behavior yet.

### Exit checklist

- [ ] Configuration has one supported access path.
- [ ] Paths work regardless of the launch directory.
- [ ] Shared data contracts are defined.
- [ ] Existing startup behavior still works.
- [ ] Configuration and path tests pass.

## Phase 2: Audio Input and Wake Words

### Files to create or modify

- `audio/__init__.py`
- `audio/microphone.py`
- `audio/wake_word.py`
- `audio/speech_to_text.py`
- `utils/audio_utils.py`
- `main.py`
- `tests/test_audio_utils.py`

### Work to complete

- Move PyAudio stream creation, recording, energy detection, silence detection, and cleanup into `Microphone`.
- Move openWakeWord loading and prediction handling into `WakeWordDetector`.
- Move Google Speech Recognition calls into `SpeechToTextService`.
- Preserve current command timeout and silence behavior.
- Add explicit handling for microphone initialization, transcription, and shutdown failures.
- Ensure each service closes resources that it owns.

### Exit checklist

- [ ] Wake-word detection behaves as before.
- [ ] Recording preserves timeout and silence behavior.
- [ ] Transcription errors are consistent.
- [ ] Audio resources close during normal and exceptional shutdown.
- [ ] Audio utility tests do not require a microphone.

## Phase 3: Text-to-Speech and Playback

### Files to create or modify

- `audio/text_to_speech.py`
- `utils/audio_utils.py`
- `main.py`
- `tests/test_audio_utils.py`

### Work to complete

- Move Gemini TTS and Google gTTS fallback behavior into `TextToSpeechService`.
- Move PCM-to-WAV conversion and MIME parsing into reusable audio utilities.
- Make provider selection a configuration concern.
- Define playback initialization, interruption, and cleanup behavior.
- Raise a clear service error for empty or invalid audio responses.

### Exit checklist

- [ ] Gemini TTS and Google TTS fallback behavior is preserved.
- [ ] WAV conversion and MIME parsing tests pass.
- [ ] Mixer resources do not leak.
- [ ] The main loop contains no provider-specific TTS logic.

## Phase 4: AI Providers and Response Contracts

### Files to create or modify

- `ai/__init__.py`
- `ai/gemini_client.py`
- `ai/intent_classifier.py`
- `ai/vision_analyzer.py`
- `ai/response_parser.py`
- `core/models.py`
- `main.py`
- `tests/test_intent_classifier.py`
- `tests/test_response_parser.py`

### Work to complete

- Wrap Gemini client creation, general conversation, multimodal requests, and TTS calls in `GeminiClient`.
- Move both pickled classifiers and vectorizers into `IntentClassifier`.
- Move screenshot capture and vision requests into `VisionAnalyzer`.
- Send the screenshot with its actual MIME type.
- Parse and validate action JSON through `ResponseParser`.
- Reject malformed JSON, unknown actions, missing fields, and unexpected parameters.
- Guarantee scan-state cleanup when a vision request fails.

### Exit checklist

- [ ] `main.py` no longer constructs Gemini payloads directly.
- [ ] Intent models load through one service.
- [ ] Vision responses become validated domain objects.
- [ ] API errors and empty responses are consistent.
- [ ] Parser tests cover valid and invalid responses.

## Phase 5: Storage and Database Boundary

### Files to create or modify

- `storage/__init__.py`
- `storage/chat_history.py`
- `storage/database.py`
- `utils/paths.py`
- `README.md`
- `tests/test_chat_history.py`

### Work to complete

- Create a `ChatHistoryRepository` for `chat_history.json`.
- Keep serialization and file access out of orchestration and AI modules.
- Define the database connection, schema, and repository boundary for future persistence.
- Decide whether JSON remains active or whether migration is required now.
- Define behavior for missing or corrupt history files.
- Document storage location, format, and migration expectations.

### Exit checklist

- [ ] Chat history has one owner.
- [ ] Storage paths use the path utilities.
- [ ] Missing and corrupt history behavior is defined.
- [ ] The database boundary is documented even if migration is deferred.
- [ ] No unrelated behavior changed.

## Phase 6: Local Actions and Confirmation

### Files to create or modify

- `actions/__init__.py`
- `actions/registry.py`
- `actions/computer_actions.py`
- `actions/calendar_actions.py`
- `actions/confirmation.py`
- `core/models.py`
- `main.py`
- `tests/test_actions.py`

### Work to complete

- Move Windows operations such as locking, closing windows, shutdown, and exit into `ComputerActions`.
- Move calendar validation and event creation into `CalendarActions`.
- Move confirmation prompting and response interpretation into `ConfirmationService`.
- Replace the long intent chain with a registry of handlers.
- Require explicit confirmation for destructive operations.
- Mock Windows APIs in tests so no real machine actions execute.

### Exit checklist

- [ ] Actions run independently of the assistant loop.
- [ ] Registry-based dispatch replaces the central intent chain.
- [ ] Destructive actions require confirmation.
- [ ] Calendar input is validated.
- [ ] Action tests are safe and deterministic.

## Phase 7: UI Extraction and Integration

### Files to create or modify

- `ui/__init__.py`
- `ui/floating_window.py`
- `ui/ui_controller.py`
- `core/events.py`
- `main.py`
- `myGUI.py`

### Work to complete

- Move `FloatingWindow` from `myGUI.py` to `ui/floating_window.py`.
- Keep painting, animations, labels, and Qt signals inside the widget.
- Create `UIController` for visibility, response text, wave animation, and scan animation.
- Ensure GUI updates from worker code use Qt signals or queued calls.
- Remove direct GUI operations from audio, AI, and action services.
- Delete or deprecate `myGUI.py` only after all imports are migrated.

### Exit checklist

- [ ] The UI can start without importing business logic.
- [ ] Worker code does not directly mutate Qt widgets.
- [ ] Existing overlay behavior is preserved.
- [ ] UI state is driven by explicit events or controller methods.
- [ ] Duplicate UI implementations are removed.

## Phase 8: Orchestration and Command Routing

### Files to create or modify

- `orchestration/__init__.py`
- `orchestration/assistant.py`
- `orchestration/command_router.py`
- `app.py`
- `main.py`
- `core/events.py`
- `tests/test_command_router.py`

### Work to complete

- Create an `Assistant` class for wake-word detection, recording, transcription, classification, routing, responses, and shutdown.
- Create a `CommandRouter` for local actions, general Gemini conversation, and screen analysis.
- Replace duplicated wake-word branches with one shared command-processing flow where behavior is equivalent.
- Inject services into the assistant instead of constructing dependencies inside the loop.
- Define states such as idle, listening, thinking, speaking, scanning, and stopping.
- Add clean cancellation and shutdown behavior.

### Exit checklist

- [ ] The assistant loop contains orchestration only.
- [ ] Equivalent wake-word flows share command processing.
- [ ] Services can be replaced with test doubles.
- [ ] Shutdown stops all services predictably.
- [ ] Router tests cover every supported intent category.

## Phase 9: Remove Legacy Structure and Harden the Project

### Files to create or modify

- `main.py`
- `myGUI.py`
- `text_to_speech.py`
- `requirements.txt`
- `README.md`
- `.gitignore`
- `tests/`
- Any remaining modules with obsolete imports

### Work to complete

- Remove compatibility code and duplicate implementations after migration.
- Remove unused imports, globals, dead functions, and obsolete comments.
- Verify dependency declarations against actual imports.
- Document installation, startup, configuration, testing, and troubleshooting.
- Add failure-path and cleanup tests.
- Run formatting, linting, type checking, the complete test suite, and a manual smoke test.

### Exit checklist

- [ ] No production code imports the old module layout.
- [ ] No obsolete entry points remain unintentionally.
- [ ] The complete test suite passes.
- [ ] Manual testing covers wake words, speech, TTS, chat, vision, actions, and shutdown.
- [ ] Documentation matches the final structure.

## Final Validation

- [ ] A clean environment installs dependencies from `requirements.txt`.
- [ ] The documented startup command works.
- [ ] The application works outside the repository root.
- [ ] Missing credentials and audio devices produce clear errors.
- [ ] API failures do not leave scan state active.
- [ ] Shutdown leaves no microphone, mixer, or Qt resources open.
- [ ] Unit tests do not require live API calls, real microphone input, or real Windows actions.
- [ ] Secrets and generated local files are excluded from version control.

## Refactoring Rule

Complete and validate each phase before starting the next. If a phase exposes an existing bug, fix only what is required to preserve the behavior being migrated; defer unrelated feature work until the modular architecture is stable.

# 🧠 BitVoid — Personal Voice Assistant (Prototype)

BitVoid is a personal AI-driven voice assistant prototype designed to simulate real-time conversations with a local Large Language Model (LLM) using voice input and output.

## 🎯 Current Progress

- [X]  🎙️ Speech-to-Text (STT) implemented using [Vosk] for accurate offline speech recognition.
- [X]  🗣️ Text-to-Speech (TTS) functionality implemented leveraging [Edge-TTS] for natural voice output.
- [X]  🤖 Local LLM Integration through [Ollama] running models like LLaMA 3.1 on your local machine.
- [X]  🔄 Basic asynchronous interactive loop prototype connecting speech input, AI processing, and voice output.
- [X]  🗂️ Organized project structure with modular design separating core logic, I/O methods, memory management, and model interface.
- [ ]  🧠 Simple memory manager implemented for storing and retrieving conversational context.
- [ ]  💾 Automatic message logging with timestamps (planned).
- [ ]  🧩 Advanced personalization and dynamic learning modules (planned).
- [ ]  🔧 Robust error handling and full async concurrency enhancements (planned).
- [ ]  📦 Dependencies

Install required packages:

### `pip install -r requirements.txt`

---

## ⚠️ Required Model Download (at lease for now)

This project uses the Vosk speech recognition model, which is not included in the repository due to its large size.
📥 How to Set Up the Model

1. Download an English model from the official Vosk website: [Vosk](

- ✅ Recommended for high accuracy: vosk-model-en-us-0.22
- 🟢 Smaller and faster: vosk-model-small-en-us-0.15

2. Extract the downloaded model into your project directory.
3. Open the config.json file in config folder and update the `vosk_model` field to match the folder name:

```json
{
    "vosk_model": "assets/vosk-model-en-us-0.22", <-- that's what you need to update
    "sample_rate": 16000,
    "chunk": 8000,
    "log_file": "",
    "ollama_model": "llama3.1",
    "ollama_url": "http://localhost:11434",
    "ollama_post": "http://localhost:11434/api/chat"
}
```

## 🗂️ Project Structure Overview

```
BitVoid/

├──bitvoid/
| |
| ├── core/
| │   ├── bitvoid.py          # Main assistant logic orchestrator (BitVoid class)
| │   ├── memory_manager.py   # Memory module for storing conversation context
| │   └── ollama_model.py     # Interface to local LLM via Ollama
| │
| ├── config/
| │   ├── config.json         # External configuration file (paths, audio settings)
| │   └── Config.py           # Reads config.json and exposes usable config values
| │
| ├── io_methods/
| │   ├── stt.py              # Speech-to-Text using Vosk
| │   ├── tts.py              # Text-to-Speech using Edge-TTS
| │   └── chat.py             # Conversation Flow Controller (planned)
| │
| ├── utils/
| │   └── logger.py           # Logging utilities (planned)
| │
| └──data/
|    └── memory.json         # Persistent long-term memory file
├── tests/
|
├── .gitignore
├── README.md
├── requirement.txt
└── main.py                 # App entry point — initializes and runs BitVoid

```

## 🚀 Next Steps

- [ ] Complete implementation of the interactive conversation loop with real-time speech streaming.
- [ ] Develop dynamic memory and personalization to enable context-aware dialogue.
- [ ] Add automatic timestamped logging for debugging and conversation history.
- [ ] Expand language support with translation layers (e.g., Whisper).
- [ ] Refine error handling and concurrency for smoother user experience.

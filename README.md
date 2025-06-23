# 🧠 Bitvoid — Personal Voice Assistant (Prototype)

Bitvoid is a personal AI-driven voice assistant prototype designed to simulate real-time conversation with a local LLM using voice input and output.

## 🎯 Features

* [X]  🎙️ **Speech-to-Text (STT)** using [Vosk].
* [X]  🗣️ **Text-to-Speech (TTS)** via [Edge-TTS].
* [X]  🤖 **LLM Integration** powered by [Ollama] with local models (e.g., LLaMA 3.1).
* [ ]  🔁 **Interactive loop**: Speak → Transcribe → Ask AI → Speak back.
* [ ]  💾 Automatic message logging with timestamps.
* [ ]  🔧 Fully asynchronous core with threading where needed.
* [ ]  🧩 Designed for modular expansion and long-term personalization.

## 📦 Dependencies

Install required packages:

```bash
pip install -r requirements.txt
```

## ⚠️ Required Model Download

This project uses the [Vosk](https://alphacephei.com/vosk/) speech recognition model, which is **not included** in the repository due to its large size.

### 📥 How to Set Up the Model

1. Download an English model from the official Vosk website:  
   [https://alphacephei.com/vosk/models](https://alphacephei.com/vosk/models)

   - ✅ For better accuracy (recommended): `vosk-model-en-us-0.22`  
   - 🟢 For faster performance and smaller size: `vosk-model-small-en-us-0.15`

2. Extract the downloaded model into your project directory.

3. Open the `config.json` file and update the `model_path` to match the folder name:

```json
{
  "model_path": "vosk-model-en-us-0.22",
  "sample_rate": 16000,
  "chunk": 8000,
  "log_file": "mic_log.txt"
}

# 🧠 Coreon —  Assistant (Prototype)

Coreon is a personal AI-driven voice assistant prototype designed to simulate real-time conversations with a local Large Language Model (LLM).

## 🎯 Current Progress Summary

### ✅ Completed

* **Local LLM Integration** using [Ollama] (LLaMA 3.1 or other models).
* **Basic architecture and modular project structure**:
  * `core/`: Logic (e.g., ollama model interface)
  * `data/`: Database models
  * `utils/`: Helpers (e.g., logger)
* **Database design finalized and implemented**:
  * `session`, `conversation`, `embedding`, `reference`, `memory`
  * Proper foreign key relations and cascade behavior in place
* **Basic chat logic with logging and session creation**

### 🛠 In Progress

* **Refactor `ollama_model.py`**:
  * Separate model communication logic
  * Clean, structured sync/async methods
  * Remove unrelated responsibilities (only chat and generation logic should live here)
* **Design and implement `reference/` package**:
  * `reference_management.py`: Orchestrator
  * `reference.py`: Data class for reference item
  * `search_query.py`: Represents a search operation metadata

### ⏸ On Hold

* **Config system (`config/`)**:
  * Current usage paused until needed (e.g., dynamic model loading, user preferences)

### 🚧 Planned (Next Phase)

* **Implement memory logic (`memory_management.py`)**
  * Store recent dialogue context
  * Retrieve conversation windows for embedding and continuity
* **Use database actively in flow:**
  * Embed user prompts and assistant replies
  * Log related references and search actions
* **Add reference-aware generation**
  * If user asks a question → check if info exists in `reference`
  * Else → auto-search, summarize, store

## ✍ Notes

* `database.py` is currently the most complete and stable module.
* Focus now shifts to **wiring** the DB with actual assistant behavior.
* `reference/` will be critical to long-term knowledge management.
* Modular thinking remains key — avoid bloated files.

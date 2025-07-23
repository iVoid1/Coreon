# ✅ Core TODO List — Foundation Phase

### 📁 setup.py / main.py

- [X]  Check if the database exists; create if missing.
- [X]  Verify core tables (sessions, conversations, embeddings, knowledge, etc.).
- [X]  Load AI model (via Ollama or alternative).
- [X]  Load session settings or start and store a new session.

### 📥 On new user input

- [ ]  Fetch all previous conversations in the current session.
- [ ]  Extract embeddings from those conversations.
- [ ]  Pass context + question to the AI model.
- [ ]  Receive response from the model.
- [ ]  Log the following in the database:
  - [ ]  Session ID
  - [ ]  Question
  - [ ]  Response
  - [ ]  Timestamp
  - [ ]  Response time duration

---

# 🔧 Internal Refinement Phase

- [X]  Use SQLAlchemy relationships instead of manual joins.
- [X]  Write test functions for database operations.
- [ ]  Implement detailed logging with a dedicated logger module for traceability.
- [X]  Make `fetch_conversation()` return JSON-ready data, not just ORM objects.
- [ ]  Create custom error handlers (e.g. InvalidSession, ModelFailure).
- [ ]  Separate STT, TTS, Embeddings, and other modules clearly into individual units.

---

# 🔮 Feature Development Phase 2

### 📊 Analytics & Monitoring

- [ ]  Calculate average model response time.
- [ ]  Analyze frequent words/topics.
- [ ]  User statistics dashboard: session counts, top topics, frequent questions.

### 🧠 search Management System

- [X]  Create `search` table for storing article summaries and long-term conversation insights.
- [ ]  Link conversations to learned search.
- [ ]  Automatically retrieve relevant search before answering queries.

### 🗃️ Backup & Restore

- [ ]  Implement periodic database backups.
- [ ]  Enable export/import of sessions.
- [ ]  (Optional) Support multi-device sync.

---

# 🛠️ Long-term Expansion & Advanced Features

- [ ]  Plugin system for adding new processing units (e.g. web search, PDF summarization).
- [ ]  Use SQLite FTS (Full Text Search) for fast in-database conversation searching.
- [ ]  Multi-user support with independent identities.
- [ ]  Permission system for modules (STT, TTS, Memory, Analysis).
- [ ]  Interactive GUI support (Electron, React) in the future.
- [ ]  Offline mode support and optional external data syncing.

---

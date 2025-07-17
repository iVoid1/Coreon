....✅ TODO List Based on the Plan:
📁 setup.py / main.py

* [X]  Check if the database exists; if not, create it.
* [X]  Verify the required tables (sessions, conversations, embeddings, ect..).
* [ ]  Load the model (via Ollama or another method).
* [ ]  Load session settings or start a new session and store it.

📥 Upon receiving new input from the user:

* [ ]  Fetch all previous conversations in the current session.
* [ ]  Extract embeddings for them.
* [ ]  Pass the context + question to the model.
* [ ]  Receive the response from the model.
* [ ]  Log everything in the database:

  * [ ]  Session ID
  * [ ]  Question
  * [ ]  Response
  * [ ]  Date and time
  * [ ]  Time taken to respond

📊 Future additions (Development Phase 2):

* [ ]  Calculate average response time.
* [ ]  User statistics interface.
* [ ]  Automatic backup storage.
* [ ]  Analysis of frequently asked questions or topics.

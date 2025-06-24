import json
import os
from datetime import datetime


class MemoryManager:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.memories = []

        if os.path.exists(filepath):
            self.load_memories()
        else:
            self.save_memories()  # create empty file if it doesn't exist

    def add_memory(self, content: str):
        timestamp = datetime.now().isoformat()
        self.memories.append({"timestamp": timestamp, "content": content})
        self.save_memories()

    def get_recent_context(self, limit: int = 5) -> list:
        return [m["content"] for m in self.memories[-limit:]]

    def save_memories(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.memories, f, indent=2, ensure_ascii=False)

    def load_memories(self):
        with open(self.filepath, 'r', encoding='utf-8') as f:
            self.memories = json.load(f)

    def clear_memory(self):
        self.memories = []
        self.save_memories()

    def memory_count(self) -> int:
        return len(self.memories)


# Example usage:
if __name__ == "__main__":
    memory = MemoryManager("memories/bitvoid-memory.json")
    memory.add_memory("Void is building BitVoid and feels inspired by Neuro-sama.")
    print(memory.get_recent_context())

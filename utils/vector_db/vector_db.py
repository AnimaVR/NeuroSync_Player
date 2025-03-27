# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

import os
import json
import numpy as np

# Define the path for the persistent vector DB JSON file.
VECTOR_DB_FILE = "chat_logs/vector_db.json"

class VectorDB:
    def __init__(self, db_file: str = VECTOR_DB_FILE):
        self.db_file = db_file
        self.entries = []
        self.load()

    def load(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    self.entries = json.load(f)
            except (json.JSONDecodeError, Exception) as e:
                print(f"Error loading vector DB: {e}")
                self.entries = []
        else:
            self.entries = []

    def save(self):
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(self.entries, f, indent=4)
        except Exception as e:
            print(f"Error saving vector DB: {e}")

    def add_entry(self, embedding: list, text: str, metadata: dict = None):
        if len(embedding) != 768:
            print("Warning: Embedding length is not 768.")

        entry = {
            "embedding": embedding,
            "text": text
        }
        if metadata:
            entry["metadata"] = metadata

        self.entries.append(entry)
        self.save()

    def cosine_similarity(self, vec1: list, vec2: list) -> float:
        if len(vec1) != len(vec2):
            raise ValueError("Both embeddings must be of the same length.")
        
        arr1 = np.array(vec1)
        arr2 = np.array(vec2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(arr1, arr2) / (norm1 * norm2))

    def search(self, query_embedding: list, top_n: int = 4) -> list:
        results = []
        for entry in self.entries:
            sim = self.cosine_similarity(query_embedding, entry["embedding"])
            results.append({"entry": entry, "similarity": sim})
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_n]

    def get_context_string(self, query_embedding: list, top_n: int = 4) -> str:
        results = self.search(query_embedding, top_n)
        if not results:
            return ""
        lines = ["\n\nRelated Memory:"]
        for i, result in enumerate(results, start=1):
            text = result["entry"].get("text", "")
            similarity = result["similarity"]
            lines.append(f"{text} (similarity: {similarity:.3f})")
        context_str = "\n".join(lines)
        while len(context_str) > 4000 and len(lines) > 1:
            lines.pop()
            context_str = "\n".join(lines)
        
        return context_str

vector_db = VectorDB()

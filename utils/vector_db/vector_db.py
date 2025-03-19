import os
import json
import numpy as np

# Define the path for the persistent vector DB JSON file.
VECTOR_DB_FILE = "chat_logs/vector_db.json"

class VectorDB:
    """
    A lightweight vector database that stores entries in memory and saves/loads
    them from a JSON file. Each entry is a dictionary containing:
      - 'embedding': a list of floats (expected length 768)
      - 'text': the associated text or context
      - Optional 'metadata': any additional information
    """
    def __init__(self, db_file: str = VECTOR_DB_FILE):
        self.db_file = db_file
        self.entries = []
        self.load()

    def load(self):
        """
        Loads the vector database from the JSON file into memory.
        If the file does not exist or is empty, initializes with an empty list.
        """
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
        """
        Saves the current in-memory vector DB entries to the JSON file.
        """
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(self.entries, f, indent=4)
        except Exception as e:
            print(f"Error saving vector DB: {e}")

    def add_entry(self, embedding: list, text: str, metadata: dict = None):
        """
        Adds a new entry to the vector DB and saves it.
        
        Args:
            embedding (list): A list of floats (expected length 768).
            text (str): The text or context associated with this embedding.
            metadata (dict, optional): Additional data to store with the entry.
        """
        # Check if embedding is of expected length (768)
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
        """
        Calculates cosine similarity between two vectors.
        
        Args:
            vec1 (list): First vector.
            vec2 (list): Second vector.
        
        Returns:
            float: The cosine similarity score.
        """
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
        """
        Searches for the top_n entries in the vector DB most similar to the query embedding.
        
        Args:
            query_embedding (list): The embedding to compare against.
            top_n (int, optional): Number of top matches to return. Default is 4.
        
        Returns:
            list: A list of dictionaries with keys 'entry' (the DB entry) and 'similarity'.
        """
        results = []
        for entry in self.entries:
            sim = self.cosine_similarity(query_embedding, entry["embedding"])
            results.append({"entry": entry, "similarity": sim})
        # Sort by similarity in descending order.
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_n]

    def get_context_string(self, query_embedding: list, top_n: int = 4) -> str:
        """
        Builds a context string from the top matching entries. This string can be appended
        after the system message contents.
        
        The returned format will be:
        
        Related Memory:
        <text> (similarity: X.XXX)
        <text> (similarity: X.XXX)
        ...
        
        Additionally, the string is ensured to be no longer than 4000 characters.
        If it exceeds the limit, the least similar entries are dropped until it fits.
        
        Args:
            query_embedding (list): The query embedding.
            top_n (int, optional): Number of top matches to include. Default is 4.
        
        Returns:
            str: The context string, or an empty string if no matches.
        """
        results = self.search(query_embedding, top_n)
        if not results:
            return ""
        # Start with a header.
        lines = ["\n\nRelated Memory:"]
        # Append each result.
        for i, result in enumerate(results, start=1):
            text = result["entry"].get("text", "")
            similarity = result["similarity"]
            lines.append(f"{text} (similarity: {similarity:.3f})")
        
        # Join lines to form the context string.
        context_str = "\n".join(lines)
        
        # If it exceeds the limit, remove the least similar entries (from the bottom) until it fits.
        while len(context_str) > 4000 and len(lines) > 1:
            # Remove the last entry (lowest similarity) before recalculating the context string.
            lines.pop()
            context_str = "\n".join(lines)
        
        return context_str

# Create a global instance for convenience.
vector_db = VectorDB()

"""
Vector Embeddings Generator - Create semantic embeddings using HuggingFace Transformers
"""
import logging
import numpy as np
from typing import List, Union

try:
    from sentence_transformers import SentenceTransformer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logging.warning("sentence-transformers not installed. Vector embeddings disabled.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorEmbedder:
    """
    Generate semantic vector embeddings for text using pre-trained models.
    Default model: all-MiniLM-L6-v2 (384 dimensions, fast, good quality)
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize embedder with specified model.
        
        Args:
            model_name: HuggingFace model name
                Options:
                - 'all-MiniLM-L6-v2': Fast, 384-dim (default)
                - 'all-mpnet-base-v2': Better quality, 768-dim, slower
                - 'paraphrase-MiniLM-L6-v2': Similar to MiniLM
        """
        self.model_name = model_name
        self.model = None
        self.embedding_dim = 384  # Default for MiniLM
        
        if HAS_TRANSFORMERS:
            try:
                logger.info(f"📥 Loading model: {model_name}...")
                self.model = SentenceTransformer(model_name)
                self.embedding_dim = self.model.get_sentence_embedding_dimension()
                logger.info(f"✅ Model loaded: {model_name} ({self.embedding_dim} dimensions)")
            except Exception as e:
                logger.error(f"❌ Failed to load model: {e}")
                self.model = None
        else:
            logger.warning("⚠️ Transformers not available. Using mock embeddings.")
    
    def encode(self, text: str, normalize: bool = True) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            normalize: Whether to normalize vector (for cosine similarity)
            
        Returns:
            Numpy array of shape (embedding_dim,)
        """
        if self.model:
            try:
                embedding = self.model.encode(
                    text,
                    convert_to_numpy=True,
                    normalize_embeddings=normalize
                )
                return embedding
            except Exception as e:
                logger.error(f"❌ Encoding failed: {e}")
                return self._mock_embedding()
        else:
            return self._mock_embedding()
    
    def batch_encode(self, texts: List[str], 
                     batch_size: int = 32,
                     normalize: bool = True) -> np.ndarray:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of input texts
            batch_size: Batch size for encoding
            normalize: Whether to normalize vectors
            
        Returns:
            Numpy array of shape (len(texts), embedding_dim)
        """
        if self.model:
            try:
                embeddings = self.model.encode(
                    texts,
                    batch_size=batch_size,
                    convert_to_numpy=True,
                    normalize_embeddings=normalize,
                    show_progress_bar=len(texts) > 100
                )
                logger.info(f"✅ Encoded {len(texts)} texts")
                return embeddings
            except Exception as e:
                logger.error(f"❌ Batch encoding failed: {e}")
                return np.array([self._mock_embedding() for _ in texts])
        else:
            return np.array([self._mock_embedding() for _ in texts])
    
    def calculate_similarity(self, embedding1: np.ndarray, 
                           embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        # Normalize if not already
        embedding1 = embedding1 / np.linalg.norm(embedding1)
        embedding2 = embedding2 / np.linalg.norm(embedding2)
        
        similarity = np.dot(embedding1, embedding2)
        return float(similarity)
    
    def find_most_similar(self, query_embedding: np.ndarray,
                         candidate_embeddings: np.ndarray,
                         top_k: int = 10) -> List[tuple]:
        """
        Find most similar embeddings to query.
        
        Args:
            query_embedding: Query vector (shape: embedding_dim)
            candidate_embeddings: Candidate vectors (shape: n_candidates, embedding_dim)
            top_k: Number of top results to return
            
        Returns:
            List of (index, similarity_score) tuples
        """
        # Normalize
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        candidates_norm = candidate_embeddings / np.linalg.norm(
            candidate_embeddings, axis=1, keepdims=True
        )
        
        # Calculate similarities
        similarities = np.dot(candidates_norm, query_norm)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = [(int(idx), float(similarities[idx])) for idx in top_indices]
        return results
    
    def _mock_embedding(self) -> np.ndarray:
        """
        Generate mock embedding for testing when model unavailable.
        
        Returns:
            Random normalized vector
        """
        # Generate random but consistent vector
        np.random.seed(42)
        vector = np.random.randn(self.embedding_dim)
        vector = vector / np.linalg.norm(vector)
        return vector
    
    def prepare_resume_text(self, resume_data: dict) -> str:
        """
        Prepare resume text for embedding by combining relevant fields.
        
        Args:
            resume_data: Dictionary with resume information
            
        Returns:
            Combined text optimized for embedding
        """
        components = []
        
        # Add skills (weighted heavily)
        if 'skills' in resume_data and resume_data['skills']:
            skills_text = "Skills: " + ", ".join(resume_data['skills'][:20])
            components.append(skills_text)
        
        # Add experience
        if 'years_experience' in resume_data:
            components.append(f"Experience: {resume_data['years_experience']} years")
        
        # Add education
        if 'education' in resume_data:
            components.append(f"Education: {resume_data['education']}")
        
        # Add raw text snippet (first 500 chars)
        if 'raw_text' in resume_data:
            text_snippet = resume_data['raw_text'][:500]
            components.append(text_snippet)
        
        combined_text = " | ".join(components)
        return combined_text
    
    def get_model_info(self) -> dict:
        """Get information about the current model."""
        return {
            'model_name': self.model_name,
            'embedding_dim': self.embedding_dim,
            'is_loaded': self.model is not None,
            'library': 'sentence-transformers' if HAS_TRANSFORMERS else 'mock'
        }


# Example usage
if __name__ == "__main__":
    embedder = VectorEmbedder()
    
    print(f"\n📊 Model Info: {embedder.get_model_info()}")
    
    # Single text encoding
    text1 = "Python developer with 5 years experience in data engineering"
    embedding1 = embedder.encode(text1)
    print(f"\n✅ Embedding shape: {embedding1.shape}")
    print(f"First 10 values: {embedding1[:10]}")
    
    # Batch encoding
    texts = [
        "Senior data engineer with AWS and Spark experience",
        "Frontend developer skilled in React and JavaScript",
        "Machine learning engineer with Python and TensorFlow"
    ]
    embeddings = embedder.batch_encode(texts)
    print(f"\n✅ Batch embeddings shape: {embeddings.shape}")
    
    # Similarity calculation
    text2 = "Data engineer with cloud and big data expertise"
    embedding2 = embedder.encode(text2)
    similarity = embedder.calculate_similarity(embedding1, embedding2)
    print(f"\n🔍 Similarity between texts: {similarity:.3f}")
    
    # Find most similar
    query = embedder.encode("Looking for Python data engineer")
    results = embedder.find_most_similar(query, embeddings, top_k=3)
    print(f"\n🎯 Top matches:")
    for idx, score in results:
        print(f"  {idx}: {texts[idx][:50]}... (score: {score:.3f})")

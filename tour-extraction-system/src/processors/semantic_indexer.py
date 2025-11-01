"""
Cria índice FAISS dos chunks para busca semântica.
"""
import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

from ..core.config import SystemConfig
from ..core.logger import Logger


class SemanticIndexer:
    """Indexador semântico usando FAISS"""
    
    def __init__(self, config: SystemConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self.model = None
        self.md_files = []
        self.texts = []
    
    def setup(self):
        """Inicializa modelo de embeddings"""
        os.makedirs(self.config.index_dir, exist_ok=True)
        self.model = SentenceTransformer(self.config.embedding_model)
        self.logger.info(f"Modelo carregado: {self.config.embedding_model}")
    
    def load_chunks(self):
        """Carrega chunks markdown"""
        self.md_files = sorted([
            os.path.join(self.config.chunks_dir, fn)
            for fn in os.listdir(self.config.chunks_dir)
            if fn.endswith(".md")
        ])
        
        self.texts = []
        for path in self.md_files:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.texts.append(f.read().strip())
            except Exception:
                self.texts.append("")
        
        self.logger.info(f"Carregados {len(self.texts)} chunks")
    
    def create_index(self):
        """Cria índice FAISS"""
        self.logger.info("Gerando embeddings...")
        
        embeddings = self.model.encode(
            self.texts,
            convert_to_numpy=True,
            normalize_embeddings=self.config.normalize_embeddings
        )
        
        # Cria índice FAISS (cosine similarity via inner product)
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)
        
        # Salva artefatos
        faiss.write_index(index, os.path.join(self.config.index_dir, "chunks.faiss"))
        np.save(os.path.join(self.config.index_dir, "embeddings.npy"), embeddings)
        
        with open(os.path.join(self.config.index_dir, "files.json"), "w", encoding="utf-8") as f:
            json.dump(self.md_files, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Índice criado: {len(self.md_files)} chunks indexados")

    def search_similar_chunks(self, text, top_k=3):
        """
        Retorna os índices dos top_k chunks semanticamente mais similares ao texto fornecido.
        """
        import faiss
        import numpy as np

        # Carrega índice, embeddings e textos
        index = faiss.read_index(os.path.join(self.config.index_dir, "chunks.faiss"))
        embeddings = np.load(os.path.join(self.config.index_dir, "embeddings.npy"))
        with open(os.path.join(self.config.index_dir, "files.json"), "r", encoding="utf-8") as f:
            md_files = json.load(f)
        if self.model is None:
            self.setup()
        # Embedding do texto de busca
        query_emb = self.model.encode([text], convert_to_numpy=True, normalize_embeddings=self.config.normalize_embeddings)
        # Busca top_k similares
        D, I = index.search(query_emb, top_k)
        indices = I[0]
        # Retorna textos e paths mais semelhantes (não retorna o próprio chunk em si)
        similar_chunks = []
        for idx in indices:
            if 0 <= idx < len(self.texts):
                similar_chunks.append({
                    "idx": idx,
                    "text": self.texts[idx],
                    "file": md_files[idx]
                })
        return similar_chunks
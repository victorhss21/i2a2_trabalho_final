"""
Gerenciamento de configuração via YAML.
"""
import yaml
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class SystemConfig:
    """Configuração centralizada do sistema"""
    
    # Diretórios
    uploads_dir: str
    chunks_dir: str
    index_dir: str
    results_dir: str
    
    # PDF Processing
    enable_ocr: bool
    pages_per_chunk: int
    
    # Indexing
    embedding_model: str
    normalize_embeddings: bool
    
    # Extraction
    llm_model: str
    temperature: float
    max_workers: int
    rate_limit: int
    max_context_chars: int
    
    # Export
    export_json: bool
    export_excel: bool
    excel_max_desc_len: int
    
    # Logging
    log_level: str
    
    @classmethod
    def from_yaml(cls, yaml_path: str = "config/settings.yaml") -> 'SystemConfig':
        """Carrega configuração de arquivo YAML"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return cls(
            uploads_dir=config['directories']['uploads'],
            chunks_dir=config['directories']['chunks'],
            index_dir=config['directories']['index'],
            results_dir=config['directories']['results'],
            enable_ocr=config['pdf_processing']['enable_ocr'],
            pages_per_chunk=config['pdf_processing']['pages_per_chunk'],
            embedding_model=config['indexing']['model'],
            normalize_embeddings=config['indexing']['normalize_embeddings'],
            llm_model=config['extraction']['llm_model'],
            temperature=config['extraction']['temperature'],
            max_workers=config['extraction']['max_workers'],
            rate_limit=config['extraction']['rate_limit_per_minute'],
            max_context_chars=config['extraction']['max_context_chars'],
            export_json=config['export']['formats']['json'],
            export_excel=config['export']['formats']['excel'],
            excel_max_desc_len=config['export']['excel_max_description_length'],
            log_level=config['logging']['level']
        )

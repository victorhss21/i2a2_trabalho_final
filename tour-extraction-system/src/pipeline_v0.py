"""
Orquestrador principal do pipeline.
"""
import time
from typing import Dict, Any

from .core.config import SystemConfig
from .core.logger import Logger
from .processors.pdf_chunker import PDFChunker
from .processors.semantic_indexer import SemanticIndexer
from .processors.tour_extractor import TourExtractor
from .processors.result_exporter import ResultExporter


class TourExtractionPipeline:
    """Pipeline completo de extração de tours"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.logger = Logger(config.log_level)
        
        # Inicializa processadores
        self.chunker = PDFChunker(config, self.logger)
        self.indexer = SemanticIndexer(config, self.logger)
        # self.extractor = TourExtractor(config, self.logger)
        self.extractor = TourExtractor(config, self.logger, indexer=self.indexer)
        self.exporter = ResultExporter(config, self.logger)
    
    def run(self, pdf_path: str) -> Dict[str, Any]:
        """
        Executa pipeline completo.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            Catálogo extraído com tours
        """
        start_time = time.time()
        
        self.logger.info("=" * 80)
        self.logger.info("TOUR EXTRACTION PIPELINE")
        self.logger.info(f"PDF: {pdf_path}")
        self.logger.info("=" * 80)
        
        try:
            # Etapa 1: Chunking
            self.logger.info("[1/3] Chunking de PDF")
            self.chunker.setup()
            self.chunker.process(pdf_path)
            
            # Etapa 2: Indexação
            self.logger.info("[2/3] Indexação Semântica")
            self.indexer.setup()
            self.indexer.load_chunks()
            self.indexer.create_index()
            
            # Etapa 3: Extração
            self.logger.info("[3/3] Extração de Tours")
            self.extractor.setup()
            catalog = self.extractor.extract()
            
            # Exportação
            self.logger.info("[FINALIZANDO] Exportando resultados")
            self.exporter.export(catalog)
            
            elapsed = time.time() - start_time
            self.logger.info("=" * 80)
            self.logger.info("PIPELINE CONCLUÍDO!")
            self.logger.info(f"Tempo: {elapsed:.2f}s ({elapsed/60:.2f} min)")
            self.logger.info(f"Tours extraídos: {len(catalog.get('tours', []))}")
            self.logger.info("=" * 80)
            
            return catalog
            
        except Exception as e:
            self.logger.error(f"ERRO CRÍTICO: {e}")
            raise

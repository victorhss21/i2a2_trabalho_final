"""
Orquestrador principal do pipeline de extração.
"""

import os
from .core.config import SystemConfig
from .core.logger import Logger
from .processors.pdf_chunker import PDFChunker
from .processors.semantic_indexer import SemanticIndexer
from .processors.tour_extractor import TourExtractor
from .processors.result_exporter import ResultExporter
from .processors.result_refiner import ResultRefiner

class TourExtractionPipeline:
    """Pipeline completo de extração de tours"""
    
    def __init__(self, config: SystemConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self.chunker = PDFChunker(config, logger)
        self.indexer = SemanticIndexer(config, logger)
        self.extractor = TourExtractor(config, logger, indexer=self.indexer)
        self.exporter = ResultExporter(config, logger)
        self.refiner = ResultRefiner(config, logger)
    
    def run(self, pdf_path: str):
        """Executa o pipeline completo"""
        self.logger.info("="*80)
        self.logger.info("TOUR EXTRACTION PIPELINE")
        self.logger.info(f"PDF: {pdf_path}")
        self.logger.info("="*80)
        
        # Etapa 1: Chunking
        self.logger.info("[1/4] Chunking de PDF")
        self.chunker.setup()
        self.chunker.process(pdf_path)
        
        # Etapa 2: Indexação
        self.logger.info("[2/4] Indexação Semântica")
        self.indexer.setup()
        self.indexer.load_chunks()
        self.indexer.create_index()
        
        # Etapa 3: Extração
        self.logger.info("[3/4] Extração de Tours")
        self.extractor.setup()
        catalog = self.extractor.extract()
        
        # Etapa 4: Exportação bruta
        self.logger.info("[4/4] Exportação e Refinamento")
        json_path, xlsx_path = self.exporter.export(catalog)
        
        # NOVA ETAPA: Refinamento para usuário final (se configurado)
        refined_xlsx = None
        if hasattr(self.config, 'export_refined') and self.config.export_refined and json_path:
            refined_xlsx = self.refiner.refine(json_path)
        
        # Log final
        self.logger.info("="*80)
        self.logger.info("✅ PIPELINE CONCLUÍDO COM SUCESSO!")
        if json_path:
            self.logger.info(f"📄 JSON completo: {json_path}")
        if xlsx_path:
            self.logger.info(f"📊 Excel bruto: {xlsx_path}")
        if refined_xlsx:
            self.logger.info(f"🎯 Excel refinado (FINAL): {refined_xlsx}")
        self.logger.info("="*80)

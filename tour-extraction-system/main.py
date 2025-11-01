"""
Ponto de entrada do sistema (CLI).
Futuro: adicionar interface web com Flask/FastAPI.
"""
import os
import argparse
from dotenv import load_dotenv

from src.core.logger import Logger
from src.core.config import SystemConfig
from src.pipeline import TourExtractionPipeline
from src.processors.result_refiner import ResultRefiner

# Carrega variáveis de ambiente
load_dotenv()


def main():
    """Ponto de entrada CLI"""
    parser = argparse.ArgumentParser(description="Tour Extraction System")
    parser.add_argument("--pdf", required=True, help="Caminho para o arquivo PDF")
    parser.add_argument("--config", default="config/settings.yaml", help="Arquivo de configuração")
    
    args = parser.parse_args()
    
    # Valida PDF
    if not os.path.exists(args.pdf):
        print(f"[ERRO] PDF não encontrado: {args.pdf}")
        return
    
    # Carrega configuração
    config = SystemConfig.from_yaml(args.config)
    
    # Executa pipeline
    logger = Logger()
    pipeline = TourExtractionPipeline(config, logger)
    pipeline.run(args.pdf)

    # # Executa refined do Excel obtido
    # logger = Logger("INFO")
    # refiner = ResultRefiner(config, logger)
    # refiner.refine("output/results/tours_extracted.json")


if __name__ == "__main__":
    main()

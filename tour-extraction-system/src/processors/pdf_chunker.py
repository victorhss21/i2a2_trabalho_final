"""
Converte PDF em chunks markdown por página.
"""
import os
import gc
import tempfile
from PyPDF2 import PdfReader, PdfWriter
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import PdfFormatOption

from ..core.config import SystemConfig
from ..core.logger import Logger


class PDFChunker:
    """Converte PDF em chunks markdown"""
    
    def __init__(self, config: SystemConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self.converter = None
    
    def setup(self):
        """Inicializa conversor Docling"""
        os.makedirs(self.config.chunks_dir, exist_ok=True)
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        
        # Limpa chunks antigos
        for fn in os.listdir(self.config.chunks_dir):
            if fn.endswith('.md'):
                os.remove(os.path.join(self.config.chunks_dir, fn))
        
        # Configura Docling
        pdf_options = PdfPipelineOptions(do_ocr=self.config.enable_ocr)
        self.converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_options)}
        )
        
        self.logger.info(f"PDF Chunker configurado (OCR: {self.config.enable_ocr})")
    
    def process(self, pdf_path: str) -> int:
        """
        Processa PDF e retorna número de chunks gerados.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            Número de páginas/chunks processados
        """
        reader = PdfReader(pdf_path)
        num_pages = len(reader.pages)
        self.logger.info(f"Processando {num_pages} páginas...")
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            for page_num in range(1, num_pages + 1):
                # Cria PDF temporário com uma página
                tmp_pdf = os.path.join(tmp_dir, f"page_{page_num:03d}.pdf")
                writer = PdfWriter()
                writer.add_page(reader.pages[page_num - 1])
                
                with open(tmp_pdf, "wb") as f:
                    writer.write(f)
                
                # Converte para markdown
                result = self.converter.convert(tmp_pdf)
                md_text = result.document.export_to_markdown()
                
                # Salva chunk
                out_path = os.path.join(self.config.chunks_dir, f"page_{page_num:03d}.md")
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(md_text)
                
                # Libera memória
                del result, md_text
                gc.collect()
        
        self.logger.info(f"Chunking concluído: {num_pages} páginas processadas")
        return num_pages

"""
Interface Streamlit para Tour Extraction System.
Permite upload de PDF e download do resultado refinado.
"""
import streamlit as st
import os
import tempfile
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv
from src.core.config import SystemConfig
from src.pipeline import TourExtractionPipeline

# Carrega variáveis de ambiente
load_dotenv()


class StreamlitLogger:
    """Logger que captura mensagens para display no Streamlit."""
    
    def __init__(self, status_container):
        self.status_container = status_container
        self.messages = []
    
    def info(self, msg: str):
        """Log de informação."""
        self.messages.append(("ℹ️", msg))
        self._update_display()
    
    def error(self, msg: str):
        """Log de erro."""
        self.messages.append(("❌", msg))
        self._update_display()
    
    def warning(self, msg: str):
        """Log de aviso."""
        self.messages.append(("⚠️", msg))
        self._update_display()
    
    def debug(self, msg: str):
        """Log de debug."""
        self.messages.append(("🔍", msg))
        self._update_display()
    
    def _update_display(self):
        """Atualiza display do status."""
        with self.status_container:
            for icon, msg in self.messages[-10:]:  # Mostra últimas 10 mensagens
                st.text(f"{icon} {msg}")


def main():
    """Interface principal do Streamlit."""
    
    # Configuração da página
    st.set_page_config(
        page_title="Tour Extraction System",
        page_icon="🌍",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Inicializa session_state para persistir dados entre reloads
    if 'processed' not in st.session_state:
        st.session_state.processed = False
    if 'xlsx_data' not in st.session_state:
        st.session_state.xlsx_data = None
    if 'json_data' not in st.session_state:
        st.session_state.json_data = None
    if 'df_preview' not in st.session_state:
        st.session_state.df_preview = None
    if 'stats' not in st.session_state:
        st.session_state.stats = {}
    
    # Título e descrição
    st.title("🌍 Tour Extraction System")
    st.markdown("""
    Extraia informações estruturadas de catálogos turísticos em PDF usando IA.
    """)
    
    # Verificação de API Key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("⚠️ OPENAI_API_KEY não encontrada no arquivo .env")
        st.stop()
    
    # Sidebar com configurações (opcional, limpa)
    with st.sidebar:
        st.header("⚙️ Configurações")
        config_file = st.text_input(
            "Arquivo de configuração",
            value="config/settings.yaml",
            help="Caminho para o arquivo YAML de configuração"
        )
        
        st.markdown("---")
        st.markdown("### 📊 Sobre o Sistema")
        st.markdown("""
        - **Processamento**: Multi-idioma
        - **IA**: GPT-4o-mini
        - **Saída**: Excel completo + JSON estruturado
        """)
    
    # Upload de arquivo
    st.header("📁 Upload do Catálogo")
    uploaded_file = st.file_uploader(
        "Selecione o arquivo PDF do catálogo turístico",
        type=["pdf"],
        help="Faça upload do PDF contendo informações de tours"
    )
    
    if uploaded_file is not None:
        # Informações do arquivo
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info(f"📄 Arquivo: **{uploaded_file.name}**")
        with col2:
            file_size = len(uploaded_file.getvalue()) / (1024 * 1024)
            st.metric("Tamanho", f"{file_size:.2f} MB")
        
        # Botão de processamento
        if st.button("🚀 Processar Catálogo", type="primary", width='stretch'):
            # Reseta estado de processamento
            st.session_state.processed = False
            st.session_state.xlsx_data = None
            st.session_state.json_data = None
            st.session_state.df_preview = None
            st.session_state.stats = {}
            
            # Container para status
            status_container = st.empty()
            progress_bar = st.progress(0)
            
            try:
                # Salva arquivo temporariamente
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                # Carrega configuração
                config = SystemConfig.from_yaml(config_file)
                
                # Cria logger customizado
                logger = StreamlitLogger(status_container)
                
                # Inicializa pipeline
                logger.info("Inicializando pipeline de extração...")
                pipeline = TourExtractionPipeline(config, logger)
                
                # Etapa 1: Chunking
                progress_bar.progress(10)
                logger.info("[1/4] Processando PDF...")
                pipeline.chunker.setup()
                pipeline.chunker.process(tmp_path)
                
                # Etapa 2: Indexação
                progress_bar.progress(30)
                logger.info("[2/4] Criando índice semântico...")
                pipeline.indexer.setup()
                pipeline.indexer.load_chunks()
                pipeline.indexer.create_index()
                
                # Etapa 3: Extração
                progress_bar.progress(50)
                logger.info("[3/4] Extraindo informações com IA...")
                pipeline.extractor.setup()
                catalog = pipeline.extractor.extract()
                
                # Etapa 4: Exportação
                progress_bar.progress(80)
                logger.info("[4/4] Gerando arquivos de saída...")
                json_path, xlsx_path = pipeline.exporter.export(catalog)
                
                # Refinamento (apenas para debug interno)
                refined_path = pipeline.refiner.refine(json_path)
                
                progress_bar.progress(100)
                logger.info("✅ Processamento concluído com sucesso!")
                
                # Limpa arquivo temporário
                os.unlink(tmp_path)
                
                # Carrega Excel completo para session_state
                df_complete = pd.read_excel(xlsx_path)
                
                # Armazena dados no session_state
                with open(xlsx_path, "rb") as f:
                    st.session_state.xlsx_data = f.read()
                
                with open(json_path, "rb") as f:
                    st.session_state.json_data = f.read()
                
                st.session_state.df_preview = df_complete.head(100)
                
                # Calcula estatísticas do Excel completo
                total_tours = len(df_complete)
                if "Location Main" in df_complete.columns:
                    total_cities = df_complete["Location Main"].nunique()
                else:
                    total_cities = "N/A"
                
                st.session_state.stats = {
                    "total_tours": total_tours,
                    "total_cities": total_cities
                }
                
                st.session_state.processed = True
                
            except Exception as e:
                progress_bar.empty()
                st.error(f"❌ Erro durante o processamento: {str(e)}")
                
                # Log de erro detalhado para debug
                import traceback
                with st.expander("🔍 Detalhes do Erro"):
                    st.code(traceback.format_exc())
                
                # Tenta limpar arquivo temporário em caso de erro
                try:
                    if 'tmp_path' in locals():
                        os.unlink(tmp_path)
                except:
                    pass
    
    # Exibe resultados se já processado
    if st.session_state.processed:
        st.success("🎉 Extração concluída com sucesso!")
        
        # Estatísticas
        st.header("📊 Estatísticas")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de Tours", st.session_state.stats["total_tours"])
        with col2:
            st.metric("Total de Cidades", st.session_state.stats["total_cities"])
        
        # Tabela com primeiras 100 linhas
        st.header("📋 Primeiras 100 Linhas Extraídas")
        st.dataframe(
            st.session_state.df_preview,
            width='stretch',
            height=400
        )
        
        # Downloads
        st.header("💾 Downloads")
        col1, col2 = st.columns(2)
        
        # Download do Excel Completo
        with col1:
            st.download_button(
                label="📥 Download Excel Completo",
                data=st.session_state.xlsx_data,
                file_name="tours_extracted.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width='stretch'
            )
        
        # Download do JSON Estruturado
        with col2:
            st.download_button(
                label="📥 Download JSON Estruturado",
                data=st.session_state.json_data,
                file_name="tours_extracted.json",
                mime="application/json",
                width='stretch'
            )
    
    elif uploaded_file is None:
        # Instruções quando não há arquivo
        st.info("👆 Faça upload de um arquivo PDF para começar o processamento")
        
        # Exemplo de uso
        with st.expander("📖 Como usar"):
            st.markdown("""
            ### Passo a passo:
            
            1. **Upload**: Selecione um arquivo PDF de catálogo turístico
            2. **Processamento**: Clique em "Processar Catálogo"
            3. **Aguarde**: O sistema irá:
               - Converter PDF para texto
               - Indexar conteúdo semanticamente
               - Extrair informações com IA
               - Gerar arquivos Excel e JSON
            4. **Download**: Baixe os resultados em seus formatos preferidos
            
            ### Formatos de saída:
            
            - **Excel Completo**: Todos os detalhes extraídos (30+ colunas)
            - **JSON Estruturado**: Hierarquia completa para integração técnica
            
            ### Campos extraídos:
            
            - ID, City, Title
            - Location (Main/Region/Zone)
            - Description
            - Duration / Duration Unit
            - Schedule (Departure/Return/Frequency)
            - Meeting Point
            - Includes / Excludes
            - Language Options
            - Min/Max Adults, Min/Max Children
            - Min Booking
            - Non Operating Periods
            - Observations
            - Pricing Type
            - Option Name
            - Capacity
            - Vehicle Options
            - Price / Currency
            - Source Chunks
            """)


if __name__ == "__main__":
    main()

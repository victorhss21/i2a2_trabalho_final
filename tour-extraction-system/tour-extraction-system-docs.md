# Tour Extraction System - Documentação Completa

## Visão Geral

O **Tour Extraction System** é um sistema automatizado de extração de informações de tours turísticos a partir de catálogos em formato PDF. O sistema utiliza inteligência artificial (CrewAI), processamento de linguagem natural e indexação semântica para extrair dados estruturados de documentos não estruturados, gerando saídas em JSON e Excel.

### Principais Características

- **Processamento Multi-idioma**: Suporte a português, inglês, espanhol e francês
- **OCR Integrado**: Extração de texto de PDFs digitalizados usando Docling
- **IA Avançada**: Uso do OpenAI GPT-4o-mini com agentes especializados
- **Indexação Semântica**: FAISS para busca por similaridade
- **Controle de Rate Limiting**: Gerenciamento automático de requisições à API
- **Processamento Paralelo**: Múltiplos workers para otimização de performance
- **Saídas Múltiplas**: JSON bruto, Excel detalhado e Excel refinado

---

## Arquitetura do Sistema

```
Tour Extraction System/
├── src/
│   ├── core/                    # Componentes centrais
│   │   ├── config.py           # Gerenciamento de configurações
│   │   └── logger.py           # Sistema de logging
│   ├── processors/             # Processadores principais
│   │   ├── pdf_chunker.py      # Conversão PDF → Markdown
│   │   ├── semantic_indexer.py # Indexação FAISS
│   │   ├── tour_extractor.py   # Extração com IA
│   │   ├── result_exporter.py  # Exportação JSON/Excel
│   │   └── result_refiner.py   # Refinamento final
│   ├── utils/                  # Utilitários
│   │   └── rate_limiter.py     # Controle de requisições
│   ├── schemas.py              # Esquemas de dados
│   └── pipeline.py             # Orquestrador principal
├── config/
│   └── settings.yaml           # Configurações do sistema
└── main.py                     # Ponto de entrada
```

---

## Configuração Inicial

### 1. Requisitos e Dependências

```bash
pip install -r requirements.txt
```

**Dependências principais:**
- `crewai`: Framework de agentes IA
- `docling`: Conversão PDF para markdown
- `sentence-transformers`: Embeddings semânticos
- `faiss-cpu`: Indexação vetorial
- `pandas`: Manipulação de dados
- `openpyxl`: Exportação Excel

### 2. Variáveis de Ambiente

Crie um arquivo `.env`:

```env
OPENAI_API_KEY=sua_chave_api_openai
```

### 3. Estrutura de Diretórios

```
output/
├── chunks/          # Chunks markdown intermediários
├── index/           # Índices FAISS e embeddings
└── results/         # Arquivos finais de saída
```

---

## Configurações do Sistema

O arquivo `config/settings.yaml` controla todos os parâmetros:

```yaml
# Configurações do Sistema de Extração de Tours
system:
  name: "Tour Extraction System"
  version: "3.0.0"

# Diretórios
directories:
  uploads: "uploads"
  chunks: "output/chunks"
  index: "output/index"
  results: "output/results"

# Processamento de PDF
pdf_processing:
  enable_ocr: true
  pages_per_chunk: 1  # 1 página = 1 chunk

# Indexação Semântica
indexing:
  model: "sentence-transformers/all-MiniLM-L6-v2"
  normalize_embeddings: true

# Extração com LLM
extraction:
  llm_model: "openai/gpt-4o-mini"
  temperature: 0.0
  max_workers: 5
  rate_limit_per_minute: 50
  max_context_chars: 15000

# Exportação
export:
  formats:
    json: true
    excel: true
  excel_max_description_length: 200
  export_refined: true  # Ativa arquivo refinado

# Logging
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
```

---

## Como Executar o Sistema

### Comando Básico

```bash
python main.py --pdf "caminho/para/catalogo.pdf"
```

### Com Configuração Personalizada

```bash
python main.py --pdf "catalogo.pdf" --config "config/custom_settings.yaml"
```

---

## Fluxo de Execução Detalhado

O sistema executa **4 etapas principais** em sequência:

### **Etapa 1: Chunking de PDF** 📄
**Arquivo:** `pdf_chunker.py`

**Função:** Converte cada página do PDF em um chunk de texto markdown.

**Processo:**
1. **Inicialização**: Configura conversor Docling com opções de OCR
2. **Divisão**: Separa PDF página por página usando PyPDF2
3. **Conversão**: Para cada página:
   - Cria PDF temporário com uma única página
   - Aplica OCR (se habilitado)
   - Converte para markdown usando Docling
   - Salva como arquivo `.md` numerado
4. **Limpeza**: Remove arquivos temporários e libera memória

**Saídas:**
- `output/chunks/page_001.md`
- `output/chunks/page_002.md`
- ... (uma por página)

**Configurações relevantes:**
- `enable_ocr`: Ativa/desativa OCR
- `pages_per_chunk`: Páginas por chunk (padrão: 1)

---

### **Etapa 2: Indexação Semântica** 🔍
**Arquivo:** `semantic_indexer.py`

**Função:** Cria índice FAISS para busca por similaridade semântica.

**Processo:**
1. **Carregamento**: Lê todos os chunks markdown
2. **Embeddings**: Gera vetores usando sentence-transformers
3. **Indexação**: Cria índice FAISS com cosine similarity
4. **Persistência**: Salva índice, embeddings e mapeamento de arquivos

**Saídas:**
- `output/index/chunks.faiss` (índice FAISS)
- `output/index/embeddings.npy` (vetores)
- `output/index/files.json` (mapeamento)

**Funcionalidade de Busca:**
```python
similar_chunks = indexer.search_similar_chunks(text, top_k=3)
```

**Configurações relevantes:**
- `model`: Modelo de embedding
- `normalize_embeddings`: Normalização de vetores

---

### **Etapa 3: Extração de Tours** 🤖
**Arquivo:** `tour_extractor.py`

**Função:** Usa CrewAI com GPT-4o-mini para extrair informações estruturadas.

**Processo:**
1. **Configuração do Agente**:
   ```python
   agent = Agent(
       role="Extrator Universal Multi-Idioma de Tours",
       goal="Extrair informações completas de tours/tarifários",
       backstory="Especialista em catálogos turísticos globais"
   )
   ```

2. **Processamento Paralelo**:
   - Divide chunks entre múltiplos workers
   - Aplica rate limiting (50 req/min padrão)
   - Para cada chunk:
     - Busca chunks similares para contexto adicional
     - Envia prompt estruturado para IA
     - Processa resposta JSON

3. **Prompt Multi-formato**:
   - Detecta idioma automaticamente
   - Suporte a formatos europeus e latino-americanos
   - Extrai 20+ campos por tour
   - Valida estrutura JSON de saída

**Schema de Extração:**
```json
{
  "agency": "Nome da Agência",
  "product": {
    "type": "Private Tour",
    "destination": "France"
  },
  "tours": [{
    "id": "1",
    "city": "Paris",
    "title": "Sightseeing tour",
    "location": {
      "main": "Paris",
      "region": "Ile-de-France",
      "zone": null
    },
    "duration": {
      "quantity": 4,
      "unit": "hours"
    },
    "description": "Complete description...",
    "pricing_type": "per_vehicle",
    "options": [{
      "name_option": "Car/Van with driver",
      "details": [{
        "capacity": "01-03 pax",
        "vehicle_options": "car",
        "price": {
          "quantity": 625,
          "currency": "EUR"
        }
      }]
    }],
    "schedule": {
      "departure_time": "08:30",
      "return_time": null,
      "frequency": "Daily"
    },
    "meeting_point": "Hotel lobby",
    "includes": ["Guide", "Transport"],
    "excludes": ["Meals", "Tips"],
    "language_options": ["english", "french"],
    "operation": {
      "non_operating_periods": ["01 May", "Sundays"]
    },
    "min_booking": 2,
    "observations": "All observations...",
    "source_chunks": ["page_001.md"]
  }]
}
```

**Configurações relevantes:**
- `llm_model`: Modelo de IA
- `temperature`: Criatividade (0.0 = determinístico)
- `max_workers`: Workers paralelos
- `rate_limit_per_minute`: Limite de requisições
- `max_context_chars`: Caracteres máximos por prompt

---

### **Etapa 4: Exportação e Refinamento** 📊
**Arquivos:** `result_exporter.py` e `result_refiner.py`

#### **4.1 Exportação Bruta (`result_exporter.py`)**

**Função:** Converte JSON estruturado em formatos de saída.

**Processo JSON:**
- Salva JSON completo com toda estrutura
- Preserva hierarquia original
- Arquivo: `tours_extracted.json`

**Processo Excel Bruto:**
- **Normalização**: Expande estruturas aninhadas
- **Multi-formato**: 
  - Formato europeu: Uma linha por opção de veículo
  - Formato latino: Uma linha por matriz de preços
- **Colunas (30+)**: ID, City, Title, Location Main/Region/Zone, Description, Duration, Schedule, Pricing, Options, etc.
- Arquivo: `tours_extracted.xlsx`

#### **4.2 Refinamento Final (`result_refiner.py`)**

**Função:** Cria versão limpa apenas com campos essenciais.

**Processo:**
1. **Seleção**: Filtra apenas 9 campos essenciais
2. **Otimização de Preços**: 
   - Varre todas as opções disponíveis
   - Seleciona **menor preço** encontrado
   - Mantém moeda correspondente
3. **Deduplicação**: Remove duplicatas por Title + Location
4. **Formatação**: Renomeia colunas para legibilidade

**Campos do Excel Refinado:**
- Title
- Location Main  
- Description
- Duration
- Duration Unit
- Min Adults
- Observations  
- Price (menor preço encontrado)
- Currency

**Arquivo:** `tours_extracted_refined.xlsx`

**Configurações relevantes:**
- `export.json`: Ativa/desativa JSON
- `export.excel`: Ativa/desativa Excel bruto
- `export_refined`: Ativa/desativa Excel refinado
- `excel_max_description_length`: Limite de caracteres

---

## Componentes de Apoio

### **Gerenciamento de Configuração** ⚙️
**Arquivo:** `config.py`

- Carrega configurações do YAML
- Valida parâmetros obrigatórios
- Classe `SystemConfig` centraliza acesso

### **Sistema de Logging** 📝
**Arquivo:** `logger.py`

- Logs estruturados com níveis (DEBUG, INFO, WARNING, ERROR)
- Saída no console com timestamps
- Rastreamento de progresso por etapa

### **Rate Limiting** ⏱️
**Arquivo:** `rate_limiter.py`

- Controla requisições para OpenAI API
- Implementa sliding window
- Previne erros por quota exceeded

### **Pipeline Principal** 🔄
**Arquivo:** `pipeline.py`

- Orquestra execução sequencial
- Gerencia dependências entre etapas
- Logs de progresso e estatísticas finais
- Tratamento de erros por etapa

---

## Estrutura de Saídas

Após execução completa, o sistema gera:

```
output/results/
├── tours_extracted.json          # JSON estruturado completo
├── tours_extracted.xlsx          # Excel com todos os detalhes
└── tours_extracted_refined.xlsx  # Excel com campos essenciais
```

### **Comparação dos Formatos de Saída:**

| Característica | JSON | Excel Bruto | Excel Refinado |
|---|---|---|---|
| **Público-alvo** | Desenvolvedores | Analistas | Usuário final |
| **Estrutura** | Hierárquica completa | Tabular expandida | Tabular essencial |
| **Campos** | Todos (~25) | Todos (~30 colunas) | Apenas 9 |
| **Duplicatas** | Preservadas | Por opção/preço | Removidas |
| **Formato preços** | Por opção | Separado por linha | Menor preço |

---

## Personalização e Extensão

### **Modificar Campos Extraídos**
Edite o prompt no `tour_extractor.py`:

```python
# Adicione novos campos ao schema JSON
"novo_campo": "valor_extraído",
```

### **Ajustar Modelo de IA**
Altere no `settings.yaml`:

```yaml
extraction:
  llm_model: "openai/gpt-4"  # ou outros modelos
  temperature: 0.1           # mais criatividade
```

### **Modificar Campos do Excel Refinado**
Edite `column_order` no `result_refiner.py`:

```python
column_order = [
    "Title",
    "Location_Main", 
    "Description",
    "Novo_Campo",  # Adicionar aqui
    # ...
]
```

---

## Solução de Problemas

### **Erro: OpenAI API Key**
```bash
OPENAI_API_KEY não configurada no arquivo .env
```
**Solução:** Configure a variável de ambiente no `.env`

### **Erro: PDF não encontrado**
```bash
[ERRO] PDF não encontrado: arquivo.pdf
```
**Solução:** Verifique o caminho do arquivo PDF

### **Erro: Rate Limit**
```bash
Rate limit exceeded
```
**Solução:** Reduza `rate_limit_per_minute` no `settings.yaml`

### **Erro: Memória insuficiente**
```bash
Out of memory
```
**Solução:** Reduza `max_workers` ou processe PDFs menores

### **Excel refinado vazio**
**Possíveis causas:**
- `export_refined: false` no YAML
- JSON de entrada mal formatado
- Erro de permissão no diretório

---

## Limitações e Considerações

### **Limitações Técnicas**
- **Dependência de API externa**: Requer conectividade e créditos OpenAI
- **Processamento sequencial de etapas**: Não paraleliza etapas principais
- **Memória**: PDFs grandes podem consumir muita RAM
- **Idiomas**: Otimizado para português, inglês, espanhol e francês

### **Limitações de Dados**
- **Formato de entrada**: Apenas PDF
- **Estrutura esperada**: Catálogos de turismo estruturados
- **Qualidade OCR**: Dependente da qualidade do PDF original

### **Considerações de Uso**
- **Custos API**: Requisições para OpenAI geram custos
- **Tempo de processamento**: PDFs grandes podem levar vários minutos
- **Precisão**: IA pode cometer erros em documentos mal estruturados

---

## Monitoramento e Logs

O sistema gera logs detalhados de cada etapa:

```
[INFO] TOUR EXTRACTION PIPELINE
[INFO] PDF: catalogo.pdf
[INFO] [1/4] Chunking de PDF  
[INFO] PDF Chunker configurado (OCR: True)
[INFO] Processando 45 páginas...
[INFO] Chunking concluído: 45 páginas processadas
[INFO] [2/4] Indexação Semântica
[INFO] Modelo carregado: sentence-transformers/all-MiniLM-L6-v2
[INFO] Carregados 45 chunks
[INFO] Gerando embeddings...
[INFO] Índice criado: 45 chunks indexados
[INFO] [3/4] Extração de Tours
[INFO] Agente configurado (modelo: openai/gpt-4o-mini)
[INFO] Processando 45 chunks com 5 workers
[INFO] Extração concluída: 23 tours extraídos
[INFO] [4/4] Exportação e Refinamento
[INFO] JSON salvo: output/results/tours_extracted.json
[INFO] Excel salvo: output/results/tours_extracted.xlsx
[INFO] ✅ Excel refinado salvo em: output/results/tours_extracted_refined.xlsx
[INFO] 📊 Total de experiências únicas: 18
[INFO] ✅ PIPELINE CONCLUÍDO COM SUCESSO!
```

---

## Roadmap Futuro

### **Planejado**
- Interface web com Flask/FastAPI
- Suporte a múltiplos formatos (Word, HTML)
- Cache inteligente de embeddings
- Dashboard de monitoramento
- API REST para integração

### **Em Consideração**
- Modelos de IA locais (Ollama)
- Processamento batch de múltiplos PDFs
- Validação automática de dados extraídos
- Exportação para outros formatos (CSV, XML)

---

## Conclusão

O Tour Extraction System oferece uma solução completa e automatizada para extração de informações de catálogos turísticos. Com sua arquitetura modular, configuração flexível e uso de IA avançada, o sistema pode processar documentos complexos e gerar saídas estruturadas de alta qualidade.

Para suporte técnico ou dúvidas sobre implementação, consulte os logs do sistema e esta documentação. O código é totalmente modular, permitindo personalizações e extensões conforme necessário.
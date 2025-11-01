"""
Extrai tours usando CrewAI em paralelo com controle de rate limit.
"""
import os
import json
import concurrent.futures
from typing import Dict, Any, List

from crewai import Agent, Task, Crew, LLM

from ..core.config import SystemConfig
from ..core.logger import Logger
from ..utils.rate_limiter import RateLimiter


class TourExtractor:
    """Extrator de tours usando CrewAI"""
    
    def __init__(self, config: SystemConfig, logger: Logger, indexer=None):
        self.config = config
        self.logger = logger
        self.agent = None
        self.md_files = []
        self.texts = []
        self.ratelimiter = RateLimiter(config.rate_limit)
        self.indexer = indexer     # Novo: injete o indexador para Expand Recall
    
    def setup(self):
        """Inicializa agente CrewAI"""
        # Valida API key
        if not os.environ.get("OPENAI_API_KEY", "").strip():
            raise ValueError("OPENAI_API_KEY não configurada no arquivo .env")
        
        # Carrega chunks
        with open(os.path.join(self.config.index_dir, "files.json"), "r") as f:
            self.md_files = json.load(f)
        
        for path in self.md_files:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.texts.append(f.read().strip())
            except Exception:
                self.texts.append("")
        
        # Cria agente
        llm = LLM(model=self.config.llm_model, temperature=self.config.temperature)
        
        self.agent = Agent(
            role="Extrator Universal Multi-Idioma de Tours",
            goal="Extrair informações completas de tours/tarifários em qualquer idioma e formato",
            backstory="Especialista em extrair dados precisos de catálogos turísticos europeus, latino-americanos e globais",
            llm=llm,
            verbose=False
        )
        
        self.logger.info(f"Agente configurado (modelo: {self.config.llm_model})")
    
    def process_chunk(self, idx: int) -> Dict[str, Any]:
        self.ratelimiter.wait()
        chunk_filename = os.path.basename(self.md_files[idx])

        # Chunk alvo/texto
        target_text = self.texts[idx][:self.config.max_context_chars]
        # (NOVO) Pegue outros chunks mais similares usando indexador!
        similar_contexts = []
        if self.indexer is not None:
            similar = self.indexer.search_similar_chunks(target_text, top_k=3)
            # Exclua duplicação do próprio chunk idx!
            similar = [c for c in similar if c['idx'] != idx]
            for c in similar:
                similar_contexts.append(c['text'][:self.config.max_context_chars])
        # Concatenar target + similares
        context = target_text + "\n\n" + "\n\n".join(similar_contexts)
        
        # Prompt ROBUSTO MULTI-FORMATO E MULTI-IDIOMA
        prompt = f"""
Extraia TODAS as informações de tours/excursões/traslados do texto com MÁXIMA PRECISÃO, INDEPENDENTE do idioma (inglês, português, espanhol, francês) ou formato (tabelas, parágrafos, listas).

-----------------------------------------------------------------------------
REGRAS CRÍTICAS DE EXTRAÇÃO:
-----------------------------------------------------------------------------

1. **IDIOMA:** Detecte automaticamente (inglês/português/espanhol/francês). Extraia em qualquer idioma.

2. **CIDADE e TÍTULO:** 
   - city: apenas a cidade (ex: "Paris", "San Andrés", "Colmar")
   - title: nome do tour SEM a cidade (ex: "French wine tasting", NÃO "Paris French wine tasting")

3. **DESCRIÇÃO:** Texto COMPLETO e detalhado (mínimo 80 caracteres). Inclua roteiro, diferenciais, pontos visitados.

4. **DURAÇÃO:** Objeto {{"quantity": 3.5, "unit": "hours"}} ou {{"quantity": 8, "unit": "hours"}}

5. **LOCALIZAÇÃO:**
   - main: cidade principal
   - region: região/estado (se mencionado)
   - zone: "Zona 1"/"Zona 2"/"Zona 3" (se houver sistema de zonas)

6. **PREÇOS - DOIS FORMATOS SUPORTADOS:**

   📌 **FORMATO A - POR VEÍCULO (Europeu):**
   - pricing_type: "per_vehicle"
   - options: [
       {{
         "name_option": "Car/Van with english speaking driver. Price per car/van",
         "details": [
           {{"capacity": "01-03 pax", "vehicle_options": "car", "price": {{"quantity": 625, "currency": "EUR"}}}},
           {{"capacity": "04-06 pax", "vehicle_options": "van", "price": {{"quantity": 625, "currency": "EUR"}}}}
         ]
       }},
       {{
         "name_option": "Entrance ticket. Price per pax",
         "details": [{{"capacity": "all", "vehicle_options": null, "price": {{"quantity": 13, "currency": "EUR"}}}}]
       }}
     ]

   📌 **FORMATO B - POR PESSOA/TABELA MATRICIAL (Latino-americano):**
   - pricing_type: "per_person"
   - pricing_matrix: [
       {{"pax_count": 1, "price": 21, "currency": "USD"}},
       ...
     ]

7. **HORÁRIOS E FREQUÊNCIA:**
   - schedule: {{
       "departure_time": "05:30" ou "08:30",
       "return_time": "17:00",
       "frequency": "Diário" ou "Segunda a Sexta"
     }}

8. **PONTO DE ENCONTRO:**
   - meeting_point: "Hotel lobby" ou "Aeroporto" ou "Pier 5"

9. **ITENS INCLUSOS/EXCLUÍDOS:**
   - includes: ["Guia em espanhol", "Transporte", "Almoço"]
   - excludes: ["Bebidas alcoólicas", "Gorjetas"]

10. **IDIOMAS DISPONÍVEIS:**
    - language_options: ["espanhol", "inglês", "português", "francês"]

11. **OPERAÇÃO:**
    - operation: {{
        "non_operating_periods": ["01 May", "08 Jan to 09 Feb", "Domingos"]
      }}

12. **OBSERVAÇÕES (TODAS!):**
    - observations: Agrupe TODAS as observações, restrições, notas, políticas de child, quantidade mínima para reserva, horários de reunião, fechamentos, suplementos, etc.
    - Exemplo: "Eiffel Tower closed: 01 May. Top floor closed: 08 Jan to 09 Feb. Only for good walkers. Minimum 2 pax to confirm."

13. **MIN_BOOKING:** Quantidade mínima de pessoas para confirmar reserva (ex: 2)

14. **SOURCE_CHUNKS:** ["{chunk_filename}"]

-----------------------------------------------------------------------------
SCHEMA OBRIGATÓRIO (adapte ao formato encontrado):
-----------------------------------------------------------------------------

{{
  "agency": "Nome da Agência",
  "product": {{
    "type": "Private Tour" ou "Shared Tour" ou "Transfer",
    "general_conditions": "Condições gerais do catálogo...",
    "year": 2024,
    "destination": ["France"] ou ["Colombia"]
  }},
  "tours": [
    {{
      "id": "TOUR_ID_UNICO_NUMERICO",
      "city": "Paris",
      "title": "French wine tasting",
      "location": {{"main": "Paris", "region": "Ile-de-France", "zone": null}},
      "duration": {{"quantity": 1.5, "unit": "hours"}},
      "description": "Complete description...",
      
      "pricing_type": "per_vehicle",  // ou "per_person"
      "options": [...],  // Se per_vehicle
      "pricing_matrix": [...],  // Se per_person
      
      "schedule": {{
        "departure_time": "08:30",
        "return_time": null,
        "frequency": "Diário"
      }},
      "meeting_point": "Hotel lobby",
      "includes": ["Guia", "Transporte", "Entrada"],
      "excludes": ["Refeições", "Gorjetas"],
      "language_options": ["espanhol", "inglês"],
      
      "operation": {{
        "non_operating_periods": ["01 May", "Domingos"]
      }},
      "min_adults": 1,
      "max_adults": 6,
      "max_childrens": null,
      "min_booking": 2,
      "observations": "Todas observações agregadas aqui...",
      "source_chunks": ["{chunk_filename}"]
    }}
  ]
}}

-----------------------------------------------------------------------------
TEXTO PARA ANÁLISE:
-----------------------------------------------------------------------------

{context}

-----------------------------------------------------------------------------
ATENÇÃO FINAL:
- Se NÃO houver informação, use null ou []
- NUNCA invente dados
- Adapte o formato ao que encontrar (per_vehicle OU per_person)
- SEMPRE extraia observations COMPLETAS
-----------------------------------------------------------------------------

RETORNE APENAS O JSON ESTRUTURADO ACIMA!
"""
        
        task = Task(
            description=prompt,
            agent=self.agent,
            expected_output="JSON com tours extraídos completos seguindo schema multi-formato"
        )
        
        crew = Crew(agents=[self.agent], tasks=[task], process="sequential", verbose=False)
        
        try:
            result = crew.kickoff()
            
            # Extrai JSON
            if hasattr(result, 'json_dict') and result.json_dict:
                return result.json_dict
            elif hasattr(result, 'pydantic') and result.pydantic:
                return result.pydantic.dict()
            else:
                content = str(result).strip()
                first, last = content.find('{'), content.rfind('}')
                if first != -1 and last != -1:
                    return json.loads(content[first:last+1])
                return {"agency": None, "product": None, "tours": []}
        except Exception as e:
            self.logger.error(f"Erro chunk {idx+1}: {e}")
            return {"agency": None, "product": None, "tours": []}
    
    def extract(self) -> Dict[str, Any]:
        """Extrai tours em paralelo"""
        self.logger.info(f"Processando {len(self.texts)} chunks com {self.config.max_workers} workers")
        
        agency = None
        product = None
        all_tours = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = {executor.submit(self.process_chunk, i): i for i in range(len(self.texts))}
            
            for future in concurrent.futures.as_completed(futures):
                data = future.result()
                
                if not agency and data.get("agency"):
                    agency = data["agency"]
                if not product and data.get("product"):
                    product = data["product"]
                
                for tour in data.get("tours", []):
                    if isinstance(tour, dict) and tour.get("title"):
                        all_tours.append(tour)
        
        self.logger.info(f"Extração concluída: {len(all_tours)} tours extraídos")
        
        return {
            "agency": agency or "Travel Agency",
            "product": product or {
                "type": "Tours",
                "general_conditions": None,
                "year": 2024,
                "destination": []
            },
            "tours": all_tours
        }

# import os
# import json
# import pandas as pd
# from typing import List, Dict, Any

# class ResultRefiner:
#     """
#     Refina os resultados brutos para formato final pronto para exibição.
#     Remove duplicatas e seleciona apenas campos essenciais.
#     """

#     def __init__(self, config, logger):
#         self.config = config
#         self.logger = logger

#     def refine(self, raw_json_path: str) -> str:
#         """
#         Refina o JSON bruto e gera Excel limpo para usuário final.
#         Args:
#             raw_json_path: Caminho do tours_extracted.json
#         Returns:
#             Caminho do arquivo Excel refinado gerado
#         """
#         self.logger.info("Iniciando refinamento dos resultados...")

#         with open(raw_json_path, "r", encoding="utf-8") as f:
#             raw_data = json.load(f)

#         # Suporta tanto lista de tours quanto dicionário com chave 'tours'
#         if isinstance(raw_data, dict) and "tours" in raw_data:
#             tours = raw_data["tours"]
#         elif isinstance(raw_data, list):
#             tours = raw_data
#         else:
#             raise ValueError("Formato de entrada inválido: esperado lista ou dict com chave 'tours'.")

#         # Extrai e limpa registros
#         refined_records = self._extract_refined_records(tours)
#         # Remove duplicatas
#         unique_records = self._remove_duplicates(refined_records)
#         # Formata e exporta para excel
#         output_path = os.path.join(self.config.results_dir, "tours_extracted_refined.xlsx")
#         os.makedirs(self.config.results_dir, exist_ok=True)
#         df = pd.DataFrame(unique_records)
#         column_order = [
#             "Title",
#             "Location_Main",
#             "Description",
#             "Duration",
#             "Duration_Unit",
#             "Min_Adults",
#             "Observations",
#             "Price",
#             "Currency"
#         ]
#         df = df[column_order]
#         df.to_excel(output_path, index=False)
#         self.logger.info(f"Excel refinado salvo em: {output_path}")
#         return output_path

#     def _extract_refined_records(self, tours: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#         """
#         Extrai os campos essenciais de cada tour.
#         """
#         refined = []
#         for tour in tours:
#             # Adaptação para possíveis variações dos nomes de campos
#             title = tour.get("title")
#             location = tour.get("location", {})
#             location_main = location.get("main") if isinstance(location, dict) else tour.get("location_main", "")
#             description = tour.get("description")
#             duration_info = tour.get("duration", {})
#             duration = duration_info.get("quantity") if isinstance(duration_info, dict) else tour.get("duration")
#             duration_unit = duration_info.get("unit") if isinstance(duration_info, dict) else tour.get("duration_unit")
#             min_adults = tour.get("min_booking") or tour.get("min_adults")
#             observations = tour.get("observations", "")
#             # Extrai preço e moeda do primeiro option/details (personalize para seu schema)
#             price = None
#             currency = None
#             if "options" in tour and isinstance(tour["options"], list) and len(tour["options"]) > 0:
#                 # Tenta pegar do primeiro details do primeiro option
#                 option = tour["options"][0]
#                 details = option.get("details", [])
#                 if details and isinstance(details[0], dict):
#                     price_info = details[0].get("price", {})
#                     price = price_info.get("quantity")
#                     currency = price_info.get("currency")
#             if price is None:
#                 price = ""
#             if currency is None:
#                 currency = ""
#             refined.append({
#                 "Title": title,
#                 "Location_Main": location_main,
#                 "Description": description,
#                 "Duration": duration,
#                 "Duration_Unit": duration_unit,
#                 "Min_Adults": min_adults,
#                 "Observations": observations,
#                 "Price": price,
#                 "Currency": currency
#             })
#         return refined

#     def _remove_duplicates(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#         """
#         Remove duplicatas considerando Title e Location_Main.
#         """
#         seen = set()
#         unique = []
#         for rec in records:
#             key = (str(rec.get("Title")).strip().lower(), str(rec.get("Location_Main")).strip().lower())
#             if key not in seen and key != ("", ""):
#                 seen.add(key)
#                 unique.append(rec)
#         return unique

import os
import json
import pandas as pd
from typing import List, Dict, Any

class ResultRefiner:
    """
    Refina os resultados brutos para formato final pronto para exibição.
    Remove duplicatas e seleciona apenas campos essenciais, buscando o menor preço dentre todas as opções disponíveis.
    """

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def refine(self, raw_json_path: str) -> str:
        """
        Refina o JSON bruto e gera Excel limpo para usuário final.
        Args:
            raw_json_path: Caminho do tours_extracted.json
        Returns:
            Caminho do arquivo Excel refinado gerado
        """
        self.logger.info("Iniciando refinamento dos resultados...")

        with open(raw_json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        # Suporta tanto lista de tours quanto dicionário com chave 'tours'
        if isinstance(raw_data, dict) and "tours" in raw_data:
            tours = raw_data["tours"]
        elif isinstance(raw_data, list):
            tours = raw_data
        else:
            raise ValueError("Formato de entrada inválido: esperado lista ou dict com chave 'tours'.")

        # Extrai e limpa registros
        refined_records = self._extract_refined_records(tours)
        # Remove duplicatas
        unique_records = self._remove_duplicates(refined_records)
        # Formata e exporta para Excel
        output_path = os.path.join(self.config.results_dir, "tours_extracted_refined.xlsx")
        os.makedirs(self.config.results_dir, exist_ok=True)
        df = pd.DataFrame(unique_records)
        column_order = [
            "Title",
            "Location_Main",
            "Description",
            "Duration",
            "Duration_Unit",
            "Min_Adults",
            "Observations",
            "Price",
            "Currency"
        ]
        df = df[column_order]
        df.to_excel(output_path, index=False)
        self.logger.info(f"Excel refinado salvo em: {output_path}")
        return output_path

    def _extract_refined_records(self, tours: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extrai os campos essenciais de cada tour, buscando o menor preço disponível em todas as opções.
        """
        refined = []
        for tour in tours:
            title = tour.get("title")
            location = tour.get("location", {})
            location_main = location.get("main") if isinstance(location, dict) else tour.get("location_main", "")
            description = tour.get("description")
            duration_info = tour.get("duration", {})
            duration = duration_info.get("quantity") if isinstance(duration_info, dict) else tour.get("duration")
            duration_unit = duration_info.get("unit") if isinstance(duration_info, dict) else tour.get("duration_unit")
            min_adults = tour.get("min_booking") or tour.get("min_adults")
            observations = tour.get("observations", "")

            # Agora busca o menor preço e a moeda correspondente em todas as opções/detalhes
            min_price = None
            min_currency = None
            if "options" in tour and isinstance(tour["options"], list):
                for option in tour["options"]:
                    details = option.get("details", [])
                    for d in details:
                        price_info = d.get("price", {})
                        price = price_info.get("quantity")
                        curr = price_info.get("currency")
                        # Salva preço/min_price se: é o primeiro OU menor valor encontrado
                        if price is not None and (min_price is None or price < min_price):
                            min_price = price
                            min_currency = curr

            price = min_price if min_price is not None else ""
            currency = min_currency if min_currency is not None else ""

            refined.append({
                "Title": title,
                "Location_Main": location_main,
                "Description": description,
                "Duration": duration,
                "Duration_Unit": duration_unit,
                "Min_Adults": min_adults,
                "Observations": observations,
                "Price": price,
                "Currency": currency
            })
        return refined

    def _remove_duplicates(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicatas considerando Title e Location_Main.
        """
        seen = set()
        unique = []
        for rec in records:
            key = (str(rec.get("Title")).strip().lower(), str(rec.get("Location_Main")).strip().lower())
            if key not in seen and key != ("", ""):
                seen.add(key)
                unique.append(rec)
        return unique

"""
Exporta resultados em JSON e Excel.
"""

import os
import json
import time
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from ..core.config import SystemConfig
from ..core.logger import Logger

class ResultExporter:
    """Exportador de resultados"""
    
    def __init__(self, config: SystemConfig, logger: Logger):
        self.config = config
        self.logger = logger
    
    def export(self, catalog: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """Exporta para JSON e/ou Excel"""
        os.makedirs(self.config.results_dir, exist_ok=True)
        
        json_path = None
        xlsx_path = None
        
        if self.config.export_json:
            json_path = self._export_json(catalog)
        
        if self.config.export_excel:
            xlsx_path = self._export_excel(catalog)
        
        return json_path, xlsx_path
    
    def _export_json(self, catalog: Dict[str, Any]) -> str:
        """Exporta para JSON"""
        json_path = os.path.join(self.config.results_dir, "tours_extracted.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)
        self.logger.info(f"JSON salvo: {json_path}")
        return json_path
    
    def _export_excel(self, catalog: Dict[str, Any]) -> str:
        """Exporta para Excel com formato completo multi-formato"""
        rows = []
        
        for tour in catalog.get("tours", []):
            # Descrição completa
            desc = tour.get("description", "")
            
            # Duration
            duration_obj = tour.get("duration", {})
            duration_val = duration_obj.get("quantity", "") if isinstance(duration_obj, dict) else ""
            duration_unit = duration_obj.get("unit", "") if isinstance(duration_obj, dict) else ""
            
            # Location
            location_obj = tour.get("location", {})
            location_main = location_obj.get("main", "") if isinstance(location_obj, dict) else ""
            location_region = location_obj.get("region", "") if isinstance(location_obj, dict) else ""
            location_zone = location_obj.get("zone", "") if isinstance(location_obj, dict) else ""
            
            # Schedule
            schedule_obj = tour.get("schedule", {})
            departure_time = schedule_obj.get("departure_time", "") if isinstance(schedule_obj, dict) else ""
            return_time = schedule_obj.get("return_time", "") if isinstance(schedule_obj, dict) else ""
            frequency = schedule_obj.get("frequency", "") if isinstance(schedule_obj, dict) else ""
            
            # Includes/Excludes
            includes = tour.get("includes", [])
            includes_str = "; ".join(includes) if includes else ""
            excludes = tour.get("excludes", [])
            excludes_str = "; ".join(excludes) if excludes else ""
            
            # Language options
            lang_opts = tour.get("language_options", [])
            lang_opts_str = "; ".join(lang_opts) if lang_opts else ""
            
            # Source chunks
            source_chunks = tour.get("source_chunks", [])
            source_chunks_str = "; ".join(source_chunks) if source_chunks else ""
            
            # Operation
            operation_obj = tour.get("operation", {})
            non_operating = operation_obj.get("non_operating_periods", []) if isinstance(operation_obj, dict) else []
            non_operating_str = "; ".join([str(p) for p in non_operating]) if non_operating else ""
            
            # Base row com todos os campos
            base_row = {
                # "ID": tour.get("id", ""),
                "City": tour.get("city", ""),
                "Title": tour.get("title", ""),
                "Location Main": location_main,
                "Location Region": location_region,
                "Location Zone": location_zone,
                "Description": desc,
                "Duration": duration_val,
                "Duration Unit": duration_unit,
                "Departure Time": departure_time,
                "Return Time": return_time,
                "Frequency": frequency,
                "Meeting Point": tour.get("meeting_point", ""),
                "Includes": includes_str,
                "Excludes": excludes_str,
                "Language Options": lang_opts_str,
                "Min Adults": tour.get("min_adults", ""),
                "Max Adults": tour.get("max_adults", ""),
                "Max Children": tour.get("max_childrens", ""),
                "Min Booking": tour.get("min_booking", ""),
                "Non Operating Periods": non_operating_str,
                "Observations": tour.get("observations", ""),
                "Source Chunks": source_chunks_str,
                "Pricing Type": tour.get("pricing_type", "")
            }
            
            # Detecta formato de preços
            pricing_type = tour.get("pricing_type", "")
            
            if pricing_type == "per_vehicle":
                # Formato europeu (options)
                options = tour.get("options", [])
                if options:
                    for opt in options:
                        opt_name = opt.get("name_option", "")
                        opt_details = opt.get("details", [])
                        
                        if opt_details:
                            for detail in opt_details:
                                row = base_row.copy()
                                row["Option Name"] = opt_name
                                row["Capacity"] = detail.get("capacity", "")
                                row["Vehicle Options"] = detail.get("vehicle_options", "")
                                
                                price_obj = detail.get("price", {})
                                if isinstance(price_obj, dict):
                                    row["Price"] = price_obj.get("quantity", "")
                                    row["Currency"] = price_obj.get("currency", "")
                                else:
                                    row["Price"] = ""
                                    row["Currency"] = ""
                                
                                rows.append(row)
                        else:
                            row = base_row.copy()
                            row["Option Name"] = opt_name
                            row["Capacity"] = ""
                            row["Vehicle Options"] = ""
                            row["Price"] = ""
                            row["Currency"] = ""
                            rows.append(row)
                else:
                    rows.append(base_row)
                    
            elif pricing_type == "per_person":
                # Formato latino-americano (pricing_matrix)
                pricing_matrix = tour.get("pricing_matrix", [])
                
                if pricing_matrix:
                    for pax_pricing in pricing_matrix:
                        row = base_row.copy()
                        row["Pax Count"] = pax_pricing.get("pax_count", "")
                        row["Price"] = pax_pricing.get("price", "")
                        row["Currency"] = pax_pricing.get("currency", "")
                        rows.append(row)
                else:
                    rows.append(base_row)
            else:
                # Sem informação de preços
                rows.append(base_row)
        
        if rows:
            df = pd.DataFrame(rows)
            excel_path = os.path.join(self.config.results_dir, "tours_extracted.xlsx")
            
            try:
                df.to_excel(excel_path, index=False, engine='openpyxl')
                self.logger.info(f"Excel salvo: {excel_path}")
                return excel_path
            except PermissionError:
                alt_path = os.path.join(self.config.results_dir, f"tours_{int(time.time())}.xlsx")
                df.to_excel(alt_path, index=False, engine='openpyxl')
                self.logger.info(f"Excel salvo: {alt_path}")
                return alt_path
        
        return None

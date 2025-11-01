"""
Schemas Pydantic para validação de dados extraídos.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class PriceDetail(BaseModel):
    """Detalhe de preço"""
    quantity: Optional[float] = None
    currency: Optional[str] = None


class OptionDetail(BaseModel):
    """Detalhe de uma opção"""
    capacity: Optional[str] = None
    vehicle_options: Optional[str] = None
    price: Optional[PriceDetail] = None


class TourOption(BaseModel):
    """Opção de tour (modalidade/preço)"""
    name_option: Optional[str] = None
    details: Optional[List[OptionDetail]] = None


class Location(BaseModel):
    """Localização do tour"""
    main: Optional[str] = None
    region: Optional[str] = None


class DurationInfo(BaseModel):
    """Informação de duração"""
    quantity: Optional[float] = None
    unit: Optional[str] = None


class NonOperatingPeriod(BaseModel):
    """Período de não operação"""
    start: Optional[str] = None
    end: Optional[str] = None
    date: Optional[str] = None


class Operation(BaseModel):
    """Operação do tour"""
    non_operating_periods: Optional[List[Any]] = None


class Tour(BaseModel):
    """Tour completo extraído"""
    id: Optional[str] = None
    city: Optional[str] = None
    title: str
    location: Optional[Location] = None
    duration: Optional[DurationInfo] = None
    description: Optional[str] = None
    options: Optional[List[TourOption]] = None
    operation: Optional[Operation] = None
    min_adults: Optional[int] = None
    max_adults: Optional[int] = None
    max_childrens: Optional[int] = None
    observations: Optional[str] = None
    source_chunks: Optional[List[str]] = None


class Product(BaseModel):
    """Produto do catálogo"""
    type: Optional[str] = None
    general_conditions: Optional[str] = None
    year: Optional[int] = None
    destination: Optional[List[str]] = None


class Catalog(BaseModel):
    """Catálogo completo de tours"""
    agency: Optional[str] = None
    product: Optional[Product] = None
    tours: List[Tour]

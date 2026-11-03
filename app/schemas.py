"""Contratos de entrada/saída da API de risco clínico da CLYVO VET."""
from typing import Literal

from pydantic import BaseModel, Field, model_validator

BLOOD_TYPES = {
    "Cachorro": {"DEA 1.1+", "DEA 1.1-", "DEA 4+"},
    "Gato": {"A", "AB", "B"},
}


class PetInput(BaseModel):
    """Dados do pet no momento da consulta (mesmos atributos do treino)."""

    species: Literal["Cachorro", "Gato"]
    pet_gender: Literal["Macho", "Fêmea"]
    pet_blood_type: str = Field(..., examples=["DEA 1.1+"])
    pet_weight: float = Field(..., gt=0, le=120, description="Peso em kg")
    pet_age_years: float = Field(..., ge=0, le=40, description="Idade em anos")
    is_castrated: bool
    has_allergy: bool
    has_chronic_disease: bool
    total_vaccines_registered: int = Field(..., ge=0, le=50)

    @model_validator(mode="after")
    def _blood_type_matches_species(self):
        validos = BLOOD_TYPES[self.species]
        if self.pet_blood_type not in validos:
            raise ValueError(
                f"pet_blood_type '{self.pet_blood_type}' inválido para {self.species}. "
                f"Valores aceitos: {sorted(validos)}"
            )
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "species": "Cachorro",
                "pet_gender": "Fêmea",
                "pet_blood_type": "DEA 1.1+",
                "pet_weight": 12.4,
                "pet_age_years": 8.2,
                "is_castrated": True,
                "has_allergy": False,
                "has_chronic_disease": True,
                "total_vaccines_registered": 2,
            }
        }
    }


class PredictionOutput(BaseModel):
    risk: Literal[0, 1] = Field(..., description="0 = baixo risco, 1 = alto risco")
    risk_label: Literal["Baixo risco", "Alto risco"]
    risk_probability: float = Field(..., ge=0, le=1, description="P(alto risco)")
    risk_score_pct: float = Field(..., description="risk_probability em %")
    recommendation: str

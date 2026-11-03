"""Schemas (entrada/saída) das rotas de cadastro e consulta."""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .schemas import BLOOD_TYPES


def _vazio_para_none(v):
    # Oracle trata '' como NULL; padronizamos igual em qualquer banco.
    return (v.strip() or None) if isinstance(v, str) else v


class TutorIn(BaseModel):
    nome: str = Field(..., min_length=2, max_length=150)
    email: str | None = Field(None, max_length=150)
    _norm = field_validator("email", mode="before")(_vazio_para_none)


class TutorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    email: str | None


class ClinicaIn(BaseModel):
    nome: str = Field(..., min_length=2, max_length=150)


class ClinicaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str


class PetIn(BaseModel):
    tutor_id: int
    nome: str = Field(..., min_length=1, max_length=100)
    especie: Literal["Cachorro", "Gato"]
    raca: str | None = Field(None, max_length=100)
    data_nascimento: date
    sexo: Literal["Macho", "Fêmea"]
    tipo_sanguineo: str
    castrado: bool = False
    alergia: str | None = Field(None, max_length=255, description="Vazio = nenhuma")
    doenca_cronica: str | None = Field(None, max_length=255, description="Vazio = nenhuma")
    _norm = field_validator("raca", "alergia", "doenca_cronica", mode="before")(_vazio_para_none)

    @model_validator(mode="after")
    def _validar(self):
        if self.tipo_sanguineo not in BLOOD_TYPES[self.especie]:
            raise ValueError(
                f"tipo_sanguineo '{self.tipo_sanguineo}' inválido para {self.especie}. "
                f"Aceitos: {sorted(BLOOD_TYPES[self.especie])}")
        if self.data_nascimento > date.today():
            raise ValueError("data_nascimento não pode ser futura")
        return self


class PetOut(BaseModel):
    id: int
    tutor_id: int
    nome: str
    especie: str
    raca: str | None
    data_nascimento: date
    sexo: str
    tipo_sanguineo: str
    castrado: bool
    alergia: str | None
    doenca_cronica: str | None
    total_vacinas: int


class VacinaIn(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    data_aplicacao: date
    data_validade: date | None = None

    @model_validator(mode="after")
    def _validar(self):
        if self.data_validade and self.data_validade < self.data_aplicacao:
            raise ValueError("data_validade não pode ser anterior à data_aplicacao")
        return self


class VacinaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    pet_id: int
    nome: str
    data_aplicacao: date
    data_validade: date | None


class ConsultaIn(BaseModel):
    pet_id: int
    clinica_id: int
    data_consulta: date
    sintomas: str | None = Field(None, max_length=500)
    diagnostico: str | None = Field(None, max_length=500)
    peso_kg: float = Field(..., gt=0, le=120)
    _norm = field_validator("sintomas", "diagnostico", mode="before")(_vazio_para_none)

    @field_validator("data_consulta")
    @classmethod
    def _nao_futura(cls, v: date):
        if v > date.today():
            raise ValueError("data_consulta não pode ser futura")
        return v


class PredicaoOut(BaseModel):
    risco: Literal[0, 1]
    risco_label: Literal["Baixo risco", "Alto risco"]
    probabilidade: float
    score_pct: float
    recomendacao: str
    modelo_versao: str
    criado_em: datetime | None


class ConsultaOut(BaseModel):
    id: int
    pet_id: int
    pet_nome: str
    clinica_id: int
    data_consulta: date
    sintomas: str | None
    diagnostico: str | None
    peso_kg: float
    predicao: PredicaoOut | None


class PetAltoRisco(BaseModel):
    pet_id: int
    pet_nome: str
    especie: str
    tutor_nome: str
    consulta_id: int
    data_consulta: date
    probabilidade: float
    score_pct: float
    recomendacao: str

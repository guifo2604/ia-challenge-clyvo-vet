"""Converte registros do banco no PetInput que o modelo espera."""
from datetime import date

from ..db.models import Consulta, Pet
from ..schemas import PetInput


def idade_em_anos(nascimento: date, referencia: date) -> float:
    # Mesma fórmula do notebook: dias / 365.25
    return (referencia - nascimento).days / 365.25


def pet_input_from_consulta(consulta: Consulta) -> PetInput:
    pet: Pet = consulta.pet
    return PetInput(
        species=pet.especie,
        pet_gender=pet.sexo,
        pet_blood_type=pet.tipo_sanguineo,
        pet_weight=consulta.peso_kg,
        pet_age_years=idade_em_anos(pet.data_nascimento, consulta.data_consulta),
        is_castrated=bool(pet.castrado),
        has_allergy=bool(pet.alergia),
        has_chronic_disease=bool(pet.doenca_cronica),
        total_vaccines_registered=len(pet.vacinas),
    )

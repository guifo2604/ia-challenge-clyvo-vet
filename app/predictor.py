"""Carrega o XGBoost treinado na Sprint 3 e executa a inferência."""
from pathlib import Path

import json

import joblib
import pandas as pd
from xgboost import XGBClassifier

from .schemas import PetInput, PredictionOutput

MODEL_DIR = Path(__file__).resolve().parent.parent / "model"
SENIOR_AGE_YEARS = 7.0  # mesma regra do notebook (IS_SENIOR)
THRESHOLD = 0.5  # limiar de decisão (mesmo do model.predict)


class RiskPredictor:
    def __init__(self, model_dir: Path = MODEL_DIR):
        # Formato preferido: JSON nativo do XGBoost (portátil entre versões/SO).
        # Fallback: .pkl gerado pelo notebook da Sprint 3.
        json_model = model_dir / "xgboost_model_clyvo.json"
        json_feats = model_dir / "model_features.json"
        if json_model.exists() and json_feats.exists():
            self.model = XGBClassifier()
            self.model.load_model(json_model)
            self.features: list[str] = json.loads(json_feats.read_text(encoding="utf-8"))
        else:
            self.model = joblib.load(model_dir / "xgboost_model_clyvo.pkl")
            self.features = joblib.load(model_dir / "model_features.pkl")

    def _to_frame(self, pet: PetInput) -> pd.DataFrame:
        """Reproduz o pré-processamento do notebook (one-hot com drop_first)."""
        row = dict.fromkeys(self.features, 0)
        row.update(
            PET_WEIGHT=pet.pet_weight,
            PET_AGE_YEARS=pet.pet_age_years,
            IS_SENIOR=int(pet.pet_age_years >= SENIOR_AGE_YEARS),
            IS_CASTRATED=int(pet.is_castrated),
            HAS_ALLERGY=int(pet.has_allergy),
            HAS_CHRONIC_DISEASE=int(pet.has_chronic_disease),
            TOTAL_VACCINES_REGISTERED=pet.total_vaccines_registered,
        )
        # Categorias-base (dropadas no treino): Cachorro, Fêmea, tipo sanguíneo "A"
        if pet.species == "Gato":
            row["SPECIES_Gato"] = 1
        if pet.pet_gender == "Macho":
            row["PET_GENDER_Macho"] = 1
        blood_col = f"PET_BLOOD_TYPE_{pet.pet_blood_type}"
        if blood_col in row:
            row[blood_col] = 1
        # Garante mesma ordem de colunas do treino
        return pd.DataFrame([row], columns=self.features)

    def predict(self, pet: PetInput) -> PredictionOutput:
        proba = float(self.model.predict_proba(self._to_frame(pet))[0, 1])
        risk = int(proba >= THRESHOLD)
        return PredictionOutput(
            risk=risk,
            risk_label="Alto risco" if risk else "Baixo risco",
            risk_probability=round(proba, 4),
            risk_score_pct=round(proba * 100, 1),
            recommendation=self._recommendation(proba),
        )

    @staticmethod
    def _recommendation(p: float) -> str:
        if p >= 0.75:
            return ("Prioridade alta na triagem: agendar retorno preventivo em curto prazo "
                    "e revisar histórico clínico do pet.")
        if p >= THRESHOLD:
            return "Acompanhamento preventivo recomendado: agendar retorno e monitorar sintomas."
        return "Manter rotina de check-ups e calendário vacinal em dia."

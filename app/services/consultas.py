"""Regras de negócio: consulta + predição de risco + conversões para a API."""
from datetime import datetime

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from ..db.models import Consulta, Pet, PredicaoRisco
from ..predictor import RiskPredictor
from ..schemas_api import ConsultaOut, PetOut, PredicaoOut
from .pet_features import pet_input_from_consulta

MODELO_VERSAO = "xgboost-sprint3-v1"


def registrar_predicao(session: Session, consulta: Consulta, predictor: RiskPredictor) -> PredicaoRisco:
    """Roda a IA com os dados do banco e grava/atualiza CV_PREDICAO_RISCO."""
    try:
        saida = predictor.predict(pet_input_from_consulta(consulta))
    except ValidationError as e:
        msg = "; ".join(err["msg"] for err in e.errors())
        raise HTTPException(422, f"Dados do pet/consulta inválidos para a IA: {msg}")

    pred = consulta.predicao or PredicaoRisco(consulta_id=consulta.id)
    pred.risco = saida.risk
    pred.probabilidade = saida.risk_probability
    pred.recomendacao = saida.recommendation
    pred.modelo_versao = MODELO_VERSAO
    pred.criado_em = datetime.now()
    session.add(pred)
    session.flush()
    session.refresh(consulta)
    return pred


def predicao_out(p: PredicaoRisco | None) -> PredicaoOut | None:
    if p is None:
        return None
    return PredicaoOut(
        risco=p.risco,
        risco_label="Alto risco" if p.risco else "Baixo risco",
        probabilidade=p.probabilidade,
        score_pct=round(p.probabilidade * 100, 1),
        recomendacao=p.recomendacao,
        modelo_versao=p.modelo_versao,
        criado_em=p.criado_em,
    )


def consulta_out(c: Consulta) -> ConsultaOut:
    return ConsultaOut(
        id=c.id, pet_id=c.pet_id, pet_nome=c.pet.nome, clinica_id=c.clinica_id,
        data_consulta=c.data_consulta, sintomas=c.sintomas, diagnostico=c.diagnostico,
        peso_kg=c.peso_kg, predicao=predicao_out(c.predicao),
    )


def pet_out(p: Pet) -> PetOut:
    return PetOut(
        id=p.id, tutor_id=p.tutor_id, nome=p.nome, especie=p.especie, raca=p.raca,
        data_nascimento=p.data_nascimento, sexo=p.sexo, tipo_sanguineo=p.tipo_sanguineo,
        castrado=bool(p.castrado), alergia=p.alergia, doenca_cronica=p.doenca_cronica,
        total_vacinas=len(p.vacinas),
    )

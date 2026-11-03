"""Consultas, histórico e a integração com a IA."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..db.database import get_session
from ..db.models import Clinica, Consulta, Pet
from ..predictor import RiskPredictor
from ..schemas_api import ConsultaIn, ConsultaOut, PetAltoRisco
from ..services.consultas import consulta_out, registrar_predicao

router = APIRouter()


def get_predictor(request: Request) -> RiskPredictor:
    return request.app.state.predictor


def _carregar(session: Session, consulta_id: int) -> Consulta:
    c = session.get(Consulta, consulta_id)
    if c is None:
        raise HTTPException(404, f"Consulta {consulta_id} não encontrada")
    return c


@router.post("/consultas", response_model=ConsultaOut, status_code=201, tags=["Consultas"],
             summary="Registrar consulta (a IA calcula o risco automaticamente)")
def registrar_consulta(dados: ConsultaIn, session: Session = Depends(get_session),
                       predictor: RiskPredictor = Depends(get_predictor)):
    pet = session.get(Pet, dados.pet_id)
    if pet is None:
        raise HTTPException(404, f"Pet {dados.pet_id} não encontrado")
    if session.get(Clinica, dados.clinica_id) is None:
        raise HTTPException(404, f"Clínica {dados.clinica_id} não encontrada")
    if dados.data_consulta < pet.data_nascimento:
        raise HTTPException(422, "data_consulta anterior ao nascimento do pet")

    consulta = Consulta(**dados.model_dump())
    session.add(consulta)
    session.flush()
    try:
        registrar_predicao(session, consulta, predictor)  # consulta + predição na mesma transação
    except Exception:
        session.rollback()
        raise
    session.commit()
    return consulta_out(consulta)


@router.get("/consultas/{consulta_id}", response_model=ConsultaOut, tags=["Consultas"])
def obter_consulta(consulta_id: int, session: Session = Depends(get_session)):
    return consulta_out(_carregar(session, consulta_id))


@router.post("/consultas/{consulta_id}/prever", response_model=ConsultaOut, tags=["Consultas"],
             summary="Recalcular o risco de uma consulta")
def prever_consulta(consulta_id: int, session: Session = Depends(get_session),
                    predictor: RiskPredictor = Depends(get_predictor)):
    consulta = _carregar(session, consulta_id)
    registrar_predicao(session, consulta, predictor)
    session.commit()
    return consulta_out(consulta)


@router.post("/consultas/prever-pendentes", tags=["Consultas"],
             summary="Calcular o risco das consultas que ainda não têm predição")
def prever_pendentes(session: Session = Depends(get_session),
                     predictor: RiskPredictor = Depends(get_predictor)):
    pendentes = session.scalars(select(Consulta).where(~Consulta.predicao.has())).all()
    feitas, erros = 0, 0
    for c in pendentes:
        try:
            registrar_predicao(session, c, predictor)
            feitas += 1
        except HTTPException:
            erros += 1
    session.commit()
    return {"previstas": feitas, "com_erro": erros}


@router.get("/pets/{pet_id}/consultas", response_model=list[ConsultaOut], tags=["Consultas"],
            summary="Histórico do pet (mais recente primeiro) com o risco de cada consulta")
def historico_do_pet(pet_id: int, session: Session = Depends(get_session)):
    if session.get(Pet, pet_id) is None:
        raise HTTPException(404, f"Pet {pet_id} não encontrado")
    q = (select(Consulta).where(Consulta.pet_id == pet_id)
         .options(selectinload(Consulta.predicao), selectinload(Consulta.pet))
         .order_by(Consulta.data_consulta.desc(), Consulta.id.desc()))
    return [consulta_out(c) for c in session.scalars(q)]


@router.get("/clinicas/{clinica_id}/consultas", response_model=list[ConsultaOut], tags=["Clínicas"],
            summary="Consultas da clínica (mais recente primeiro)")
def consultas_da_clinica(clinica_id: int, session: Session = Depends(get_session)):
    if session.get(Clinica, clinica_id) is None:
        raise HTTPException(404, f"Clínica {clinica_id} não encontrada")
    q = (select(Consulta).where(Consulta.clinica_id == clinica_id)
         .options(selectinload(Consulta.predicao), selectinload(Consulta.pet))
         .order_by(Consulta.data_consulta.desc(), Consulta.id.desc()))
    return [consulta_out(c) for c in session.scalars(q)]


@router.get("/clinicas/{clinica_id}/alto-risco", response_model=list[PetAltoRisco], tags=["Clínicas"],
            summary="Pets cuja consulta mais recente está em ALTO risco (maior risco primeiro)")
def pets_alto_risco(clinica_id: int, session: Session = Depends(get_session)):
    if session.get(Clinica, clinica_id) is None:
        raise HTTPException(404, f"Clínica {clinica_id} não encontrada")
    q = (select(Consulta).where(Consulta.clinica_id == clinica_id)
         .options(selectinload(Consulta.predicao),
                  selectinload(Consulta.pet).selectinload(Pet.tutor))
         .order_by(Consulta.data_consulta.desc(), Consulta.id.desc()))
    ultima_por_pet: dict[int, Consulta] = {}
    for c in session.scalars(q):          # já vem da mais recente para a mais antiga
        ultima_por_pet.setdefault(c.pet_id, c)
    lista = [
        PetAltoRisco(
            pet_id=c.pet_id, pet_nome=c.pet.nome, especie=c.pet.especie,
            tutor_nome=c.pet.tutor.nome, consulta_id=c.id, data_consulta=c.data_consulta,
            probabilidade=c.predicao.probabilidade, score_pct=round(c.predicao.probabilidade * 100, 1),
            recomendacao=c.predicao.recomendacao)
        for c in ultima_por_pet.values() if c.predicao and c.predicao.risco == 1
    ]
    return sorted(lista, key=lambda x: x.probabilidade, reverse=True)

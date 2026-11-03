"""Tutores, clínicas, pets e vacinas."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..db.database import get_session
from ..db.models import Clinica, Pet, Tutor, VacinaAplicada
from ..schemas_api import (ClinicaIn, ClinicaOut, PetIn, PetOut, TutorIn, TutorOut,
                           VacinaIn, VacinaOut)
from ..services.consultas import pet_out

router = APIRouter()


def _get_or_404(session: Session, model, id_: int, nome: str):
    obj = session.get(model, id_)
    if obj is None:
        raise HTTPException(404, f"{nome} {id_} não encontrado(a)")
    return obj


# ---------- Tutores ----------
@router.get("/tutores", response_model=list[TutorOut], tags=["Tutores"])
def listar_tutores(session: Session = Depends(get_session)):
    return session.scalars(select(Tutor).order_by(Tutor.nome)).all()


@router.post("/tutores", response_model=TutorOut, status_code=201, tags=["Tutores"])
def criar_tutor(dados: TutorIn, session: Session = Depends(get_session)):
    tutor = Tutor(**dados.model_dump())
    session.add(tutor)
    session.commit()
    return tutor


@router.get("/tutores/{tutor_id}", response_model=TutorOut, tags=["Tutores"])
def obter_tutor(tutor_id: int, session: Session = Depends(get_session)):
    return _get_or_404(session, Tutor, tutor_id, "Tutor")


# ---------- Clínicas ----------
@router.get("/clinicas", response_model=list[ClinicaOut], tags=["Clínicas"])
def listar_clinicas(session: Session = Depends(get_session)):
    return session.scalars(select(Clinica).order_by(Clinica.nome)).all()


@router.post("/clinicas", response_model=ClinicaOut, status_code=201, tags=["Clínicas"])
def criar_clinica(dados: ClinicaIn, session: Session = Depends(get_session)):
    clinica = Clinica(**dados.model_dump())
    session.add(clinica)
    session.commit()
    return clinica


# ---------- Pets ----------
@router.get("/pets", response_model=list[PetOut], tags=["Pets"])
def listar_pets(tutor_id: int | None = Query(None, description="Filtra pelos pets deste tutor"),
                session: Session = Depends(get_session)):
    q = select(Pet).options(selectinload(Pet.vacinas)).order_by(Pet.nome)
    if tutor_id is not None:
        q = q.where(Pet.tutor_id == tutor_id)
    return [pet_out(p) for p in session.scalars(q)]


@router.post("/pets", response_model=PetOut, status_code=201, tags=["Pets"])
def criar_pet(dados: PetIn, session: Session = Depends(get_session)):
    _get_or_404(session, Tutor, dados.tutor_id, "Tutor")
    campos = dados.model_dump()
    campos["castrado"] = int(campos["castrado"])
    pet = Pet(**campos)
    session.add(pet)
    session.commit()
    return pet_out(pet)


@router.get("/pets/{pet_id}", response_model=PetOut, tags=["Pets"])
def obter_pet(pet_id: int, session: Session = Depends(get_session)):
    return pet_out(_get_or_404(session, Pet, pet_id, "Pet"))


# ---------- Vacinas ----------
@router.get("/pets/{pet_id}/vacinas", response_model=list[VacinaOut], tags=["Vacinas"])
def listar_vacinas(pet_id: int, session: Session = Depends(get_session)):
    _get_or_404(session, Pet, pet_id, "Pet")
    q = select(VacinaAplicada).where(VacinaAplicada.pet_id == pet_id).order_by(VacinaAplicada.data_aplicacao)
    return session.scalars(q).all()


@router.post("/pets/{pet_id}/vacinas", response_model=VacinaOut, status_code=201, tags=["Vacinas"])
def registrar_vacina(pet_id: int, dados: VacinaIn, session: Session = Depends(get_session)):
    _get_or_404(session, Pet, pet_id, "Pet")
    vacina = VacinaAplicada(pet_id=pet_id, **dados.model_dump())
    session.add(vacina)
    session.commit()
    return vacina

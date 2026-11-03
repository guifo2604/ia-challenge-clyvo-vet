"""Carrega os dados de exemplo (dataset-prontpet.csv) nas tabelas CV_*.

Uso:
    python -m scripts.seed_from_csv            # só insere se as tabelas estiverem vazias
    python -m scripts.seed_from_csv --reset    # apaga SÓ as tabelas CV_* e recria
"""
import argparse
import csv
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import Base, engine

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "dataset-prontpet.csv"


def _d(txt: str, fmt: str):
    return datetime.strptime(txt, fmt).date() if txt else None


def seed(session: Session, csv_path: Path = CSV_PATH) -> dict:
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))

    tutores, clinicas, pets, vacinas, consultas = {}, {}, {}, set(), set()
    for r in rows:
        if r["ID_TUTOR"] not in tutores:
            t = models.Tutor(nome=r["TUTOR_NAME"])
            session.add(t)
            tutores[r["ID_TUTOR"]] = t
        if r["ID_CLINIC"] not in clinicas:
            c = models.Clinica(nome=r["CLINIC_NAME"])
            session.add(c)
            clinicas[r["ID_CLINIC"]] = c
    session.flush()

    for r in rows:
        if r["ID_PET"] not in pets:
            p = models.Pet(
                tutor_id=tutores[r["ID_TUTOR"]].id,
                nome=r["PET_NAME"],
                especie=r["SPECIES"],
                raca=r["BREED"],
                data_nascimento=_d(r["PET_BIRTH_DATE"], "%d/%m/%Y %H:%M"),
                sexo=r["PET_GENDER"],
                tipo_sanguineo=r["PET_BLOOD_TYPE"],
                castrado=int(r["IS_CASTRATED_PET"].upper().startswith("S")),
                alergia=r["PET_ALLERGY"] or None,
                doenca_cronica=r["CHRONIC_PET_DISEASE"] or None,
            )
            session.add(p)
            pets[r["ID_PET"]] = p
    session.flush()

    for r in rows:
        chave_vac = (r["ID_PET"], r["ID_VACCINE"])
        if r["ID_VACCINE"] and chave_vac not in vacinas:
            vacinas.add(chave_vac)
            session.add(models.VacinaAplicada(
                pet_id=pets[r["ID_PET"]].id,
                nome=r["VACCINE_NAME"],
                data_aplicacao=_d(r["VACCINE_APPLICATION_DATE"], "%d/%m/%Y"),
                data_validade=_d(r["VACCINE_EXPIRATION_DATE"], "%d/%m/%Y"),
            ))
        if r["ID_CONSULTATION"] not in consultas:
            consultas.add(r["ID_CONSULTATION"])
            session.add(models.Consulta(
                pet_id=pets[r["ID_PET"]].id,
                clinica_id=clinicas[r["ID_CLINIC"]].id,
                data_consulta=_d(r["CONSULTATION_DATE"], "%d/%m/%Y"),
                sintomas=r["SYMPTOMS"],
                diagnostico=r["DIAGNOSIS"],
                peso_kg=float(r["PET_WEIGHT"].replace(",", ".")),
            ))
    session.commit()
    return {"tutores": len(tutores), "clinicas": len(clinicas), "pets": len(pets),
            "vacinas": len(vacinas), "consultas": len(consultas)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="recria as tabelas CV_*")
    args = ap.parse_args()

    if args.reset:
        Base.metadata.drop_all(engine)   # só conhece as tabelas CV_* deste projeto
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        if session.scalar(select(models.Tutor.id).limit(1)) is not None:
            print("Tabelas já têm dados. Use --reset para recarregar.")
            return
        print("Carregado:", seed(session))


if __name__ == "__main__":
    main()

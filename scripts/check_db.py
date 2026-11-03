"""Verifica a conexão, as tabelas CV_* e se a IA consegue prever a partir do banco.

Uso:  python -m scripts.check_db
"""
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import engine
from app.predictor import RiskPredictor
from app.services.pet_features import pet_input_from_consulta

ESPERADO = {"tutores": 15, "clinicas": 4, "pets": 20, "vacinas": 59, "consultas": 100}


def main():
    print(f"Banco: {engine.dialect.name}  ->  {engine.url.render_as_string(hide_password=True)}")

    with engine.connect() as conn:
        conn.execute(text("SELECT 1 FROM DUAL" if engine.dialect.name == "oracle" else "SELECT 1"))
    print("[OK] conexão")

    with Session(engine) as s:
        contagens = {
            "tutores": s.scalar(select(func.count(models.Tutor.id))),
            "clinicas": s.scalar(select(func.count(models.Clinica.id))),
            "pets": s.scalar(select(func.count(models.Pet.id))),
            "vacinas": s.scalar(select(func.count(models.VacinaAplicada.id))),
            "consultas": s.scalar(select(func.count(models.Consulta.id))),
        }
        for nome, qtd in contagens.items():
            marca = "OK" if qtd == ESPERADO[nome] else "ATENÇÃO"
            print(f"[{marca}] {nome}: {qtd} (esperado {ESPERADO[nome]})")

        predictor = RiskPredictor()
        resultados = [predictor.predict(pet_input_from_consulta(c)).risk
                      for c in s.scalars(select(models.Consulta))]
        print(f"[OK] IA rodou em {len(resultados)} consultas vindas do banco: "
              f"{sum(resultados)} alto risco, {len(resultados) - sum(resultados)} baixo risco")


if __name__ == "__main__":
    main()

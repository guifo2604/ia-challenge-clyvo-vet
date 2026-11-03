"""Modelo de dados da CLYVO VET (prefixo CV_ para não colidir com tabelas TB_ de outras matérias no schema Oracle compartilhado)."""
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Float, ForeignKey, Identity, Integer, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Tutor(Base):
    __tablename__ = "CV_TUTOR"
    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    nome: Mapped[str] = mapped_column(String(150))
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    pets: Mapped[list["Pet"]] = relationship(back_populates="tutor")


class Clinica(Base):
    __tablename__ = "CV_CLINICA"
    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    nome: Mapped[str] = mapped_column(String(150))


class Pet(Base):
    __tablename__ = "CV_PET"
    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    tutor_id: Mapped[int] = mapped_column(ForeignKey("CV_TUTOR.id"))
    nome: Mapped[str] = mapped_column(String(100))
    especie: Mapped[str] = mapped_column(String(20))        # Cachorro | Gato
    raca: Mapped[str | None] = mapped_column(String(100), nullable=True)
    data_nascimento: Mapped[date] = mapped_column(Date)
    sexo: Mapped[str] = mapped_column(String(10))           # Macho | Fêmea
    tipo_sanguineo: Mapped[str] = mapped_column(String(20))
    castrado: Mapped[int] = mapped_column(SmallInteger, default=0)  # 0/1 (NUMBER(1): compatível com qualquer Oracle)
    alergia: Mapped[str | None] = mapped_column(String(255), nullable=True)         # NULL = nenhuma
    doenca_cronica: Mapped[str | None] = mapped_column(String(255), nullable=True)  # NULL = nenhuma

    __table_args__ = (CheckConstraint("castrado IN (0, 1)", name="ck_cv_pet_castrado"),)

    tutor: Mapped[Tutor] = relationship(back_populates="pets")
    vacinas: Mapped[list["VacinaAplicada"]] = relationship(back_populates="pet")
    consultas: Mapped[list["Consulta"]] = relationship(back_populates="pet")


class VacinaAplicada(Base):
    __tablename__ = "CV_VACINA_APLICADA"
    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("CV_PET.id"))
    nome: Mapped[str] = mapped_column(String(100))
    data_aplicacao: Mapped[date] = mapped_column(Date)
    data_validade: Mapped[date | None] = mapped_column(Date, nullable=True)
    pet: Mapped[Pet] = relationship(back_populates="vacinas")


class Consulta(Base):
    __tablename__ = "CV_CONSULTA"
    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("CV_PET.id"))
    clinica_id: Mapped[int] = mapped_column(ForeignKey("CV_CLINICA.id"))
    data_consulta: Mapped[date] = mapped_column(Date)
    sintomas: Mapped[str | None] = mapped_column(String(500), nullable=True)
    diagnostico: Mapped[str | None] = mapped_column(String(500), nullable=True)
    peso_kg: Mapped[float] = mapped_column(Float)

    pet: Mapped[Pet] = relationship(back_populates="consultas")
    clinica: Mapped[Clinica] = relationship()
    predicao: Mapped["PredicaoRisco | None"] = relationship(back_populates="consulta", uselist=False)


class PredicaoRisco(Base):
    """Resultado da IA para uma consulta (auditável: guarda a versão do modelo)."""
    __tablename__ = "CV_PREDICAO_RISCO"
    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    consulta_id: Mapped[int] = mapped_column(ForeignKey("CV_CONSULTA.id"), unique=True)
    risco: Mapped[int] = mapped_column(Integer)              # 0 baixo | 1 alto
    probabilidade: Mapped[float] = mapped_column(Float)
    recomendacao: Mapped[str] = mapped_column(String(500))
    modelo_versao: Mapped[str] = mapped_column(String(50))
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    consulta: Mapped[Consulta] = relationship(back_populates="predicao")

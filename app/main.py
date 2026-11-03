"""API de inferência de risco clínico — CLYVO VET."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .predictor import RiskPredictor
from .routers import cadastros, consultas
from .schemas import PetInput, PredictionOutput


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.predictor = RiskPredictor()  # carrega o modelo uma única vez
    yield


app = FastAPI(
    title="CLYVO VET — API de Risco Clínico",
    description="Prediz o nível de risco (baixo/alto) de um pet a partir de seu histórico.",
    version="0.3.0",
    lifespan=lifespan,
)


STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _pagina(nome: str):
    return lambda: FileResponse(STATIC_DIR / nome)


for _rota, _arquivo in (("/", "index.html"), ("/tutor", "tutor.html"), ("/vet", "vet.html")):
    app.add_api_route(_rota, _pagina(_arquivo), methods=["GET"], include_in_schema=False)

app.include_router(cadastros.router)
app.include_router(consultas.router)


@app.get("/health", tags=["IA"])
def health():
    p: RiskPredictor = app.state.predictor
    return {"status": "ok", "model": "XGBoost", "n_features": len(p.features)}


@app.post("/predict", response_model=PredictionOutput, tags=["IA"], summary="Previsão avulsa (sem banco)")
def predict(pet: PetInput):
    return app.state.predictor.predict(pet)

"""
FastAPI application — the 'payload' for the cloud platform.

It intentionally stays small. Its job is to PROVE the infrastructure works:
  - GET  /            -> HTML page listing products (reads from the DB)
  - GET  /api/products-> JSON list of products
  - POST /api/products-> add a product (proves the DB is writable)
  - GET  /healthz     -> health check used by load balancers / Cloud Run
"""
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import SessionLocal, wait_for_db, db_is_healthy
from app.models import Product, init_db

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Cloud Platform Demo Store")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.on_event("startup")
def on_startup() -> None:
    wait_for_db()
    init_db()


def get_session() -> Session:
    return SessionLocal()


class ProductIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=400)
    price: float = Field(ge=0)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    session = get_session()
    try:
        products = session.query(Product).order_by(Product.id).all()
        items = [p.as_dict() for p in products]
    finally:
        session.close()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "products": items, "db_ok": db_is_healthy()},
    )


@app.get("/api/products")
def list_products():
    session = get_session()
    try:
        return [p.as_dict() for p in session.query(Product).order_by(Product.id).all()]
    finally:
        session.close()


@app.post("/api/products", status_code=201)
def add_product(payload: ProductIn):
    session = get_session()
    try:
        product = Product(
            name=payload.name,
            description=payload.description,
            price=payload.price,
        )
        session.add(product)
        session.commit()
        session.refresh(product)
        return product.as_dict()
    except Exception as exc:  # noqa: BLE001
        session.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        session.close()

@app.delete("/api/products/{product_id}", status_code=204)
def delete_product(product_id: int):
    session = get_session()
    try:
        product = session.get(Product, product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        session.delete(product)
        session.commit()
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        session.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        session.close()

@app.get("/healthz")
def healthz():
    """Returns 200 only if the app can reach the database."""
    if db_is_healthy():
        return {"status": "ok", "database": "reachable"}
    return JSONResponse(
        status_code=503,
        content={"status": "degraded", "database": "unreachable"},
    )

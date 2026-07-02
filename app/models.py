"""Product model + seed data."""
from sqlalchemy import Column, Integer, String, Numeric
from sqlalchemy.orm import Session

from app.database import Base, engine, SessionLocal


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    description = Column(String(400), nullable=False, default="")
    price = Column(Numeric(10, 2), nullable=False, default=0)

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
        }


_SEED = [
    ("Desert Roast Coffee", "Medium-dark single-origin beans, 250g bag.", 38.00),
    ("Ceramic Pour-Over", "Hand-glazed dripper for a clean, bright cup.", 95.00),
    ("Travel Tumbler", "Double-walled steel, keeps drinks hot for 6 hours.", 60.00),
    ("Cardamom Syrup", "Small-batch syrup for spiced lattes, 200ml.", 27.50),
]


def init_db() -> None:
    """Create tables and seed a few rows if the table is empty."""
    Base.metadata.create_all(bind=engine)
    session: Session = SessionLocal()
    try:
        if session.query(Product).count() == 0:
            session.add_all(
                Product(name=n, description=d, price=p) for n, d, p in _SEED
            )
            session.commit()
            print(f"[db] seeded {len(_SEED)} products")
    finally:
        session.close()


import datetime
from typing import List
from typing import Optional
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func
from sqlalchemy import String, DateTime, CheckConstraint, ForeignKey


class Base(DeclarativeBase):
    pass


class Route(Base):
    __tablename__ = "route"
    id: Mapped[int] = mapped_column(primary_key=True)
    origin: Mapped[str] = mapped_column(String(30))
    destination: Mapped[str] = mapped_column(String(30))
    abbr: Mapped[str] = mapped_column(String(30), unique=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    history: Mapped[List["RouteHistory"]] = relationship(back_populates="route")
    def __repr__(self) -> str:
        return f"Route(id={self.id!r}, origin={self.origin!r}, destination={self.destination!r}, abbr={self.abbr!r})"
    

class RouteHistory(Base):
    __tablename__ = "route_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    extracted_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    price: Mapped[int] = mapped_column(CheckConstraint("price > 0"))
    departure_date: Mapped[datetime.datetime]
    route_id = mapped_column(ForeignKey("route.id"))
    route: Mapped["Route"] = relationship(back_populates="history")
    def __repr__(self) -> str:
        return f"RouteHistory(id={self.id!r}, extracted_at={self.extracted_at!r}, price={self.price!r}, route_id={self.route_id!r})"


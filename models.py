from __future__ import annotations
from datetime import date
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy import (
	String,
	Integer,
	Date,
	ForeignKey,
)
from sqlalchemy.orm import (
	DeclarativeBase,
	Mapped,
	mapped_column,
	relationship,
)


class Model(AsyncAttrs, DeclarativeBase):
	__abstract__ = True
	id: Mapped[int] = mapped_column(Integer, primary_key=True)


class TrackedModel(Model):
	__abstract__ = True
	code: Mapped[str] = mapped_column(String, unique=True)
	created_at: Mapped[date] = mapped_column(Date, default=date.today)
	finished_at: Mapped[Optional[date]] = mapped_column(Date)


class Pallet(TrackedModel):
	__tablename__ = 'pallets'
	boxes: Mapped[List[Box]] = relationship(back_populates='pallet', cascade='all, delete-orphan')


class Box(TrackedModel):
	__tablename__ = 'boxes'
	pallet_id: Mapped[int] = mapped_column(ForeignKey('pallets.id'))
	pallet: Mapped[Pallet] = relationship(back_populates='boxes')
	products: Mapped[List[BoxProduct]] = relationship(back_populates='box', cascade='all, delete-orphan')


class Product(Model):
	__tablename__ = 'products'
	name: Mapped[str] = mapped_column(String)
	ean: Mapped[str] = mapped_column(String(15), unique=True)


class BoxProduct(Model):
	__tablename__ = 'box_products'
	box_id: Mapped[int] = mapped_column(ForeignKey('boxes.id'))
	product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
	box: Mapped[Box] = relationship(back_populates='products')
	product: Mapped[Product] = relationship()
	quantity: Mapped[int] = mapped_column(Integer, default=1)

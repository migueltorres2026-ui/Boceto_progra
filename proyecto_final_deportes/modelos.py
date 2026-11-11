"""Cuatro entidades, relaciones y restricciones que también protege SQLite."""
from __future__ import annotations
from datetime import date
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, Date, ForeignKey, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Categoria(Base):
    __tablename__ = 'categoria'
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descripcion: Mapped[str] = mapped_column(String(300), default='', nullable=False)
    equipos: Mapped[list[Equipo]] = relationship(back_populates='categoria', passive_deletes='all')


class Equipo(Base):
    __tablename__ = 'equipo'
    __table_args__ = (
        CheckConstraint('precio_diario > 0', name='ck_precio'),
        CheckConstraint('stock_total >= 0', name='ck_total'),
        CheckConstraint('stock_disponible >= 0 AND stock_disponible <= stock_total', name='ck_disponible'),
        CheckConstraint("tipo IN ('general','pelota','bicicleta')", name='ck_tipo'),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    categoria_id: Mapped[int] = mapped_column(ForeignKey('categoria.id', ondelete='RESTRICT'), nullable=False)
    precio_diario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    stock_total: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_disponible: Mapped[int] = mapped_column(Integer, nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    categoria: Mapped[Categoria] = relationship(back_populates='equipos')
    arriendos: Mapped[list[Arriendo]] = relationship(back_populates='equipo', passive_deletes='all')
    __mapper_args__ = {'polymorphic_on': tipo, 'polymorphic_identity': 'general'}

    def instrucciones(self):
        return 'Revisar integridad y limpieza antes de entregar.'


class Pelota(Equipo):
    __mapper_args__ = {'polymorphic_identity': 'pelota'}

    def instrucciones(self):
        return 'Revisar presión y superficie de la pelota.'


class Bicicleta(Equipo):
    __mapper_args__ = {'polymorphic_identity': 'bicicleta'}

    def instrucciones(self):
        return 'Revisar frenos, neumáticos y ajuste del sillín.'


class Cliente(Base):
    __tablename__ = 'cliente'
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    correo: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    telefono: Mapped[str] = mapped_column(String(30), nullable=False)
    arriendos: Mapped[list[Arriendo]] = relationship(back_populates='cliente', passive_deletes='all')


class Arriendo(Base):
    __tablename__ = 'arriendo'
    __table_args__ = (
        CheckConstraint('cantidad > 0', name='ck_cantidad'),
        CheckConstraint('fecha_fin_prevista >= fecha_inicio', name='ck_fechas'),
        CheckConstraint("estado IN ('ACTIVO','DEVUELTO')", name='ck_estado'),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    equipo_id: Mapped[int] = mapped_column(ForeignKey('equipo.id', ondelete='RESTRICT'), nullable=False)
    cliente_id: Mapped[int] = mapped_column(ForeignKey('cliente.id', ondelete='RESTRICT'), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin_prevista: Mapped[date] = mapped_column(Date, nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[str] = mapped_column(String(10), default='ACTIVO', nullable=False)
    equipo: Mapped[Equipo] = relationship(back_populates='arriendos')
    cliente: Mapped[Cliente] = relationship(back_populates='arriendos')

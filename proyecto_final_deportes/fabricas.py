"""Factory Method: cada creador decide qué producto ORM concreto construir."""
from abc import ABC, abstractmethod
from modelos import Equipo, Pelota, Bicicleta


class CreadorEquipo(ABC):
    @abstractmethod
    def factory_method(self) -> Equipo:
        """Punto de extensión: se redefine en las subclases creadoras."""

    def crear(self, nombre, categoria_id, precio_diario, stock_total):
        equipo = self.factory_method()
        equipo.nombre = nombre
        equipo.categoria_id = categoria_id
        equipo.precio_diario = precio_diario
        equipo.stock_total = stock_total
        equipo.stock_disponible = stock_total
        return equipo


class CreadorGeneral(CreadorEquipo):
    def factory_method(self):
        return Equipo()


class CreadorPelota(CreadorEquipo):
    def factory_method(self):
        return Pelota()


class CreadorBicicleta(CreadorEquipo):
    def factory_method(self):
        return Bicicleta()


CREADORES = {
    'general': CreadorGeneral(),
    'pelota': CreadorPelota(),
    'bicicleta': CreadorBicicleta(),
}

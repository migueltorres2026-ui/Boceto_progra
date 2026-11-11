"""Casos de uso: no contienen input, print ni widgets de Tkinter."""
from contextlib import contextmanager
from sqlalchemy import select, func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from modelos import Categoria, Equipo, Cliente, Arriendo
from fabricas import CREADORES
import validaciones as v


class Servicios:
    def __init__(self, Session):
        self.Session = Session

    @contextmanager
    def transaccion(self):
        try:
            with self.Session.begin() as session:
                yield session
        except IntegrityError:
            raise ValueError('Operación rechazada: nombre/correo repetido o registro relacionado.') from None

    @staticmethod
    def obtener(session, modelo, identificador):
        v.entero(identificador, 'ID')
        objeto = session.get(modelo, identificador)
        if objeto is None:
            raise ValueError(f'{modelo.__name__} no encontrado.')
        return objeto

    def guardar_categoria(self, nombre, descripcion='', id_categoria=None):
        nombre = v.texto(nombre, 'Nombre')
        descripcion = v.texto(descripcion, 'Descripción', 300, obligatorio=False)
        with self.transaccion() as s:
            c = self.obtener(s, Categoria, id_categoria) if id_categoria is not None else Categoria()
            c.nombre, c.descripcion = nombre, descripcion
            s.add(c)
        return c

    def categorias(self):
        with self.Session() as s:
            return s.scalars(select(Categoria).order_by(Categoria.nombre)).all()

    def eliminar_categoria(self, identificador):
        with self.transaccion() as s:
            c = self.obtener(s, Categoria, identificador)
            if s.scalar(select(func.count(Equipo.id)).where(Equipo.categoria_id == c.id)):
                raise ValueError('La categoría tiene equipos. Reasígnalos o elimínalos primero.')
            s.delete(c)

    def guardar_cliente(self, nombre, correo, telefono, id_cliente=None):
        nombre = v.texto(nombre, 'Nombre')
        correo = v.correo(correo)
        telefono = v.texto(telefono, 'Teléfono', 30)
        with self.transaccion() as s:
            c = self.obtener(s, Cliente, id_cliente) if id_cliente is not None else Cliente()
            c.nombre, c.correo, c.telefono = nombre, correo, telefono
            s.add(c)
        return c

    def clientes(self):
        with self.Session() as s:
            return s.scalars(select(Cliente).order_by(Cliente.nombre)).all()

    def eliminar_cliente(self, identificador):
        with self.transaccion() as s:
            c = self.obtener(s, Cliente, identificador)
            if s.scalar(select(func.count(Arriendo.id)).where(Arriendo.cliente_id == c.id)):
                raise ValueError('El cliente tiene historial de arriendos; no puede eliminarse.')
            s.delete(c)

    def guardar_equipo(self, nombre, categoria_id, precio_diario, stock_total, tipo='general', id_equipo=None):
        nombre = v.texto(nombre, 'Nombre')
        v.entero(categoria_id, 'Categoría')
        precio_diario = v.precio(precio_diario)
        v.entero(stock_total, 'Stock total', 0)
        if tipo not in CREADORES:
            raise ValueError('Tipo de equipamiento inválido.')
        with self.transaccion() as s:
            self.obtener(s, Categoria, categoria_id)
            if id_equipo is None:
                e = CREADORES[tipo].crear(nombre, categoria_id, precio_diario, stock_total)
                s.add(e)
            else:
                e = self.obtener(s, Equipo, id_equipo)
                if tipo != e.tipo:
                    raise ValueError('El tipo del equipo se conserva al editar; selecciona su tipo actual.')
                prestadas = s.scalar(select(func.coalesce(func.sum(Arriendo.cantidad), 0)).where(
                    Arriendo.equipo_id == e.id, Arriendo.estado == 'ACTIVO'))
                if stock_total < prestadas:
                    raise ValueError(f'Hay {prestadas} unidades arrendadas. El total no puede ser menor.')
                e.nombre, e.categoria_id, e.precio_diario = nombre, categoria_id, precio_diario
                e.stock_total = stock_total
                e.stock_disponible = stock_total - prestadas
        return e

    def equipos(self, solo_disponibles=False):
        consulta = select(Equipo).options(joinedload(Equipo.categoria)).order_by(Equipo.nombre)
        if solo_disponibles:
            consulta = consulta.where(Equipo.stock_disponible > 0)
        with self.Session() as s:
            return s.scalars(consulta).all()

    def eliminar_equipo(self, identificador):
        with self.transaccion() as s:
            e = self.obtener(s, Equipo, identificador)
            if s.scalar(select(func.count(Arriendo.id)).where(Arriendo.equipo_id == e.id)):
                raise ValueError('El equipo tiene historial de arriendos; no puede eliminarse.')
            s.delete(e)

    def registrar_arriendo(self, equipo_id, cliente_id, inicio, fin, cantidad):
        v.entero(equipo_id, 'Equipo')
        v.entero(cliente_id, 'Cliente')
        v.entero(cantidad, 'Cantidad')
        v.fechas(inicio, fin)
        with self.transaccion() as s:
            self.obtener(s, Equipo, equipo_id)
            self.obtener(s, Cliente, cliente_id)
            # UPDATE condicionado evita descontar stock insuficiente incluso si otra
            # operación lo modificó desde que se leyó el equipo.
            resultado = s.execute(update(Equipo).where(
                Equipo.id == equipo_id, Equipo.stock_disponible >= cantidad
            ).values(stock_disponible=Equipo.stock_disponible - cantidad))
            if resultado.rowcount != 1:
                raise ValueError('Stock insuficiente. No se guardó el arriendo.')
            arriendo = Arriendo(equipo_id=equipo_id, cliente_id=cliente_id,
                                fecha_inicio=inicio, fecha_fin_prevista=fin,
                                cantidad=cantidad, estado='ACTIVO')
            s.add(arriendo)
        return arriendo

    def devolver(self, id_arriendo):
        with self.transaccion() as s:
            a = self.obtener(s, Arriendo, id_arriendo)
            # Reclamar la devolución una sola vez, en la misma transacción.
            resultado = s.execute(update(Arriendo).where(
                Arriendo.id == a.id, Arriendo.estado == 'ACTIVO'
            ).values(estado='DEVUELTO'))
            if resultado.rowcount != 1:
                raise ValueError('Ese arriendo ya fue devuelto.')
            resultado = s.execute(update(Equipo).where(
                Equipo.id == a.equipo_id,
                Equipo.stock_disponible + a.cantidad <= Equipo.stock_total
            ).values(stock_disponible=Equipo.stock_disponible + a.cantidad))
            if resultado.rowcount != 1:
                raise ValueError('Stock inconsistente. La devolución no se guardó.')
        return a

    def arriendos(self, solo_activos=False):
        consulta = select(Arriendo).options(joinedload(Arriendo.equipo), joinedload(Arriendo.cliente)).order_by(Arriendo.id.desc())
        if solo_activos:
            consulta = consulta.where(Arriendo.estado == 'ACTIVO')
        with self.Session() as s:
            return s.scalars(consulta).all()

    def estadisticas(self):
        # COUNT(id) cuenta operaciones, nunca SUM(cantidad).
        with self.Session() as s:
            por_categoria = s.execute(select(Categoria.id, Categoria.nombre, func.count(Arriendo.id)).select_from(
                Categoria).join(Equipo, Equipo.categoria_id == Categoria.id).join(
                Arriendo, Arriendo.equipo_id == Equipo.id).group_by(Categoria.id, Categoria.nombre).order_by(Categoria.nombre)).all()
            por_equipo = s.execute(select(Equipo.id, Equipo.nombre, func.count(Arriendo.id).label('total')).join(
                Arriendo, Arriendo.equipo_id == Equipo.id).group_by(Equipo.id, Equipo.nombre).order_by(
                func.count(Arriendo.id).desc(), Equipo.id).limit(10)).all()
        return por_categoria, por_equipo

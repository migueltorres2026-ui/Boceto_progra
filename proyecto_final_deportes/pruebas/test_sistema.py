"""Pruebas en SQLite temporal: no tocan la base usada por la interfaz."""
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import date
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from conexion import configurar_bd, crear_tablas
from servicios import Servicios
from modelos import Equipo, Pelota, Bicicleta, Arriendo
from informes import crear_figura


class SistemaTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.ruta = Path(self.temp.name) / 'pruebas.db'
        self.engine, self.Session = configurar_bd(self.ruta)
        crear_tablas(self.engine)
        self.s = Servicios(self.Session)
        self.c = self.s.guardar_categoria('Balón', 'Deportes colectivos')
        self.e = self.s.guardar_equipo('Pelota', self.c.id, '3000.50', 5, 'pelota')
        self.cl = self.s.guardar_cliente('Miguel', 'MIGUEL@ejemplo.cl', '123456')

    def tearDown(self):
        self.engine.dispose()
        self.temp.cleanup()

    def arrendar(self, cantidad=2, equipo=None, cliente=None):
        return self.s.registrar_arriendo(equipo or self.e.id, cliente or self.cl.id,
                                        date(2026, 11, 10), date(2026, 11, 12), cantidad)

    def stock(self):
        return next(e for e in self.s.equipos() if e.id == self.e.id).stock_disponible

    def test_seis_pasos_rubrica_y_persistencia(self):
        self.assertEqual(self.stock(), 5)
        a = self.arrendar(2)
        self.assertEqual(self.stock(), 3)
        self.assertEqual(self.s.arriendos()[0].estado, 'ACTIVO')
        with self.assertRaises(ValueError):
            self.arrendar(4)
        self.assertEqual(self.stock(), 3)
        self.assertEqual(len(self.s.arriendos()), 1)
        self.s.devolver(a.id)
        self.assertEqual(self.stock(), 5)
        with self.assertRaises(ValueError):
            self.s.devolver(a.id)
        self.assertEqual(self.stock(), 5)
        self.engine.dispose()
        self.engine, self.Session = configurar_bd(self.ruta)
        self.s = Servicios(self.Session)
        self.assertEqual(self.stock(), 5)
        self.assertEqual(self.s.arriendos()[0].estado, 'DEVUELTO')
        self.assertEqual(self.s.estadisticas()[0][0][2], 1)

    def test_crud_y_restricciones_relaciones(self):
        otra = self.s.guardar_categoria('Otra')
        self.s.guardar_categoria('Otra editada', 'Descripción', otra.id)
        cliente = self.s.guardar_cliente('Ana', 'ana@ejemplo.cl', '987')
        self.s.guardar_cliente('Ana María', 'ana2@ejemplo.cl', '123', cliente.id)
        e = self.s.guardar_equipo('Casco', otra.id, '500', 1)
        self.s.guardar_equipo('Casco nuevo', otra.id, '600', 2, id_equipo=e.id)
        self.s.eliminar_equipo(e.id)
        self.s.eliminar_cliente(cliente.id)
        self.s.eliminar_categoria(otra.id)
        self.arrendar()
        for metodo, ident in ((self.s.eliminar_categoria, self.c.id),
                              (self.s.eliminar_equipo, self.e.id),
                              (self.s.eliminar_cliente, self.cl.id)):
            with self.assertRaises(ValueError):
                metodo(ident)

    def test_invalidos_y_unicos(self):
        for n in (0, -1, True):
            with self.assertRaises(ValueError): self.arrendar(n)
        with self.assertRaises(ValueError): self.arrendar(equipo=999)
        with self.assertRaises(ValueError): self.arrendar(cliente=999)
        with self.assertRaises(ValueError): self.s.guardar_categoria('Balón')
        with self.assertRaises(ValueError): self.s.guardar_cliente('Otro', 'miguel@ejemplo.cl', '1')
        with self.assertRaises(ValueError): self.s.guardar_cliente('Otro', 'incorrecto', '1')
        with self.assertRaises(ValueError): self.s.guardar_equipo('X', self.c.id, 'NaN', 1)
        with self.assertRaises(ValueError): self.s.guardar_equipo('X', self.c.id, '0', 1)
        with self.assertRaises(ValueError): self.s.guardar_equipo('X', self.c.id, '1.005', 1)
        with self.assertRaises(ValueError): self.s.guardar_equipo('X', self.c.id, '1', -1)
        with self.assertRaises(ValueError):
            self.s.registrar_arriendo(self.e.id, self.cl.id, date(2026,11,12), date(2026,11,10), 1)
        self.assertEqual(self.stock(), 5)
        self.assertEqual(self.s.arriendos(), [])

    def test_stock_al_editar_y_consultas(self):
        a = self.arrendar(2)
        with self.assertRaises(ValueError):
            self.s.guardar_equipo('Pelota', self.c.id, '3000', 1, 'pelota', self.e.id)
        self.s.guardar_equipo('Pelota', self.c.id, '3000', 7, 'pelota', self.e.id)
        self.assertEqual(self.stock(), 5)
        self.assertEqual(len(self.s.arriendos(True)), 1)
        self.s.devolver(a.id)
        self.assertEqual(self.stock(), 7)
        self.assertEqual(self.s.arriendos(True), [])
        self.arrendar(7)
        self.assertEqual(self.s.equipos(True), [])

    def test_factory_rehidrata_subtipos(self):
        b = self.s.guardar_equipo('Bici', self.c.id, '9000', 1, 'bicicleta')
        equipos = {e.id: e for e in self.s.equipos()}
        self.assertIsInstance(equipos[self.e.id], Pelota)
        self.assertIsInstance(equipos[b.id], Bicicleta)
        self.assertNotEqual(equipos[self.e.id].instrucciones(), equipos[b.id].instrucciones())

    def test_graficos_cuentan_operaciones_no_unidades(self):
        self.arrendar(2)
        self.arrendar(1)
        categorias, equipos = self.s.estadisticas()
        self.assertEqual(categorias[0][2], 2)
        self.assertEqual(equipos[0][2], 2)
        figura = crear_figura(self.s)
        self.assertEqual(len(figura.axes), 2)
        self.assertEqual(figura.axes[0].patches[0].get_width(), 2)
        figura.savefig(Path(self.temp.name) / 'graficos.png')

    def test_rollback_si_falla_insert_despues_de_descontar_stock(self):
        # Provocar un fallo real en SQLite después del UPDATE del stock.
        with self.engine.begin() as conexion:
            conexion.exec_driver_sql("CREATE TRIGGER rechazar BEFORE INSERT ON arriendo BEGIN SELECT RAISE(ABORT, 'prueba'); END")
        with self.assertRaises(ValueError): self.arrendar(2)
        self.assertEqual(self.stock(), 5)
        self.assertEqual(self.s.arriendos(), [])

    def test_bd_protege_stock_y_claves_foraneas(self):
        with self.assertRaises(IntegrityError):
            with self.Session.begin() as s:
                equipo = s.get(Equipo, self.e.id)
                equipo.stock_disponible = 6
        with self.assertRaises(IntegrityError):
            with self.Session.begin() as s:
                s.add(Arriendo(equipo_id=999, cliente_id=self.cl.id, cantidad=1,
                    fecha_inicio=date(2026,11,10), fecha_fin_prevista=date(2026,11,11)))
        self.assertEqual(self.stock(), 5)


if __name__ == '__main__':
    unittest.main()

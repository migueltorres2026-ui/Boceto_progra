"""Motor SQLite y fábrica de sesiones; la ruta no depende de la terminal."""
import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

RUTA_BD = Path(os.environ.get('DEPORTES_DB', Path(__file__).parent / 'datos' / 'deportes.db')).resolve()


def configurar_bd(ruta=RUTA_BD):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine('sqlite:///' + str(ruta), connect_args={'timeout': 15})

    @event.listens_for(engine, 'connect')
    def activar_claves_foraneas(conexion, _):
        conexion.execute('PRAGMA foreign_keys=ON')

    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def crear_tablas(engine):
    from modelos import Base
    Base.metadata.create_all(engine)

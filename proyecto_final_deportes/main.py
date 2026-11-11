"""Punto de entrada: configurar, crear tablas, iniciar Tkinter."""
import tkinter as tk
from tkinter import messagebox
from sqlalchemy.exc import SQLAlchemyError
from conexion import configurar_bd, crear_tablas
from servicios import Servicios
from interfaz import Aplicacion

def main():
    engine, Session = configurar_bd()
    try:
        crear_tablas(engine)
        app = Aplicacion(Servicios(Session))
        app.mainloop()
    except SQLAlchemyError as error:
        ventana = tk.Tk()
        ventana.withdraw()
        messagebox.showerror('Inicio', f'No se pudo abrir la base de datos: {error}')
        ventana.destroy()
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()

"""Formularios Tkinter. Los botones delegan las reglas a Servicios."""
from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox
from sqlalchemy.exc import SQLAlchemyError
from fabricas import CREADORES
from informes import crear_figura


def numero(texto, campo):
    try:
        return int(texto)
    except (ValueError, TypeError):
        raise ValueError(f'{campo}: ingresa un número entero.') from None


def fecha(texto):
    try:
        return date.fromisoformat(texto)
    except ValueError:
        raise ValueError('Fecha inválida: usa AAAA-MM-DD.') from None


def id_opcion(texto, campo):
    if not texto:
        raise ValueError(f'Selecciona {campo}.')
    return numero(texto.split(' | ', 1)[0], campo)


def tabla(parent, columnas):
    marco = ttk.Frame(parent)
    marco.pack(fill='both', expand=True, pady=8)
    vista = ttk.Treeview(marco, columns=columnas, show='headings', selectmode='browse', height=12)
    for nombre in columnas:
        vista.heading(nombre, text=nombre)
        vista.column(nombre, width=135, minwidth=70)
    vertical = ttk.Scrollbar(marco, orient='vertical', command=vista.yview)
    horizontal = ttk.Scrollbar(marco, orient='horizontal', command=vista.xview)
    vista.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    vista.grid(row=0, column=0, sticky='nsew')
    vertical.grid(row=0, column=1, sticky='ns')
    horizontal.grid(row=1, column=0, sticky='ew')
    marco.rowconfigure(0, weight=1)
    marco.columnconfigure(0, weight=1)
    return vista


class FormularioCRUD(ttk.Frame):
    def __init__(self, parent, app, titulo, campos, columnas, listar, guardar, eliminar, valores):
        super().__init__(parent, padding=15)
        self.app, self.campos = app, campos
        self.listar, self.guardar, self.eliminar, self.valores = listar, guardar, eliminar, valores
        self.identificador = None
        self.objetos, self.variables, self.widgets = {}, {}, {}
        ttk.Label(self, text=titulo, style='Titulo.TLabel').pack(anchor='w')
        ttk.Label(self, text='Nuevo: completa los campos y guarda. Editar o eliminar: selecciona una fila.').pack(anchor='w', pady=(4, 8))
        formulario = ttk.Frame(self)
        formulario.pack(fill='x')
        for i, (clave, etiqueta, opciones) in enumerate(campos):
            fila, columna = divmod(i, 3)
            bloque = ttk.Frame(formulario, padding=(0, 0, 15, 8))
            bloque.grid(row=fila, column=columna, sticky='ew')
            formulario.columnconfigure(columna, weight=1)
            ttk.Label(bloque, text=etiqueta).pack(anchor='w')
            variable = tk.StringVar()
            widget = (ttk.Combobox(bloque, textvariable=variable, state='readonly')
                      if opciones is not None else ttk.Entry(bloque, textvariable=variable))
            widget.pack(fill='x')
            if opciones:
                widget['values'] = opciones
            self.variables[clave], self.widgets[clave] = variable, widget
        botones = ttk.Frame(self)
        botones.pack(fill='x', pady=4)
        ttk.Button(botones, text='Nuevo / limpiar', command=self.limpiar).pack(side='left', padx=(0, 8))
        ttk.Button(botones, text='Guardar', command=lambda: app.ejecutar(self.guardar_formulario)).pack(side='left', padx=8)
        ttk.Button(botones, text='Eliminar seleccionado', command=lambda: app.ejecutar(self.eliminar_seleccionado)).pack(side='left', padx=8)
        ttk.Button(botones, text='Actualizar listas', command=lambda: app.ejecutar(app.refrescar)).pack(side='left', padx=8)
        self.vista = tabla(self, columnas)
        self.vista.bind('<<TreeviewSelect>>', self.seleccionar)
        self.limpiar()

    def limpiar(self):
        self.identificador = None
        for clave, variable in self.variables.items():
            variable.set('general' if clave == 'tipo' else '')
        if hasattr(self, 'vista'):
            self.vista.selection_remove(self.vista.selection())

    def cargar(self):
        self.objetos = {o.id: o for o in self.listar()}
        self.vista.delete(*self.vista.get_children())
        for identificador, objeto in self.objetos.items():
            self.vista.insert('', 'end', iid=str(identificador), values=self.valores(objeto))

    def seleccionar(self, _=None):
        seleccion = self.vista.selection()
        if not seleccion:
            return
        self.identificador = int(seleccion[0])
        objeto = self.objetos[self.identificador]
        for clave, variable in self.variables.items():
            if clave == 'categoria_id':
                variable.set(f'{objeto.categoria.id} | {objeto.categoria.nombre}')
            else:
                variable.set(str(getattr(objeto, clave)))

    def guardar_formulario(self):
        datos = {clave: variable.get() for clave, variable in self.variables.items()}
        self.guardar(datos, self.identificador)
        self.app.estado.set('Registro guardado correctamente.')
        self.limpiar()
        self.app.refrescar()

    def eliminar_seleccionado(self):
        if self.identificador is None:
            raise ValueError('Selecciona una fila para eliminar.')
        if messagebox.askyesno('Eliminar', '¿Eliminar el registro seleccionado?', parent=self):
            self.eliminar(self.identificador)
            self.limpiar()
            self.app.refrescar()
            self.app.estado.set('Registro eliminado.')


class Aplicacion(tk.Tk):
    def __init__(self, servicios):
        super().__init__()
        self.servicios = servicios
        self.title('Deportes | Gestión de arriendos')
        self.geometry('1180x760')
        self.minsize(960, 650)
        estilo = ttk.Style(self)
        if 'clam' in estilo.theme_names():
            estilo.theme_use('clam')
        estilo.configure('Titulo.TLabel', font=('Sans', 17, 'bold'))
        estilo.configure('Treeview', rowheight=28)
        estilo.configure('TButton', padding=6)
        self.estado = tk.StringVar(value='Selecciona una pestaña para comenzar.')
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=12, pady=12)
        self.crear_catalogos()
        self.crear_arriendos()
        self.crear_informes()
        ttk.Label(self, textvariable=self.estado, padding=10).pack(fill='x')
        self.refrescar()

    def ejecutar(self, accion):
        try:
            accion()
        except ValueError as error:
            messagebox.showwarning('Revisa los datos', str(error), parent=self)
        except SQLAlchemyError:
            messagebox.showerror('Base de datos', 'No se pudo completar la operación. Revisa la conexión o inténtalo nuevamente.', parent=self)

    def crear_catalogos(self):
        s = self.servicios
        self.categorias_form = FormularioCRUD(self.notebook, self, 'Categorías',
            [('nombre', 'Nombre', None), ('descripcion', 'Descripción', None)],
            ('ID', 'Nombre', 'Descripción'), s.categorias,
            lambda d, i: s.guardar_categoria(d['nombre'], d['descripcion'], i), s.eliminar_categoria,
            lambda c: (c.id, c.nombre, c.descripcion))
        self.notebook.add(self.categorias_form, text='Categorías')
        self.equipos_form = FormularioCRUD(self.notebook, self, 'Equipos',
            [('nombre', 'Nombre', None), ('categoria_id', 'Categoría', []),
             ('precio_diario', 'Precio diario', None), ('stock_total', 'Stock total', None),
             ('tipo', 'Tipo (se conserva al editar)', list(CREADORES))],
            ('ID', 'Nombre', 'Categoría', 'Tipo', 'Precio diario', 'Stock total', 'Disponible'),
            s.equipos, self.guardar_equipo, s.eliminar_equipo,
            lambda e: (e.id, e.nombre, e.categoria.nombre, e.tipo, f'{e.precio_diario:.2f}', e.stock_total, e.stock_disponible))
        self.notebook.add(self.equipos_form, text='Equipos')
        ttk.Button(self.equipos_form, text='Ver instrucciones de entrega (Factory Method)',
                   command=lambda: self.ejecutar(self.ver_instrucciones)).pack(anchor='w')
        self.clientes_form = FormularioCRUD(self.notebook, self, 'Clientes',
            [('nombre', 'Nombre', None), ('correo', 'Correo', None), ('telefono', 'Teléfono', None)],
            ('ID', 'Nombre', 'Correo', 'Teléfono'), s.clientes,
            lambda d, i: s.guardar_cliente(d['nombre'], d['correo'], d['telefono'], i), s.eliminar_cliente,
            lambda c: (c.id, c.nombre, c.correo, c.telefono))
        self.notebook.add(self.clientes_form, text='Clientes')

    def guardar_equipo(self, d, identificador):
        return self.servicios.guardar_equipo(d['nombre'], id_opcion(d['categoria_id'], 'categoría'),
            d['precio_diario'], numero(d['stock_total'], 'Stock total'), d['tipo'], identificador)

    def ver_instrucciones(self):
        identificador = self.equipos_form.identificador
        if identificador is None:
            raise ValueError('Selecciona un equipo.')
        equipo = self.equipos_form.objetos[identificador]
        messagebox.showinfo('Preparación de entrega', equipo.instrucciones(), parent=self)

    def crear_arriendos(self):
        marco = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(marco, text='Arriendos y devoluciones')
        ttk.Label(marco, text='Arriendos y devoluciones', style='Titulo.TLabel').pack(anchor='w')
        ttk.Label(marco, text='Cada operación arrienda un tipo de equipo. La devolución es completa.').pack(anchor='w', pady=8)
        formulario = ttk.Frame(marco)
        formulario.pack(fill='x')
        self.arriendo_variables, self.arriendo_widgets = {}, {}
        campos = [('equipo', 'Equipo'), ('cliente', 'Cliente'), ('cantidad', 'Cantidad'),
                  ('inicio', 'Inicio (AAAA-MM-DD)'), ('fin', 'Fin previsto (AAAA-MM-DD)')]
        for i, (clave, etiqueta) in enumerate(campos):
            bloque = ttk.Frame(formulario, padding=(0, 0, 10, 8))
            bloque.grid(row=i // 3, column=i % 3, sticky='ew')
            formulario.columnconfigure(i % 3, weight=1)
            ttk.Label(bloque, text=etiqueta).pack(anchor='w')
            variable = tk.StringVar(value=(date.today().isoformat() if clave in ('inicio', 'fin') else ''))
            widget = (ttk.Combobox(bloque, textvariable=variable, state='readonly')
                      if clave in ('equipo', 'cliente') else ttk.Entry(bloque, textvariable=variable))
            widget.pack(fill='x')
            self.arriendo_variables[clave], self.arriendo_widgets[clave] = variable, widget
        botones = ttk.Frame(marco)
        botones.pack(fill='x', pady=6)
        ttk.Button(botones, text='Registrar arriendo', command=lambda: self.ejecutar(self.arrendar)).pack(side='left')
        ttk.Button(botones, text='Devolver seleccionado', command=lambda: self.ejecutar(self.devolver)).pack(side='left', padx=8)
        self.solo_activos = tk.BooleanVar()
        ttk.Checkbutton(botones, text='Solo activos', variable=self.solo_activos,
                        command=lambda: self.ejecutar(self.refrescar)).pack(side='left', padx=8)
        self.solo_disponibles = tk.BooleanVar()
        ttk.Checkbutton(botones, text='Solo equipos disponibles', variable=self.solo_disponibles,
                        command=lambda: self.ejecutar(self.refrescar)).pack(side='left')
        self.arriendos_vista = tabla(marco, ('ID', 'Equipo', 'Cliente', 'Inicio', 'Fin previsto', 'Cantidad', 'Estado'))
        ttk.Label(marco, text='Sin marcar “Solo activos” se muestra todo el historial.').pack(anchor='w')

    def arrendar(self):
        d = {k: v.get() for k, v in self.arriendo_variables.items()}
        a = self.servicios.registrar_arriendo(id_opcion(d['equipo'], 'equipo'), id_opcion(d['cliente'], 'cliente'),
            fecha(d['inicio']), fecha(d['fin']), numero(d['cantidad'], 'Cantidad'))
        self.estado.set(f'Arriendo #{a.id} registrado. Stock actualizado.')
        self.arriendo_variables['cantidad'].set('')
        self.refrescar()

    def devolver(self):
        seleccion = self.arriendos_vista.selection()
        if not seleccion:
            raise ValueError('Selecciona el arriendo que deseas devolver.')
        if messagebox.askyesno('Devolver', '¿Confirmar la devolución completa?', parent=self):
            self.servicios.devolver(int(seleccion[0]))
            self.refrescar()
            self.estado.set('Devolución registrada. Stock restituido.')

    def crear_informes(self):
        self.informes_marco = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.informes_marco, text='Gráficos')
        ttk.Label(self.informes_marco, text='Gráficos desde la base de datos', style='Titulo.TLabel').pack(anchor='w')
        ttk.Label(self.informes_marco, text='Incluyen activos y devueltos. Cada arriendo cuenta como una operación.').pack(anchor='w', pady=8)
        ttk.Button(self.informes_marco, text='Actualizar gráficos', command=lambda: self.ejecutar(self.dibujar)).pack(anchor='w')
        self.grafico_marco = ttk.Frame(self.informes_marco)
        self.grafico_marco.pack(fill='both', expand=True)
        self.canvas = None

    def dibujar(self):
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()
            self.canvas.figure.clear()
        self.canvas = FigureCanvasTkAgg(crear_figura(self.servicios), master=self.grafico_marco)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

    @staticmethod
    def actualizar_opciones(widget, variable, valores):
        actual = variable.get()
        widget['values'] = valores
        if actual not in valores:
            variable.set('')

    def refrescar(self):
        for formulario in (self.categorias_form, self.equipos_form, self.clientes_form):
            formulario.cargar()
        categorias = [f'{c.id} | {c.nombre}' for c in self.servicios.categorias()]
        self.actualizar_opciones(self.equipos_form.widgets['categoria_id'],
            self.equipos_form.variables['categoria_id'], categorias)
        equipos = [f'{e.id} | {e.nombre} (disponibles: {e.stock_disponible})'
                   for e in self.servicios.equipos(self.solo_disponibles.get())]
        clientes = [f'{c.id} | {c.nombre}' for c in self.servicios.clientes()]
        self.actualizar_opciones(self.arriendo_widgets['equipo'], self.arriendo_variables['equipo'], equipos)
        self.actualizar_opciones(self.arriendo_widgets['cliente'], self.arriendo_variables['cliente'], clientes)
        self.arriendos_vista.delete(*self.arriendos_vista.get_children())
        for a in self.servicios.arriendos(self.solo_activos.get()):
            self.arriendos_vista.insert('', 'end', iid=str(a.id), values=(
                a.id, a.equipo.nombre, a.cliente.nombre, a.fecha_inicio,
                a.fecha_fin_prevista, a.cantidad, a.estado))
        self.dibujar()

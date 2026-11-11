"""Construye una figura desde consultas reales; sirve en Tk y en las pruebas."""
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator


def crear_figura(servicios):
    categorias, equipos = servicios.estadisticas()
    figura = Figure(figsize=(11, 5), dpi=100, layout='constrained')
    for ax, filas, titulo in zip(figura.subplots(1, 2), (categorias, equipos),
                                ('Arriendos por categoría', 'Equipos con más arriendos')):
        ax.set_title(titulo)
        ax.set_xlabel('Número de operaciones')
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        if filas:
            nombres = [f'{nombre} (#{identificador})' for identificador, nombre, _ in filas]
            ax.barh(nombres, [total for _, _, total in filas], color='#287e82')
            ax.invert_yaxis()
        else:
            ax.text(0.5, 0.5, 'Todavía no hay arriendos', transform=ax.transAxes, ha='center')
        ax.spines[['top', 'right']].set_visible(False)
    return figura

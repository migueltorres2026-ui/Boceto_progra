# Evidencia de pruebas y demostración

## Automatizadas

Ejecutadas el 10 de noviembre de 2026 con SQLAlchemy 2.0 y SQLite temporal. Resultado: **8 pruebas correctas**.

| Prueba | Qué comprueba |
|---|---|
| seis_pasos_rubrica_y_persistencia | Stock 5 → 3, rechazo de 4 adicionales, devolución → 5, rechazo duplicado y reapertura |
| crud_y_restricciones_relaciones | Altas, cambios, bajas y bloqueo de registros vinculados |
| invalidos_y_unicos | Cantidades, IDs, fechas, correo, nombre único, precio y stock inválidos |
| stock_al_editar_y_consultas | Editar total conserva unidades activas; filtros disponibles/activos |
| factory_rehidrata_subtipos | Se recuperan Pelota y Bicicleta con comportamiento distinto |
| graficos_cuentan_operaciones_no_unidades | Dos operaciones, aunque sumen tres unidades; figura con dos gráficos |
| rollback_si_falla_insert_despues_de_descontar_stock | Un fallo inducido de INSERT revierte el descuento de stock |
| bd_protege_stock_y_claves_foraneas | SQLite rechaza disponible superior al total y equipo inexistente |

El gráfico [ejemplo generado desde una base temporal](graficos_ejemplo.svg) muestra dos operaciones, de 2 y 1 unidades, como total **2**, no 3. No representa datos fijos de la aplicación: la ventana consulta su propia base cada vez.

## Pendiente en un escritorio con Tkinter

La sesión de preparación no permitió establecer un servidor gráfico, por lo que no se declara verificada visualmente la ventana. Ejecutar y marcar cada paso antes de entregar:

- [ ] Abrir `python main.py`, comprobar todas las pestañas y redimensionar la ventana.
- [ ] Crear categoría y equipo con stock total 5.
- [ ] Crear cliente y arrendar 2 unidades: disponible 3, estado ACTIVO.
- [ ] Intentar arrendar 4 más: rechazo, disponible sigue 3.
- [ ] Devolver el arriendo: disponible 5, estado DEVUELTO.
- [ ] Intentar devolverlo otra vez: rechazo, disponible sigue 5.
- [ ] Editar cada catálogo y verificar el cambio en su tabla.
- [ ] Eliminar un registro sin relaciones; intentar eliminar uno con historial.
- [ ] Escribir texto en cantidad/stock, fechas inválidas, correo repetido y nombre vacío.
- [ ] Ver instrucciones de entrega de pelota y bicicleta.
- [ ] Cerrar, reabrir y comprobar persistencia y ambos gráficos.
- [ ] Probar los filtros Solo activos y Solo equipos disponibles.

## Capturas requeridas para completar la entrega

Guarda capturas reales en esta carpeta y enlázalas en README:

1. Catálogo de equipos con stock visible.
2. Arriendo activo y stock después de descontar.
3. Mensaje de rechazo por stock insuficiente.
4. Historial con devolución y stock repuesto.
5. Pestaña con los dos gráficos.

No reemplaces las capturas por dibujos o resultados inventados. Explica las decisiones con tus palabras y comprueba los pasos frente al docente.

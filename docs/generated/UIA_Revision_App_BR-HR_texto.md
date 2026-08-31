30, agosto, 2026

Revisión técnica de la aplicación Botón Rojo de Alta Resolución (BR-HR)

Objeto y alcance:

Revisión de la aplicación web publicada en mapgisdev.github.io/boton-rojo-chile, contrastada con el documento «BR-HR. Botón Rojo de Alta Resolución - Chile» y con la metodología del Botón Rojo oficial de GEPRIF. La revisión se realizó el 30 de agosto de 2026 e incluyó el recorrido de la interfaz, la inspección del código de la aplicación, la descarga y el análisis de todos sus archivos de datos, y la lectura de la consola y del tráfico de red del navegador. Todo lo que se afirma aquí fue verificado sobre la versión publicada ese día; donde hay interpretación, se dice.

El propósito del BR-HR —sustituir una regla booleana rígida por un índice continuo y bajar la unidad de análisis por debajo de la comuna— es acertado y ataca dos problemas reales. La arquitectura elegida, con hexágonos H3 y separación entre línea base, modelo continuo y calibración, es la correcta. Lo que sigue no cuestiona el diseño, sino el estado de la implementación publicada, que hoy no permite sostener las conclusiones que la interfaz muestra.

Resumen para la decisión:

Se identificaron veintidós hallazgos. Tres impiden usar la aplicación como está: el pronóstico del día no contiene valores modelados, el padrón comunal está duplicado y el denominador con que se calculan los porcentajes es una constante. Otros ocho afectan la validez metodológica de lo que se muestra, cinco son defectos técnicos y seis son problemas de comprensión para el usuario final. Ninguno es irreparable, y varios se corrigen en horas.

1.  Hallazgos bloqueantes

1.1  El pronóstico del día no trae valores modelados. El archivo h3_res7.geojson que alimenta el mapa de hoy contiene 15.820 hexágonos, y los 15.820 tienen exactamente el mismo valor: probabilidad de ignición 0,05 y clasificación VERDE, sin una sola excepción entre Arica y Magallanes. Una constante nacional no es la salida de un modelo meteorológico. Es invierno y el peligro real es bajo, pero un cálculo sobre GFS produciría variación entre el altiplano, el valle central y la Patagonia. Mientras esto no cambie, el modo «Pronóstico Hoy» no está operativo, aunque la interfaz lo presente como tal.

1.2  Tres conteos distintos de comunas en la misma carga. El límite comunal (comunas_chile.geojson) trae 346 comunas, que es la cifra correcta. El archivo que alimenta la tabla y los indicadores (communes.json) trae 411 filas para 318 comunas únicas: 73 comunas están duplicadas, y Cauquenes, Cholchol, Cobquecura y Ninhue aparecen cuatro veces cada una. El resumen del día (summary.json) declara 318. La consecuencia es visible en pantalla: la tabla lista Buin tres veces y Arauco dos, y los indicadores del encabezado cuentan sobre un padrón inflado y a la vez incompleto, porque faltan 28 comunas.

1.3  El denominador de los porcentajes es una constante. El campo total_hexagons vale 50 para todas las comunas en el archivo de hoy y 45 para todas en los escenarios históricos. Con hexágonos H3 de resolución 7, de unas 516 hectáreas, eso equivale a afirmar que cada comuna de Chile tiene entre 23.000 y 26.000 hectáreas. Colchane tiene 401.560 y Providencia menos de 1.500. Cualquier porcentaje que se derive del cociente entre hexágonos rojos y totales es aritmética sobre un denominador ficticio. El campo pct_superficie_roja parece calcularse por otra vía, porque toma valores que ese cociente no podría producir, pero entonces los dos campos se contradicen y no hay forma de saber cuál manda.

2.  Hallazgos metodológicos

2.1  El campo de horas críticas solo toma dos valores. En los 11.981 hexágonos del escenario del 3 de febrero de 2023, horas_br vale 2 en 4.277 casos y 4 en 7.704. No aparece ningún 1, 3 ni 5. Si la ventana de evaluación tiene cinco pasos horarios, el campo debería recorrer 1 a 5. Además la partición coincide casi exactamente con la clasificación de alerta —4.354 amarillos y 7.627 rojos—, de modo que horas_br no aporta información propia: es una reetiquetación. Cabe señalar que el propio código de la aplicación contiene una regla idéntica, que asigna 4 horas si el incendio superó 100 hectáreas y 2 si no.

2.2  Sobreactivación severa en el escenario histórico. El 3 de febrero de 2023 la aplicación marca 106 comunas en alerta roja y 114 en amarilla: 220 de 346, el 63,6 % del país. De ellas, 44 superan el 90 % de su superficie en condición Botón Rojo y 8 llegan al 100 %. Ese día hubo megaincendios reales, pero el Botón Rojo oficial no activa a esa escala. Si casi todo el territorio se enciende, el índice deja de discriminar, que es exactamente el problema inverso al «efecto acantilado» que el BR-HR se propone corregir. Antes de presentar este escenario como validación, hay que contrastar comuna a comuna contra lo que CONAF declaró ese día.

La distribución es bimodal: o la comuna no tiene nada, o tiene casi todo. Un índice continuo debería producir un gradiente, no dos modas.

2.3  El indicador «Territorio en riesgo» está mal rotulado. Muestra 48,33 % para ese día, que es el cociente entre celdas rojas y celdas combustibles (16.062 de 33.237). No es el 48 % del territorio nacional. Rotulado así, en una vocería o en una minuta, el número se lee como algo mucho más grave de lo que es.

2.4  Los conteos de celdas no cuadran entre archivos. El resumen declara 33.237 celdas totales; la tabla de correspondencia entre comunas y hexágonos suma 33.876; la malla publicada hoy trae 15.820; y el escenario histórico declara 16.062 celdas rojas mientras su propio archivo de hexágonos contiene 7.627 marcados como rojo. Son cuatro cifras para lo que debería ser una sola.

2.5  La correspondencia entre comunas y hexágonos tiene más claves que comunas. El archivo commune_h3_lookup.json tiene 636 entradas cuando Chile tiene 346 comunas. Conviene revisar si arrastra códigos territoriales antiguos o registros repetidos.

2.6  Existe un sintetizador que deduce el pronóstico de los incendios ocurridos. El código incluye una función que, para una fecha sin archivos precalculados, fabrica la alerta a partir de los focos observados: asigna 35 % más 12 % por cada foco registrado en la comuna, fija la probabilidad de ignición en 0,82 y reparte las horas críticas según la superficie quemada. Hoy no se ejecuta, porque los siete escenarios del selector tienen sus archivos. Pero se activaría con cualquier fecha nueva que se agregue sin ellos, y en ese caso la aplicación mostraría un pronóstico deducido de lo que ya se quemó, es decir, un acierto garantizado por construcción. Conviene eliminarla o dejarla claramente marcada como demostración.

2.7  Los focos satelitales se muestran sin filtro. Los 23 focos FIRMS de hoy tienen potencia radiativa entre 0,35 y 11,07 megawatts, e incluyen detecciones nocturnas en Magallanes y en el interior de Antofagasta. En pleno invierno, y con esas potencias, lo más probable es que correspondan a fuentes industriales o a falsos positivos, no a vegetación ardiendo. La capa los rotula a todos como «Foco Activo Satelital» sin umbral de potencia ni de confianza.

2.8  Nomenclatura regional inconsistente entre archivos. El archivo de hoy usa «Biobío», «Metropolitana» y «Araucanía»; los escenarios históricos usan «Región del Bío-Bío», «Región Metropolitana de Santiago» y «Región de La Araucanía». Además aparece «Zona sin demarcar» como región. Cualquier filtro o agregación por región dará resultados distintos según el escenario cargado. Nótese que la grafía oficial es Biobío, sin tilde ni guion.

3.  Hallazgos técnicos

4.  Comprensión para el usuario final

Este bloque importa más de lo que parece: la aplicación está pensada para apoyar decisiones operativas, y quien la usa en una jefatura provincial o en un municipio no tiene por qué conocer la metodología.

—  Sin explicación del método. La interfaz no menciona en ningún lugar la ventana de la tarde, la probabilidad de ignición, la humedad del combustible ni la metodología. Nada explica qué se está mirando ni de dónde sale.

—  Sin marca temporal. No hay fecha ni hora de actualización visible, ni indicación de a qué día del pronóstico corresponde el mapa. El usuario no puede saber si está viendo hoy, mañana o el quinto día.

—  Leyenda ambigua. La leyenda comunal usa dos expresiones distintas para la misma cosa: «≥ 30 % de superficie en condición Botón Rojo» y «10 % a 29 % de superficie en riesgo severo». Y en ningún caso aclara que el denominador es la superficie combustible y no la superficie total de la comuna, que es justamente la distinción que el BR-HR quiere resolver.

—  Capas sin leyenda. Las capas de hexágonos, los mapas de calor y los focos satelitales no tienen leyenda propia. El usuario ve colores sin escala.

—  Tabla truncada sin aviso. La tabla muestra treinta y cinco filas. Con 220 comunas en alerta en el escenario de 2023, queda oculta la mayoría, y no hay indicación de que la lista está recortada.

—  Primera pantalla vacía de información. En el arranque de hoy la tabla lista las comunas en orden alfabético, todas con 0,0 %. Es la primera pantalla que ve el usuario y no comunica nada.

5.  Qué corregir, en orden

El orden responde a dependencia, no a esfuerzo: sin resolver lo primero, lo demás no se puede evaluar.

6.  Observaciones sobre el documento de respaldo

Tres puntos del resumen conviene precisarlos antes de que circule. Primero, la base histórica: el documento indica 68.546 registros, y el archivo que la aplicación carga tiene 68.187, con cuatro registros sin fecha. La diferencia es menor pero conviene explicarla. Segundo, el documento describe los umbrales del modelo M1 —probabilidad de ignición igual o superior a 60 con humedad del combustible igual o inferior a 10 para la alerta roja, y probabilidad entre 40 y 60 para la amarilla—, pero la aplicación clasifica por porcentaje de superficie comunal, con cortes en 30 % y 10 %. Son dos reglas distintas conviviendo, y el documento no explica cómo se articulan. Tercero, el documento menciona ERA5-Land para la reconstrucción histórica y GFS para la operación; en el código publicado no hay rastro de ninguna de las dos, porque la aplicación solo consume archivos ya calculados. Eso es razonable en una arquitectura separada, pero entonces conviene documentar dónde vive el motor de cálculo y cómo se auditan sus salidas.

Una observación de fondo, dicha con franqueza porque es el punto que más valor tiene: el BR-HR promete resolver el efecto acantilado y la dilución espacial, y en el diseño lo logra. Pero la evidencia que hoy muestra la aplicación no lo demuestra, y en el escenario de 2023 sugiere haber cambiado un problema por otro. La forma de zanjarlo no es afinar la interfaz, sino publicar la validación que el propio documento anuncia: entrenamiento con 2014-2022, prueba ciega con 2022-2024, y las métricas de acierto y falsa alarma sobre la temporada reservada. Con esas cifras, el BR-HR se sostiene solo.

Trazabilidad de la revisión:

Aplicación revisada: mapgisdev.github.io/boton-rojo-chile, versión rotulada «2026», el 30 de agosto de 2026. Se inspeccionaron el archivo app.js (1.132 líneas), los archivos de datos comunas_chile.geojson, communes.json, summary.json, h3_res7.geojson, h3_centroids.json, commune_h3_lookup.json, firms_latest.json e incendios_historicos_all.json, y los archivos precalculados de los siete escenarios históricos del selector. Se registraron la consola y las peticiones de red del navegador. Los conteos y distribuciones citados se calcularon sobre esos archivos en el momento de la revisión. Documento de respaldo: «BR-HR. Botón Rojo de Alta Resolución - Chile», sin fecha. Referencia metodológica: informe UIA sobre la metodología del Botón Rojo oficial, 27 de agosto de 2026.

Gravedad | N° | Qué significa

Bloqueante | 3 | Lo que la aplicación muestra hoy no puede interpretarse como resultado del modelo.

Metodológico | 8 | El resultado se muestra, pero su construcción no resiste una auditoría técnica.

Técnico | 5 | No impide el uso, pero degrada el rendimiento y la mantenibilidad.

Comprensión | 6 | Un usuario no experto no puede saber qué está mirando.

Superficie comunal en condición Botón Rojo | N° de comunas | Participación

0 % | 188 | 54,3 %

Sobre 0 % y bajo 10 % | 28 | 8,1 %

10 % a 29 % | 24 | 6,9 %

30 % a 59 % | 17 | 4,9 %

60 % a 89 % | 37 | 10,7 %

90 % a 99,9 % | 44 | 12,7 %

100 % | 8 | 2,3 %

Hallazgo | Detalle verificado | Corrección

Diez errores 404 en cada carga | La aplicación pide primero rutas absolutas del tipo /data/r2_export/…, que en GitHub Pages resuelven a la raíz del dominio y no al subdirectorio del proyecto. Una función de respaldo reintenta con la ruta relativa, que sí existe, de modo que la aplicación funciona, pero arrastra una cascada de errores en cada arranque. | Usar rutas relativas o una base configurable.

Llamadas a una API que no existe | El código define la base de la API como el origen del sitio y llama a /api/v1/forecast/latest/summary y a /api/v1/firms/active-points. En un sitio estático siempre responden 404. Es residuo de un despliegue con servidor. | Retirar las llamadas o condicionarlas a que exista un backend.

La capa de mapa de calor no tiene datos | El archivo h3_centroids.json está vacío: cero elementos. La casilla «Mapa de Calor: Alerta Botón Rojo» se puede activar, pero no dibuja nada y no avisa por qué. | Poblar el archivo o deshabilitar la casilla con un mensaje.

Advertencias de la biblioteca de mapas | MapLibre emite «Expected value to be of type number, but found null» durante la carga: alguna expresión de estilo lee una propiedad que llega nula. | Añadir un valor por defecto en la expresión.

El resumen y el tablero no coinciden | El resumen del día declara dos comunas en alerta amarilla; el tablero muestra cero, porque el indicador se recalcula desde la lista de comunas en vez de leerlo del resumen. | Definir una única fuente de verdad para los indicadores.

Prioridad | Acción | Efecto

1 | Regenerar la malla del día con valores modelados reales, o mostrar un aviso explícito mientras no los haya. | Devuelve sentido al modo «Pronóstico Hoy».

2 | Deduplicar el padrón comunal contra las 346 comunas del límite oficial y unificar los tres conteos. | Corrige la tabla, los indicadores y cualquier cifra que se cite.

3 | Calcular total_hexagons por comuna a partir de la correspondencia real con la malla H3. | Vuelve interpretable el porcentaje de superficie.

4 | Rotular el indicador como porcentaje de superficie combustible, no de territorio. | Evita un error de comunicación en vocerías.

5 | Reconstruir horas_br como el conteo real de pasos horarios, de 1 a 5. | Recupera información que hoy se pierde.

6 | Contrastar el escenario de 2023 contra las comunas que CONAF declaró ese día y recalibrar los umbrales. | Mide la sobreactivación y la corrige con evidencia.

7 | Eliminar el sintetizador basado en focos observados, o marcarlo como demostración. | Evita que una fecha nueva muestre un acierto fabricado.

8 | Filtrar los focos FIRMS por potencia radiativa y confianza. | Deja de mostrar como incendios lo que no lo es.

9 | Corregir rutas, retirar las llamadas a la API inexistente y poblar o deshabilitar la capa de calor. | Limpia la consola y acelera la carga.

10 | Agregar marca temporal, nota metodológica breve y leyendas para todas las capas. | Hace la aplicación usable por quien no participó en su construcción.
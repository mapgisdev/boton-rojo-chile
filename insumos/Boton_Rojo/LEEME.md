# Botón Rojo — documentación y réplica

Carpeta de trabajo de la Unidad de Información y Análisis (UIA) de CONAF.
Reúne la reconstrucción de la metodología del índice **Botón Rojo** de GEPRIF, el
código para replicarlo y la arquitectura para operarlo con software libre.

Actualizado el 27 de agosto de 2026.

---

## Qué hay aquí

### Documentos

| Archivo | Qué contiene |
|---|---|
| `UIA_Metodologia_Boton_Rojo_CONAF.docx` | **Empezar por aquí.** Informe institucional de nueve páginas: metodología completa, fórmulas, umbrales, insumos, tablas de reclasificación, verificaciones empíricas, limitaciones y ruta de replicación. |
| `UIA_Metodologia_Boton_Rojo_CONAF.pdf` | El mismo informe, para compartir sin depender de Word. |
| `Arquitectura_Boton_Rojo_Open_Source.html` | Arquitectura de referencia en software libre: equivalencias frente a Earth Engine y ArcGIS Online, stack capa por capa con versiones y licencias, trampas verificadas, dimensionamiento y ruta de migración. Se abre en cualquier navegador. |
| `matriz_probabilidad_ignicion.xlsx` | La matriz reconstruida de 288 celdas, en tres variantes comparables, más las vistas expuesto y sombreado. |
| `matriz_probabilidad_ignicion.csv` | La misma matriz en formato plano, para consumir desde código. |

### Código

| Archivo | Qué hace |
|---|---|
| `codigo/nucleo.py` | Algoritmo puro en numpy: humedad del combustible, reclasificaciones, matriz de probabilidad de ignición y regla de activación. Ejecutarlo corre cuatro verificaciones automáticas. |
| `codigo/boton_rojo_gee.js` | Réplica en Google Earth Engine, el mismo entorno en que CONAF lo produce. Se pega directo en el Code Editor. |
| `codigo/pipeline.py` | Réplica fuera de Earth Engine: descarga el GFS desde NOMADS, calcula y agrega por comuna. |
| `codigo/conaf_api.py` | Cliente de los servicios REST de CONAF: descarga del producto oficial, cosecha diaria y calibración empírica de la matriz. |
| `codigo/publicar.py` | Publicación abierta: COG, ítems STAC en pgstac y tabla comunal en PostGIS. |
| `codigo/generar_matriz.py` | Regenera la matriz en Excel, CSV y JavaScript. |
| `codigo/generar_informe.py` | Regenera el informe Word con el formato institucional. |
| `codigo/despliegue/` | Pila de servicios y unidades systemd para operar el índice sin plataformas propietarias. |

---

## Cómo empezar

```bash
cd codigo
pip install -r requirements.txt
python nucleo.py            # verificaciones del algoritmo
python generar_matriz.py    # regenera la matriz
```

Para consultar el producto oficial vigente de CONAF:

```bash
python conaf_api.py br --salida boton_rojo_vigente.xlsx
python conaf_api.py cosechar          # archiva la corrida del día
```

Para levantar la pila de publicación abierta:

```bash
cd codigo/despliegue
cp env.ejemplo .env         # completar claves y rutas
podman-compose up -d
```

---

## Tres advertencias que conviene no perder de vista

**La matriz de probabilidad de ignición es una reconstrucción.** CONAF no la
publica, y el informe técnico de NASA DEVELOP señala que sus valores fueron
determinados usando la temporada de incendios chilena 2016-2017 como referencia.
La versión incluida aquí se genera con la ecuación de Rothermel y BehavePlus, que
reproduce la tabla del NWCG con un error medio de 0,83 puntos porcentuales, pero
**no es la matriz de CONAF**. Antes de cualquier uso operativo hay que pedirla al
DEI/GEPRIF (dei.geprif@conaf.cl) o calibrarla con `conaf_api.calibrar_matriz()`.

**No existe una serie histórica pública del Botón Rojo.** El servicio publicado
contiene solo la ventana vigente de cinco días y se sobrescribe en cada corrida.
Quien la necesite debe cosecharla a diario desde ahora, o solicitarla al DEI.

**Las condiciones de Earth Engine cambiaron en abril de 2026.** Hay cuotas
mensuales para el uso no comercial, y la documentación de Google señala que los
usuarios de gobierno con fines operacionales deben usar cuenta comercial de pago.
Conviene medir el consumo real en EECU-hora y postular al nivel Partner —ambas
cosas cuestan cero— antes de decidir nada sobre migración.

---

## Cita

Los datos del Botón Rojo son de uso público; su utilización debe citar a CONAF
como fuente, conforme a la licencia declarada por el Departamento de Desarrollo e
Investigación de la Gerencia de Protección contra Incendios Forestales.

Este material es un documento de trabajo de la UIA. No constituye una decisión
institucional ni compromete a GEPRIF.

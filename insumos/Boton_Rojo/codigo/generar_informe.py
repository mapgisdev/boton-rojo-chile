# -*- coding: utf-8 -*-
"""Genera el informe institucional CONAF sobre la metodología del Botón Rojo."""

import os
import re
import shutil
import zipfile

PLANTILLA = "/root/.claude/skills/synced/conaf-document/assets/plantilla_conaf.docx"
TRABAJO = "/home/claude/boton_rojo/_trabajo"
SALIDA = "/home/claude/boton_rojo/UIA_Metodologia_Boton_Rojo_CONAF.docx"

AZUL = "002060"
FUENTE = 'w:ascii="Open Sans" w:cs="Open Sans" w:eastAsia="Open Sans" w:hAnsi="Open Sans"'


def esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&#x201D;"))


def fecha(dia, mes, anio):
    return f'''<w:p><w:pPr><w:spacing w:after="0" w:before="0" w:line="240" w:lineRule="auto"/>
<w:ind w:left="0" w:right="0" w:firstLine="0"/><w:jc w:val="right"/></w:pPr>
<w:r><w:rPr><w:rFonts w:ascii="Verdana" w:cs="Verdana" w:eastAsia="Verdana" w:hAnsi="Verdana"/>
<w:b w:val="1"/><w:bCs w:val="1"/><w:color w:val="{AZUL}"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr>
<w:t xml:space="preserve">{dia}, {mes}, {anio}</w:t></w:r></w:p>'''


def titulo(t):
    return f'''<w:p><w:pPr><w:shd w:fill="ffffff" w:val="clear"/>
<w:spacing w:after="225" w:before="0" w:line="240" w:lineRule="auto"/>
<w:ind w:left="0" w:right="-142" w:firstLine="0"/><w:jc w:val="center"/></w:pPr>
<w:r><w:rPr><w:rFonts {FUENTE}/><w:b w:val="1"/><w:bCs w:val="1"/>
<w:color w:val="{AZUL}"/><w:sz w:val="40"/><w:szCs w:val="40"/></w:rPr>
<w:t xml:space="preserve">{esc(t)}</w:t></w:r></w:p>'''


def _run(t, negrita=False, sz=21):
    b = "1" if negrita else "0"
    return (f'<w:r><w:rPr><w:rFonts {FUENTE}/><w:b w:val="{b}"/><w:bCs w:val="{b}"/>'
            f'<w:color w:val="{AZUL}"/><w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(t)}</w:t></w:r>')


def parrafo(*trozos, sz=21, alineacion="both", espacio=225):
    """Cada trozo es str (normal) o (texto, True) para negrita."""
    runs = ""
    for trozo in trozos:
        if isinstance(trozo, tuple):
            runs += _run(trozo[0], trozo[1], sz)
        else:
            runs += _run(trozo, False, sz)
    return (f'<w:p><w:pPr><w:shd w:fill="ffffff" w:val="clear"/>'
            f'<w:spacing w:after="{espacio}" w:before="0" w:line="276" w:lineRule="auto"/>'
            f'<w:ind w:left="0" w:right="-142" w:firstLine="0"/>'
            f'<w:jc w:val="{alineacion}"/></w:pPr>{runs}</w:p>')


def seccion(t):
    return parrafo((t, True))


def vinieta(t, negrita_hasta=None):
    """Párrafo con sangría y guion, opcionalmente con inicio en negrita."""
    if negrita_hasta:
        runs = _run("—  " + negrita_hasta, True) + _run(t)
    else:
        runs = _run("—  " + t)
    return (f'<w:p><w:pPr><w:shd w:fill="ffffff" w:val="clear"/>'
            f'<w:spacing w:after="80" w:before="0" w:line="276" w:lineRule="auto"/>'
            f'<w:ind w:left="284" w:right="-142" w:hanging="284"/>'
            f'<w:jc w:val="both"/></w:pPr>{runs}</w:p>')


def vacio():
    return ('<w:p><w:pPr><w:spacing w:after="0" w:before="0" w:line="240" '
            'w:lineRule="auto"/></w:pPr>'
            '<w:r><w:rPr><w:rtl w:val="0"/></w:rPr></w:r></w:p>')


def _celda(texto, ancho, negrita=False, relleno=None, sz=17, alineacion="left"):
    shd = f'<w:shd w:val="clear" w:fill="{relleno}"/>' if relleno else ""
    return (f'<w:tc><w:tcPr><w:tcW w:w="{ancho}" w:type="dxa"/>{shd}'
            f'<w:tcMar><w:top w:w="60" w:type="dxa"/><w:bottom w:w="60" w:type="dxa"/>'
            f'<w:left w:w="90" w:type="dxa"/><w:right w:w="90" w:type="dxa"/></w:tcMar>'
            f'<w:vAlign w:val="center"/></w:tcPr>'
            f'<w:p><w:pPr><w:spacing w:after="0" w:before="0" w:line="240" w:lineRule="auto"/>'
            f'<w:jc w:val="{alineacion}"/></w:pPr>{_run(texto, negrita, sz)}</w:p></w:tc>')


def tabla(cabecera, filas, anchos, alineaciones=None, sz=17):
    alineaciones = alineaciones or ["left"] * len(cabecera)
    bordes = ('<w:tblBorders>'
              + "".join(f'<w:{b} w:val="single" w:sz="4" w:space="0" w:color="B4C6E7"/>'
                        for b in ("top", "left", "bottom", "right", "insideH", "insideV"))
              + '</w:tblBorders>')
    xml = (f'<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/>'
           f'<w:tblW w:w="{sum(anchos)}" w:type="dxa"/>{bordes}'
           f'<w:tblLayout w:type="fixed"/></w:tblPr><w:tblGrid>'
           + "".join(f'<w:gridCol w:w="{a}"/>' for a in anchos) + '</w:tblGrid>')
    xml += '<w:tr><w:trPr><w:tblHeader/></w:trPr>' + "".join(
        _celda(c, a, True, "DDE5F3", sz, al)
        for c, a, al in zip(cabecera, anchos, alineaciones)) + '</w:tr>'
    for fila in filas:
        xml += '<w:tr>' + "".join(
            _celda(str(c), a, False, None, sz, al)
            for c, a, al in zip(fila, anchos, alineaciones)) + '</w:tr>'
    return xml + '</w:tbl>' + parrafo("", espacio=60)


# ---------------------------------------------------------------------------
# Contenido
# ---------------------------------------------------------------------------

cuerpo = []
A = cuerpo.append

A(fecha(27, "agosto", 2026))
A(vacio())
A(titulo("Botón Rojo de CONAF: metodología de cálculo y ruta de replicación"))
A(vacio())

A(seccion("Objeto:"))
A(parrafo(
    "Este informe reconstruye la metodología con que la Gerencia de Protección contra "
    "Incendios Forestales (GEPRIF) calcula el índice Botón Rojo, e identifica los insumos "
    "concretos que se requieren para replicarlo. A lo largo del documento se distingue de "
    "manera explícita entre tres niveles de evidencia: lo ",
    ("confirmado", True),
    " por fuente institucional, lo ",
    ("verificado empíricamente", True),
    " contra los servicios de datos que CONAF publica, y lo ",
    ("reconstruido", True),
    " por inferencia técnica. Esa distinción es deliberada: un solo componente de la cadena "
    "de cálculo no está publicado, y es precisamente el que determina el resultado."))
A(vacio())

A(seccion("1.  Qué es el Botón Rojo y quién lo produce"))
A(parrafo(
    "La definición institucional vigente, contenida en los metadatos del ítem oficial de "
    "CONAF en ArcGIS Online, es la siguiente: “Botón Rojo es una herramienta que permite "
    "identificar aquellos territorios que tendrían un mayor potencial de ignición y "
    "propagación de incendios forestales, lo que se traduce en un escenario complejo para el "
    "control, sobre todo existiendo simultaneidad de incidentes”."))
A(parrafo(
    "Fue creado el año 2018 por el Departamento de Desarrollo e Investigación (DEI) de "
    "GEPRIF. La versión vigente fue lanzada el año 2023 y se genera sobre Google Earth Engine, "
    "publicándose en ArcGIS Online. La unidad operativa responsable es la Sección de Análisis "
    "y Predicción de Incendios Forestales (SAPIF); el correo institucional declarado en los "
    "metadatos es dei.geprif@conaf.cl."))
A(parrafo(
    "Conviene precisar su naturaleza jurídica, porque la prensa la confunde de manera "
    "sistemática: el Botón Rojo ",
    ("no es una alerta", True),
    ". Es un insumo técnico de pronóstico que CONAF entrega al Sistema de Protección Civil, y "
    "sobre cuyo informe SENAPRED funda la declaración de Alerta Temprana Preventiva conforme a "
    "la Ley N° 21.364. Su horizonte es de cinco días, con situación diaria y mapas de "
    "pronóstico publicados lunes, miércoles y viernes."))
A(vacio())

A(seccion("2.  Regla de activación"))
A(parrafo(
    "La condición de Botón Rojo se asigna a los territorios donde se cumplen ",
    ("simultáneamente", True),
    " dos criterios, calculados a partir del último pronóstico meteorológico GFS de NOAA para "
    "la ventana horaria de la tarde:"))
A(vinieta("probabilidad de ignición mayor o igual a 70 %, y", ""))
A(vinieta("velocidad del viento mayor o igual a 20 km/h.", ""))
A(parrafo(
    "Existe una discrepancia documental sobre la ventana horaria: los metadatos del ítem "
    "ArcGIS indican “entre las 14:00 y 18:00 horas”, mientras que el sitio institucional "
    "señala “entre las 14:00 y las 18:59 hrs”. ",
    ("La lectura correcta es 14:00–18:59", True),
    ", y queda zanjada por los propios datos: el campo horas del servicio publicado recorre "
    "los valores 1 a 5, es decir cinco pasos horarios (14, 15, 16, 17 y 18)."))
A(vacio())

A(seccion("3.  Insumos concretos"))
A(parrafo(
    "Los cuatro insumos son abiertos y gratuitos. Ninguno exige convenio, licencia comercial "
    "ni acceso privilegiado, lo que hace la réplica plenamente factible con recursos propios."))
A(tabla(
    ["Insumo", "Fuente exacta", "Resolución", "Uso en la cadena"],
    [["Pronóstico meteorológico",
      "NOAA GFS 0,25°. En Earth Engine: ImageCollection NOAA/GFS0P25",
      "27.830 m; corridas cada 6 h; paso horario hasta 120 h",
      "Temperatura, humedad relativa y componentes u y v del viento"],
     ["Topografía",
      "SRTM 90 m. En Earth Engine: CGIAR/SRTM90_V4",
      "90 m",
      "Sombreado topográfico (hillshade)"],
     ["Cobertura de suelo",
      "ESA WorldCover v200 (2021). En Earth Engine: ESA/WorldCover/v200",
      "10 m",
      "Máscara de superficie combustible"],
     ["División comunal",
      "División Política Administrativa 2023 (SUBDERE, IGM, INE)",
      "1:50.000",
      "Agregación y comunicación del resultado"]],
    [1900, 3050, 2000, 2500]))
A(parrafo(
    "Sobre la cobertura de suelo cabe una precisión. CONAF declara usar “la cobertura "
    "Landcover 2021 generada por el programa europeo Copernicus”, filtrando “bosques, "
    "matorrales, pastizales, cultivos agrícolas y humedales”. El producto Copernicus Global "
    "Land Cover llega solo hasta 2019, de modo que la atribución es imprecisa: la enumeración "
    "corresponde exactamente, y en orden de código ascendente, a cinco clases de ",
    ("ESA WorldCover v200 (2021)", True),
    " —10 bosques, 20 matorrales, 30 pastizales, 40 cultivos agrícolas y 90 humedales "
    "herbáceos—, producto de la ESA construido íntegramente con datos Sentinel del programa "
    "Copernicus. Esos son los cinco códigos que debe usar la máscara."))
A(vacio())

A(seccion("4.  Cadena de cálculo"))
A(parrafo(
    "La secuencia completa quedó documentada en el proyecto NASA DEVELOP 2022 “Chile "
    "Disasters: Automating Wildfire Risk and Occurrence Mapping in Google Earth Engine”, "
    "ejecutado en conjunto con CONAF con el objeto expreso de migrar a Earth Engine el modelo "
    "que CONAF operaba en ArcGIS Pro. Ese informe es, hasta donde alcanza la revisión "
    "realizada, la documentación técnica más profunda que existe sobre el método, y no es de "
    "CONAF sino de su contraparte."))
A(parrafo(("Paso 1. Humedad del combustible fino muerto.", True),
          " Regresión lineal desarrollada por la Universidad de Chile, con la humedad relativa "
          "expresada de 1 a 100 y la temperatura en grados Celsius:"))
A(parrafo("HCFM  =  0,297374  +  0,262 · HR  −  0,00982 · T",
          alineacion="center", espacio=140))
A(parrafo(("Paso 2. Velocidad del viento.", True),
          " Módulo del vector de viento a 10 m, convertido de m/s a km/h:"))
A(parrafo("V  =  √( u² + v² ) · 3,6", alineacion="center", espacio=140))
A(parrafo(("Paso 3. Sombreado.", True),
          " Sombreado topográfico calculado sobre el modelo de elevación SRTM con azimut 313 "
          "y altura solar 60 grados, reclasificado a dos estados: sombreado o expuesto."))
A(parrafo(("Paso 4. Clave compuesta.", True),
          " Las tres variables se reclasifican y se suman para formar un entero que actúa como "
          "índice de una tabla de consulta. La estructura de la clave es deliberada: los "
          "millares codifican la humedad del combustible, las centenas el sombreado y las "
          "unidades la temperatura."))
A(parrafo("clave  =  ReclassC(HCFM)  +  ReclassG(sombreado)  +  ReclassA(T)",
          alineacion="center", espacio=140))
A(parrafo(
    "Así, una celda con humedad del combustible entre 4 % y 5 %, expuesta al sol y con "
    "temperatura entre 30 °C y 35 °C produce la clave 5.000 + 100 + 8 = 5.108."))
A(parrafo(("Paso 5. Probabilidad de ignición.", True),
          " La clave se traduce a un porcentaje mediante una matriz de 288 valores. Este es el "
          "único eslabón no publicado, y se trata en el apartado 6."))
A(parrafo(("Paso 6. Activación y acumulación horaria.", True),
          " Se evalúa la regla en cada uno de los cinco pasos horarios de la ventana de tarde. "
          "En el modelo original la operación se expresa como la suma de dos criterios "
          "binarios, y la condición se cumple cuando esa suma vale 2. El número de pasos "
          "horarios que la cumplen queda registrado en el campo horas."))
A(parrafo(("Paso 7. Máscara y agregación.", True),
          " El resultado se enmascara por superficie combustible y se agrega a nivel comunal, "
          "reportando la superficie en hectáreas por comuna, día y número de horas."))
A(vacio())

A(seccion("5.  Tablas de reclasificación"))
A(parrafo(
    "Las siete tablas provienen del apéndice del informe técnico de NASA DEVELOP y se "
    "reproducen aquí de manera literal. Dos de ellas —C y E— pudieron verificarse de forma "
    "independiente, porque coinciden exactamente con las leyendas de las capas que CONAF "
    "publica en línea."))
A(tabla(
    ["Tabla", "Variable de entrada", "Reclasificación", "Verificación"],
    [["A", "Temperatura (°C)",
      "<0→1; 0–5→2; 5–10→3; 10–15→4; 15–20→5; 20–25→6; 25–30→7; 30–35→8; 35–40→9",
      "Coincide con la leyenda de la capa pública TP"],
     ["B", "HCFM (%), para visualización",
      "0–2→1; 2–4→2; 4–6→3; 6–8→4; 8–10→5; 10–12→6; 12–15→7; 15–20→8; 20–25→9; >25→10",
      "Coincide exactamente con la leyenda de la capa pública HC"],
     ["C", "HCFM (%), clave de consulta",
      "≤2→2.000; 2–3→3.000; … ; 15–16→16.000; 16–30→17.000. Equivale a 1.000 · techo(HCFM), "
      "acotado entre 2.000 y 17.000",
      "Indexa las dieciséis filas de humedad de la tabla NFDRS"],
     ["D", "Probabilidad de ignición (%)",
      "Deciles: 0–10→1; 10–20→2; … ; 90–100→10",
      "Coincide con la leyenda de la capa pública PI"],
     ["E", "Viento (km/h)",
      "0–3→1 (calmo); 3–5→2; 5–10→3; 10–15→4; 15–20→5; 20–25→6; 25–30→7; >30→8",
      "Coincide exactamente con la leyenda de la capa pública VV"],
     ["F", "Viento (km/h), binario",
      "<20→0; ≥20→1",
      "Es el umbral de viento del Botón Rojo"],
     ["G", "Sombreado (hillshade)",
      "0–123,5→200 (sombreado); 123,5–247→100 (expuesto)",
      "Aporta las centenas de la clave compuesta"]],
    [700, 2100, 4550, 2100]))
A(parrafo(
    "Un detalle con consecuencias operativas: las tablas A y C no cubren todo el dominio "
    "posible. La tabla A se detiene en 40 °C y la tabla C en 30 % de humedad del combustible. "
    "En la herramienta Reclassify de ArcGIS, y salvo configuración explícita en contrario, un "
    "valor fuera de rango se convierte en dato nulo. Esto significa que ",
    ("durante una ola de calor con temperaturas sobre 40 °C el píxel podría quedar fuera del "
     "índice justo cuando el riesgo es máximo", True),
    ". La tabla F presenta el mismo problema en el extremo opuesto: su rango parte en 0,0001, "
    "de modo que una celda con viento exactamente nulo queda sin valor. Son bordes que "
    "cualquier réplica debe tratar explícitamente, y que conviene verificar en el modelo "
    "vigente de CONAF."))
A(vacio())

A(seccion("6.  La matriz de probabilidad de ignición: el eslabón que falta"))
A(parrafo(
    "La matriz tiene 288 celdas, resultado de dieciséis clases de humedad del combustible, dos "
    "condiciones de sombreado y nueve clases de temperatura. Esa dimensión no es arbitraria: "
    "reproduce exactamente la estructura de la tabla de Probability of Ignition del National "
    "Fire Danger Rating System estadounidense, publicada por el NWCG en el Incident Response "
    "Pocket Guide. La nomenclatura de CONAF —“probabilidad de ignición” y “humedad del "
    "combustible fino muerto”— pertenece al mismo linaje, y el umbral de 70 % replica la nota "
    "de esa tabla, que marca ese valor como el punto en que la probabilidad de focos "
    "secundarios pasa a ser alta."))
A(parrafo(
    "Sin embargo, el informe técnico de NASA DEVELOP es explícito en un punto decisivo: los "
    "valores de la matriz “were determined using the 2016-2017 fire season as a proxy”. Es "
    "decir, ",
    ("CONAF no transcribió la tabla estadounidense: la recalibró empíricamente con la "
     "temporada de incendios chilena 2016-2017", True),
    ". La matriz es, por tanto, un producto propio y no derivable de la literatura."))
A(parrafo(
    "Para efectos de esta réplica se reconstruyó la matriz completa aplicando la ecuación de "
    "probabilidad de ignición de Rothermel y BehavePlus, del Rocky Mountain Research Station, "
    "que es de dominio público. Contrastada contra las 144 celdas publicadas de la tabla NWCG "
    "en condición expuesta, la reconstrucción arroja un error medio de 0,83 puntos "
    "porcentuales y 132 coincidencias exactas, con un máximo de 10 puntos atribuible a un solo "
    "escalón de redondeo."))
A(parrafo(
    "La reconstrucción es sólida como referencia física, pero conviene mirar de frente su "
    "consecuencia numérica. Con la matriz reconstruida el umbral de 70 % se alcanza solo con "
    "humedades del combustible fino muerto iguales o inferiores a 4 %, lo que a 30 °C exige una "
    "humedad relativa de 15,2 % o menos. Si en la operación real CONAF activa el Botón Rojo con "
    "humedades relativas más altas, la conclusión es que ",
    ("su calibración chilena es sensiblemente más permisiva que la ecuación original", True),
    ", y esa diferencia debe resolverse antes de cualquier uso operativo de la réplica. Es la "
    "brecha principal de este trabajo, y se señala sin atenuantes."))
A(tabla(
    ["Temperatura del aire", "HR máxima que activa", "HCFM correspondiente"],
    [["20 °C", "14,8 %", "3,98 %"],
     ["25 °C", "15,0 %", "3,98 %"],
     ["30 °C", "15,2 %", "3,99 %"],
     ["35 °C", "15,4 %", "3,99 %"],
     ["40 °C", "19,4 %", "4,99 %"]],
    [3200, 3200, 3050], ["left", "center", "center"]))
A(parrafo(
    "Existen dos vías para cerrar esta brecha, y conviene seguir ambas en paralelo. La primera "
    "es solicitar formalmente la matriz al DEI/GEPRIF, o por Ley de Transparencia; los datos "
    "del Botón Rojo son de uso público según la propia licencia declarada por CONAF. La "
    "segunda es recuperarla por inversión empírica: CONAF publica simultáneamente las capas de "
    "temperatura, humedad del combustible y probabilidad de ignición sobre la misma grilla, de "
    "modo que cruzándolas se obtiene, para cada combinación, el decil de probabilidad que "
    "asigna el modelo oficial. Acumulando algunas semanas de cobertura nacional se cubren las "
    "288 combinaciones. El código adjunto implementa esta segunda vía."))
A(vacio())

A(seccion("7.  Verificaciones empíricas sobre los datos publicados"))
A(parrafo(
    "Las siguientes propiedades no están documentadas por CONAF y se establecieron "
    "interrogando directamente sus servicios de datos. Son relevantes porque determinan cómo "
    "debe construirse la agregación comunal de la réplica."))
A(tabla(
    ["Hallazgo", "Evidencia"],
    [["La grilla del índice equivale a celdas de 2 km",
      "En la capa PI, el cociente entre superficie y número de píxeles es exactamente "
      "4.000.000 m² en EPSG:3857 para todos los polígonos examinados"],
     ["El campo horas recorre 1 a 5",
      "Simbología de la capa Boton_Rojo y valores observados; confirma la ventana de cinco "
      "pasos horarios"],
     ["com_ha es la superficie combustible de la comuna, no su superficie total",
      "Colchane registra 177.125 ha sobre 401.560 ha de superficie comunal; Diego de Almagro, "
      "21.550 ha sobre 1.866.490 ha. El valor es constante para una misma comuna en todos sus "
      "registros"],
     ["La superficie combustible se contabiliza sobre celdas de 500 m",
      "Todos los valores de com_ha observados son múltiplos exactos de 25 ha: 177.125; "
      "131.925; 92.625; 82.525; 61.600; 48.000; 21.550; 12.275"],
     ["proportion es el cociente entre superficie activada y superficie combustible",
      "Verificado en catorce registros independientes: SUM_br_ha dividido por com_ha reproduce "
      "el valor publicado"],
     ["El servicio no es un archivo histórico",
      "Contiene únicamente la ventana vigente de cinco días y se sobrescribe en cada corrida. "
      "Al 27 de agosto de 2026 almacenaba 77 registros, correspondientes al 25 al 29 de mayo "
      "de 2026"]],
    [3800, 5650]))
A(parrafo(
    "La última observación tiene una implicancia práctica inmediata: ",
    ("no existe una serie histórica pública del Botón Rojo", True),
    ". Quien la necesite debe cosecharla a diario desde ahora, o solicitarla al DEI/GEPRIF. El "
    "código adjunto incluye un cosechador idempotente pensado para ejecutarse como tarea "
    "programada."))
A(vacio())

A(seccion("8.  Servicios de datos disponibles"))
A(parrafo(
    "Todos los productos del Botón Rojo se publican como servicios REST públicos en la "
    "organización ArcGIS Online del DEI. La raíz es "
    "services5.arcgis.com/A1ELWse9bRAi2JiV/arcgis/rest/services. Cada servicio meteorológico "
    "tiene cinco capas, d0 a d4, una por día de pronóstico, nombradas dN_AAAAMMDD_XX y "
    "sobrescritas en cada corrida."))
A(tabla(
    ["Servicio", "Contenido", "Campo clave"],
    [["TP", "Temperatura, en grados Celsius", "label: clase 1 a 9"],
     ["HR", "Humedad relativa, en porcentaje", "label"],
     ["HC", "Humedad del combustible fino muerto, en porcentaje", "label: clase 1 a 10"],
     ["VV", "Velocidad del viento, en km/h", "label: clase 1 a 8"],
     ["PI", "Probabilidad de ignición, en porcentaje", "label: decil 10 a 100"],
     ["Boton_Rojo",
      "Resultado agregado por comuna",
      "date, horas, com_id, com, prov, reg, com_ha, SUM_br_ha, proportion"]],
    [1200, 5100, 3150]))
A(parrafo(
    "La licencia declarada por CONAF establece que los datos son de uso público y que su "
    "utilización debe citar a CONAF como fuente. Cabe notar que ninguno de estos servicios "
    "está documentado como dato abierto ni cuenta con una API declarada; se accedió a ellos a "
    "través de la interfaz REST estándar de ArcGIS, que es pública."))
A(vacio())

A(seccion("9.  Limitaciones metodológicas a considerar"))
A(parrafo(
    "Más allá de la matriz faltante, la revisión deja a la vista cuatro limitaciones que "
    "conviene tener presentes tanto para replicar el índice como para interpretarlo."))
A(vinieta(
    "El pronóstico GFS tiene una resolución nativa de 0,25°, del orden de 25 km. La "
    "publicación sobre una grilla de 2 km es una operación de suavizado, no un aumento real de "
    "información: el viento de quebrada, el efecto Puelche o el Raco no quedan resueltos.",
    "Resolución efectiva. "))
A(vinieta(
    "La regresión de humedad del combustible depende solo de temperatura y humedad relativa "
    "instantáneas. No incorpora precipitación previa, radiación acumulada ni estado de curado "
    "del pastizal, de modo que no distingue un combustible que viene de una semana seca de uno "
    "que llovió ayer.",
    "Ausencia de memoria del combustible. "))
A(vinieta(
    "No se encontró ninguna evaluación publicada del desempeño del sistema —probabilidad de "
    "detección, tasa de falsas alarmas, curva ROC— ni tesis, artículo o ponencia que lo "
    "valide. La única evaluación disponible es la del proyecto NASA DEVELOP, acotada a cinco "
    "incendios de enero de 2017 en tres regiones.",
    "Sin validación publicada. "))
A(vinieta(
    "El modelo no incorpora tipo ni carga de combustible, solo la máscara binaria de "
    "superficie combustible; tampoco considera presencia humana, que es el principal factor de "
    "ocurrencia en Chile. Ambas limitaciones están reconocidas de forma expresa en el informe "
    "de NASA DEVELOP.",
    "Sin modelo de combustible ni factor antrópico. "))
A(vacio())

A(seccion("10.  Ruta de replicación propuesta"))
A(parrafo(
    "Con lo anterior, la réplica es alcanzable en plazos breves. Se propone la siguiente "
    "secuencia, ordenada por dependencia."))
A(vinieta(
    "Ejecutar la réplica en Google Earth Engine con la matriz reconstruida y contrastar el "
    "resultado, comuna por comuna y día por día, contra el producto oficial. La discrepancia "
    "observada es la medida directa de cuánto se aparta la matriz reconstruida de la real.",
    "Etapa 1, una semana. "))
A(vinieta(
    "En paralelo, oficiar al DEI/GEPRIF solicitando la matriz de 288 valores y la memoria de "
    "cálculo, e iniciar la cosecha diaria de los servicios publicados para constituir la serie "
    "histórica que hoy no existe.",
    "Etapa 2, en paralelo. "))
A(vinieta(
    "Si la matriz no se obtiene, recuperarla por inversión empírica cruzando las capas TP, HC "
    "y PI publicadas. Dos a tres semanas de cobertura nacional bastan para cubrir las "
    "combinaciones relevantes del rango operativo.",
    "Etapa 3, tres semanas. "))
A(vinieta(
    "Con la matriz resuelta, evaluar el desempeño contra los focos de calor VIIRS y contra el "
    "registro histórico de ocurrencia de CONAF, calculando probabilidad de detección y tasa de "
    "falsas alarmas. Esta evaluación no existe hoy y sería, en sí misma, un aporte al producto "
    "institucional.",
    "Etapa 4. "))
A(vinieta(
    "Evaluar mejoras acotadas y de alto rendimiento: corrección de sesgo de la humedad "
    "relativa con las estaciones de AGROMET del INIA y de la red EMA de la Dirección "
    "Meteorológica, tratamiento explícito de los bordes de dominio de las tablas A, C y F, y "
    "reemplazo de la regresión de humedad del combustible por un modelo con memoria.",
    "Etapa 5, opcional. "))
A(vacio())

A(seccion("11.  Entregables adjuntos"))
A(parrafo(
    "Se acompañan los siguientes archivos, todos comentados en español y listos para ejecutar:"))
A(vinieta("algoritmo puro en Python, con cuatro verificaciones automáticas.", "nucleo.py: "))
A(vinieta("réplica completa en el mismo entorno que usa CONAF, con la matriz "
          "reconstruida incorporada.", "boton_rojo_gee.js: "))
A(vinieta("réplica fuera de Earth Engine, desde la descarga del GFS en NOMADS "
          "hasta la tabla comunal.", "pipeline.py: "))
A(vinieta("cliente de los servicios REST de CONAF, con cosecha diaria y "
          "calibración empírica de la matriz.", "conaf_api.py: "))
A(vinieta("la matriz reconstruida en tres variantes "
          "comparables.", "matriz_probabilidad_ignicion.xlsx: "))
A(vacio())

A(seccion("Fuentes principales:"))
A(parrafo(
    "Metadatos del ítem oficial “Boton Rojo CONAF” en ArcGIS Online, identificador "
    "41ee3c691359437aa9df2a09d7f6124e, propiedad del usuario deigeprif; sitio institucional de "
    "CONAF, sección Situación actual y pronóstico de incendios; documento “Mapas en Carto.com "
    "elaborados por la Gerencia de Protección contra Incendios Forestales”, GEPRIF, 2022; "
    "NASA DEVELOP 2022, “Chile Disasters: Automating Wildfire Risk and Occurrence Mapping in "
    "Google Earth Engine”, NTRS 20220005936 y 20220007384; catálogo de Google Earth Engine "
    "para NOAA/GFS0P25 y ESA/WorldCover/v200; National Wildfire Coordinating Group, Incident "
    "Response Pocket Guide, tabla de Probability of Ignition; servicios REST públicos de la "
    "organización ArcGIS Online del DEI/GEPRIF, consultados el 26 y 27 de agosto de 2026."))

# ---------------------------------------------------------------------------
# Ensamblado
# ---------------------------------------------------------------------------

if os.path.exists(TRABAJO):
    shutil.rmtree(TRABAJO)
os.makedirs(TRABAJO)
with zipfile.ZipFile(PLANTILLA) as z:
    z.extractall(TRABAJO)

ruta_xml = os.path.join(TRABAJO, "word", "document.xml")
with open(ruta_xml, encoding="utf-8") as fh:
    xml = fh.read()

inicio = xml.index("<w:body>") + len("<w:body>")
fin = xml.index("<w:sectPr")
preservado = ""
m = re.search(r"<w:p>.*?<v:shapetype.*?</w:p>", xml[inicio:fin], re.S)
if m:
    preservado = m.group(0)

xml = xml[:inicio] + preservado + "".join(cuerpo) + xml[fin:]
with open(ruta_xml, "w", encoding="utf-8") as fh:
    fh.write(xml)

if os.path.exists(SALIDA):
    os.remove(SALIDA)
with zipfile.ZipFile(PLANTILLA) as origen, zipfile.ZipFile(SALIDA, "w", zipfile.ZIP_DEFLATED) as destino:
    for item in origen.infolist():
        ruta = os.path.join(TRABAJO, item.filename)
        with open(ruta, "rb") as fh:
            destino.writestr(item, fh.read())

print("Generado:", SALIDA, os.path.getsize(SALIDA), "bytes")
print("Párrafos/tablas insertados:", len(cuerpo))

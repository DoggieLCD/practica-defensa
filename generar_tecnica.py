# -*- coding: utf-8 -*-
"""
Genera tecnica.html: guía técnica de la tesis (datos, criterio, estacionariedad, modelos,
evaluación, Diebold-Mariano, umbrales) con una sección final de preguntas técnicas.

Uso:
    python generar_tecnica.py              -> escribe tecnica.html en la carpeta actual
    python generar_tecnica.py otra.html    -> escribe con otro nombre

En Google Colab: sube este archivo y ejecuta  !python generar_tecnica.py

Formato del texto: **negrita**, `código`, _{subíndice} y ^{superíndice}.
Para cambiar contenido, edita las listas SECCIONES, PREGUNTAS_ALTERNATIVAS y
PREGUNTAS_ABIERTAS, vuelve a ejecutar el script y sube el tecnica.html nuevo.
"""

import html
import json
import re
import sys
from pathlib import Path

TITULO_TESIS = (
    "Predicción de Peaks Extremos de Demanda Eléctrica en el Sistema Eléctrico Nacional "
    "de Chile mediante Modelos de Machine Learning"
)


# ---------------------------------------------------------------------------
# Bloques de contenido
# ---------------------------------------------------------------------------
def P(texto):
    return {"tipo": "p", "texto": texto}


def H3(texto):
    return {"tipo": "h3", "texto": texto}


def F(expresion, etiqueta=""):
    return {"tipo": "f", "texto": expresion, "etiqueta": etiqueta}


def L(*items):
    return {"tipo": "lista", "items": list(items)}


def T(columnas, filas, nota="", destacar=()):
    return {"tipo": "tabla", "columnas": columnas, "filas": filas, "nota": nota, "destacar": list(destacar)}


def N(texto, etiqueta="Para la defensa", clase="defensa"):
    return {"tipo": "nota", "texto": texto, "etiqueta": etiqueta, "clase": clase}


# ---------------------------------------------------------------------------
# SECCIONES: el contenido técnico. Todas las cifras vienen de la tesis.
# ---------------------------------------------------------------------------
SECCIONES = [
    {
        "id": "datos",
        "titulo": "1. Datos, validación y partición",
        "resumen": "Una serie diaria oficial, validada contra el regulador y dividida en tres períodos que no se mezclan.",
        "ref": "En la tesis: apartados 3.3, 3.4, 3.7 y 4.1.5 · Tablas 3.2, 3.3, 3.4, 3.7 y 4.1",
        "bloques": [
            H3("Fuente y variable objetivo"),
            P("Los datos vienen del portal Energía Abierta de la Comisión Nacional de Energía (conjunto «Demanda Diaria por Sistema SEN»). El archivo trae 11.864 registros diarios entre 2006 y julio de 2026, separados por sistema: SIC (4.347), SING (4.383) y SEN (3.134). El estudio usa los 3.134 días del SEN, del 1 de enero de 2018 al 31 de julio de 2026."),
            P("La variable objetivo es la **demanda máxima bruta horaria diaria** (`dmax_mw`). Es horaria porque corresponde al promedio de potencia en la hora de mayor exigencia, diaria porque se toma un valor por jornada y bruta porque incluye los consumos propios de las centrales. Es la misma magnitud que publican la CNE y el Coordinador, y por eso se pudo contrastar: el 24 de noviembre de 2025 la serie marca 12.293,88 MW y el reporte de la CNE 12.294 MW; el 29 de diciembre de 2025, 13.093,11 MW contra 13.093 MW."),
            H3("Por qué la serie parte en 2018"),
            P("Antes de la interconexión, concretada a fines de 2017, operaban dos sistemas independientes, cada uno con su propia demanda máxima y su propio instante de ocurrencia. Construir una serie única exigiría sumar ambos máximos, lo que supone que los dos alcanzaban la punta a la misma hora. Eso no se cumple: el Norte Grande tenía carga minera continua y el centro-sur un perfil residencial y comercial con más variación horaria. La suma sobrestimaría la demanda máxima conjunta, así que la ventana parte el 1 de enero de 2018, primer año completo de operación unificada."),
            H3("Validación de los datos"),
            P("Antes de cualquier transformación se aplicaron ocho pruebas: continuidad (0 fechas faltantes), unicidad (0 duplicados), completitud de `dmax_mw` y `dmin_mw` (0 nulos), rango físico (0 valores no positivos), coherencia `dmax_mw` ≥ `dmin_mw` (0 incoherencias), variación diaria plausible de hasta 30% (0 saltos) y mínimos compatibles con la operación (`dmin_mw` ≥ 35% de la mediana histórica, equivalente a 2.821,02 MW). Solo la última marcó registros: cinco."),
            P("Cuatro de ellos eran fallas de registro, como 1,88 MW el 23 de mayo de 2018 o 127,64 MW el 11 de septiembre de 2022. El quinto fue real: el apagón del 25 de febrero de 2025 (57,50 MW), por la desconexión de la línea Nueva Maitencillo–Nueva Pan de Azúcar de 2x500 kV, que afectó desde Arica hasta Los Lagos por más de ocho horas. Una falla de registro se excluye y una contingencia real se conserva; para separarlas hubo que revisar los reportes operacionales, porque en ambos casos la demanda vuelve a lo normal al día siguiente. Este tratamiento solo afecta la demanda mínima, usada en la relación valle-punta del Capítulo I, y no la variable objetivo."),
            H3("Observaciones utilizables"),
            P("De los 3.134 días se pierden 371 al inicio. Los primeros 174 no permiten calcular el criterio de peak, porque su cadena de ventanas retrocede 174 días (sección 2). Los 197 siguientes se excluyen porque el rezago anual de las predictoras (`lag_364`) necesita un año de historia en el origen. Quedan **2.763 observaciones utilizables**, del 7 de enero de 2019 al 31 de julio de 2026, con 117 eventos (4,23%)."),
            H3("Partición temporal"),
            T(["Subconjunto", "Período", "Observaciones utilizables", "Eventos", "Tasa"],
              [["Entrenamiento", "2018 a 2024", "2.186", "99", "4,53%"],
               ["Validación", "2025", "365", "10", "2,74%"],
               ["Prueba", "Enero a julio de 2026", "212", "8", "3,77%"],
               ["Total", "2018 a julio de 2026", "2.763", "117", "4,23%"]],
              "Tabla 3.7 de la tesis. El tramo utilizable del entrenamiento parte el 7 de enero de 2019.", destacar=[3]),
            P("La partición es estrictamente temporal y sin superposición: asignar días al azar metería información del futuro en el entrenamiento y daría un desempeño optimista. Los pronósticos de los primeros días de la prueba salen de orígenes de diciembre de 2025 (el del 1 de enero a siete días se emite el 25 de diciembre), y eso no contamina la prueba, porque la condición es que ninguna observación posterior al origen intervenga en el ajuste."),
            H3("La prueba es más exigente que el entrenamiento"),
            T(["Subconjunto", "n", "Media", "DE", "Mínimo", "Mediana", "Máximo", "CV (%)"],
              [["Entrenamiento", "2.557", "10.138,4", "637,6", "8.234,8", "10.129,4", "11.999,9", "6,3"],
               ["Validación", "365", "11.073,0", "692,4", "9.384,2", "11.184,5", "13.093,1", "6,3"],
               ["Prueba", "212", "12.369,2", "735,1", "10.422,2", "12.391,8", "14.151,8", "5,9"]],
              "Tabla 4.1 de la tesis, en MW. Aquí n cuenta todos los días de cada período: el entrenamiento tiene 2.557 días, de los cuales 2.186 son utilizables para modelar."),
            P("La media de la prueba supera en 22,0% a la del entrenamiento, el equivalente a 3,5 desviaciones estándar de este. El día más bajo de la prueba (10.422,2 MW) supera la media del entrenamiento (10.138,4 MW), y la mediana de la prueba supera en 391,9 MW el máximo del entrenamiento: más de la mitad de los días evaluados está sobre cualquier nivel que los modelos vieron al ajustarse."),
            P("Esto pesa distinto según la familia. SARIMAX trabaja sobre la serie diferenciada y Prophet proyecta su tendencia, así que no quedan acotados al rango visto. Los árboles de CatBoost, en cambio, predicen promedios de observaciones de entrenamiento y no extrapolan por construcción. El reajuste cada siete días mitiga esa asimetría al incorporar el nuevo régimen, pero es una diferencia estructural entre familias que hay que tener presente al compararlas."),
            P("Aun así, la tasa de eventos se mantiene entre 2,74% y 4,53% en los tres períodos: el cambio de nivel no aumenta la frecuencia del fenómeno, porque el criterio mide desviaciones respecto del nivel reciente y no niveles absolutos."),
        ],
    },
    {
        "id": "criterio",
        "titulo": "2. El criterio de peak extremo (OE1)",
        "resumen": "Un peak extremo es una demanda inesperada respecto del comportamiento reciente, no una demanda alta en términos absolutos.",
        "ref": "En la tesis: apartados 3.5 y 4.1.4 · Ecuaciones 3.1 a 3.4 · Tablas 3.5 y 4.3",
        "bloques": [
            H3("Las tres etapas"),
            P("El criterio pertenece al enfoque de desviación respecto de un nivel esperado. Las tres etapas usan solo observaciones anteriores al día evaluado, de modo que el criterio es causal y se puede calcular en el momento en que se necesita la alerta."),
            F("b_{t} = mediana( y_{t−28}, …, y_{t−1} )", "Ecuación 3.1 · nivel base"),
            P("Se usa la mediana y no la media porque es robusta frente a los propios eventos: un peak reciente no infla el nivel base ni enmascara eventos posteriores."),
            F("f_{t} = (1/8) · Σ_{s=1}^{8} y_{t−7s} / b_{t−7s}        E_{t} = b_{t} · f_{t}", "Ecuación 3.2 · factor del día de la semana y nivel esperado"),
            P("El factor promedia, sobre las últimas ocho semanas, el cociente entre la demanda del mismo día de la semana y su nivel base. Así una misma desviación significa lo mismo un martes que un domingo."),
            F("z_{t} = ( y_{t} / E_{t} − 1 ) / σ_{t}", "Ecuación 3.3 · desviación tipificada"),
            P("σ_{t} es la desviación estándar de las desviaciones relativas (y/E − 1) en los 90 días anteriores a t. El día es **peak extremo si z_{t} > k_{e}**, con k_{e} = 1,75."),
            H3("Por qué esas ventanas"),
            L("**28 días para el nivel base:** cuatro semanas completas, con el mismo número de cada día de la semana, así el nivel no queda sesgado por el día en que se calcula. Una ventana más corta sería sensible al ruido diario y una más larga reaccionaría tarde a cambios de nivel como el de 2025.",
              "**8 semanas para el factor:** ocho observaciones por cada día de la semana, suficientes para promediar el ruido sin usar un patrón tan antiguo que ya haya cambiado.",
              "**90 días para la dispersión:** una desviación estándar necesita más observaciones que una medida de nivel. Noventa días son cerca de un trimestre: capturan la variabilidad de la estación en curso sin mezclar estaciones."),
            P("Las ventanas se encadenan. σ usa 90 días de desviaciones; cada desviación necesita su factor f, que mira ocho semanas atrás (56 días); y cada factor necesita niveles base de 28 días. Por eso la cadena retrocede 90 + 56 + 28 = 174 días y el criterio no es calculable antes del 24 de junio de 2018."),
            H3("Calibración del umbral de etiquetado k_{e}"),
            T(["k_{e}", "Eventos", "Tasa (%)", "Un evento cada (días)"],
              [["1,00", "463", "15,64", "6,4"], ["1,25", "308", "10,41", "9,6"], ["1,40", "242", "8,18", "12,2"],
               ["1,50", "205", "6,93", "14,4"], ["1,60", "172", "5,81", "17,2"], ["1,75", "127", "4,29", "23,3"],
               ["2,00", "83", "2,80", "35,7"], ["2,25", "47", "1,59", "63,0"], ["2,50", "27", "0,91", "109,6"]],
              "Tabla 3.5 de la tesis, calculada sobre los 2.960 días en que el criterio es calculable.", destacar=[5]),
            P("Un k_{e} bajo produce tantos eventos que pierden significado operacional; uno alto deja tan pocos que no se puede entrenar ni evaluar la detección. Con 1,75 quedan 117 eventos sobre las 2.763 observaciones utilizables (4,23%), del orden de un evento cada 24 días."),
            N("La calibración se hizo sobre la serie completa, incluidas validación y prueba, y la tesis lo declara como limitación. Para acotarla se recalculó solo con el entrenamiento (2.383 días calculables, del 24 de junio de 2018 al 31 de diciembre de 2024): con 1,75 salen 109 eventos, una tasa de 4,57% (uno cada 21,9 días), y toda la rejilla difiere en menos de un punto porcentual, así que la misma regla habría elegido el mismo valor. Como las etiquetas usan solo días anteriores, los eventos de la prueba serían idénticos. Además, la elección no usa el desempeño de ningún modelo."),
            H3("Dos usos del criterio: etiquetar y alertar"),
            P("Etiquetar un día observado usa su demanda real y los componentes calculados con los días previos a ese día (Ecuaciones 3.1 a 3.3); la etiqueta es una propiedad del día. Alertar sobre un pronóstico es distinto: el pronóstico del día T + h se emite en el origen T, así que los componentes del criterio solo pueden usar lo disponible hasta T."),
            F("ẑ_{T+h|T} = ( ŷ_{T+h|T} / ( b_{T+1} · f_{T+h} ) − 1 ) / σ_{T+1}", "Ecuación 3.4 · desviación tipificada del pronóstico"),
            L("**b y σ quedan congelados en el origen:** se evalúan en T + 1, lo más reciente calculable, y son los mismos para los siete días. El séptimo día se compara contra un nivel base de siete días de antigüedad, que es la restricción real de la operación.",
              "**f corresponde al día objetivo:** f_{T+h} necesita datos hasta y_{T+h−7}, disponibles en el origen para todo h ≤ 7. Esa coincidencia entre el ciclo semanal y el horizonte permite corregir cada día por su propio día de la semana sin fuga de información; con un horizonte mayor a siete días no sería posible."),
            H3("Lo que encontró el criterio"),
            P("Sobre los 2.960 días calculables identificó 127 eventos (4,29%); en el conjunto de modelado, 117. El año 2025, el de mayor demanda media entre los completos, tiene la tasa más baja (2,74%): un nivel alto pero sostenido sube el nivel base y no genera eventos. El máximo de la serie (14.151,8 MW, 10 de junio de 2026) sí fue peak, con z = 2,87 sobre un nivel esperado de 12.986,2 MW; el máximo de 2025 (13.093,1 MW, 29 de diciembre) llegó a 1,69 y quedó bajo el umbral."),
            P("Por día de la semana los eventos se reparten parejo (15 lunes, 13 martes, 18 miércoles, 20 jueves, 23 viernes, 18 sábados y 20 domingos), lo que confirma que el factor f funciona: sin él se concentrarían en los días hábiles, que tienen 657,9 MW más de demanda promedio. Por mes, en cambio, no hay uniformidad: mayo concentra 30 eventos (23,6%), porque en la subida hacia el invierno el nivel base de 28 días queda bajo el nivel efectivo. Los eventos vienen en rachas: 82 rachas, 58 de un solo día y la más larga de seis días (27 de mayo al 1 de junio de 2022)."),
        ],
    },
    {
        "id": "estacionariedad",
        "titulo": "3. Estacionariedad, pruebas y diferenciación",
        "resumen": "ADF y KPSS dicen cuántas veces diferenciar; la ACF y la PACF orientan los órdenes del modelo.",
        "ref": "En la tesis: apartados 2.3.3, 2.3.4 y 4.1.3 · Ecuaciones 2.3 a 2.5 · Tabla 4.2",
        "bloques": [
            H3("Qué es una serie estacionaria"),
            P("Una serie es estacionaria cuando su media y su varianza no dependen del momento en que se observa: no tiene tendencia ni estacionalidad, aunque puede tener dependencia entre días cercanos. ARIMA la necesita porque sus coeficientes describen una estructura que debe mantenerse estable en el tiempo. Señales de no estacionariedad: el gráfico muestra tendencia, la ACF decae muy lento hacia cero y el primer coeficiente de autocorrelación es alto y positivo."),
            H3("Diferenciar"),
            F("y′_{t} = y_{t} − y_{t−1} = (1 − B) y_{t}", "Ecuación 2.3 · primera diferencia"),
            F("(1 − B^{s}) y_{t} = y_{t} − y_{t−s}        con s = 7:  y_{t} − y_{t−7}", "Ecuación 2.4 · diferencia estacional"),
            P("B es el operador de rezago (B y_{t} = y_{t−1}). Diferenciar estabiliza la media: en vez de modelar el nivel de la demanda, el modelo trabaja con sus cambios. El orden d cuenta cuántas diferencias regulares se aplican y D cuántas estacionales. Rara vez hace falta más de una."),
            H3("ADF y KPSS: hipótesis nulas opuestas"),
            T(["Prueba", "Hipótesis nula", "Si p < 0,05"],
              [["ADF (Dickey-Fuller aumentada)", "Hay raíz unitaria: la serie no es estacionaria", "Se rechaza: estacionaria"],
               ["KPSS (Kwiatkowski-Phillips-Schmidt-Shin)", "La serie es estacionaria", "Se rechaza: no estacionaria"]]),
            P("Se usan juntas porque se complementan: si coinciden, la conclusión es firme; si se contradicen, la serie está en un caso intermedio. En la tesis, ADF selecciona sus rezagos por el criterio de Akaike y KPSS se aplica con constante y selección automática de rezagos (ambas en statsmodels)."),
            T(["Serie", "Prueba", "Estadístico", "p", "Conclusión (α = 0,05)"],
              [["Original", "ADF", "−1,271", "0,642", "No se rechaza: no estacionaria"],
               ["Original", "KPSS", "6,857", "0,010", "Se rechaza: no estacionaria"],
               ["Primera diferencia", "ADF", "−13,501", "< 0,001", "Se rechaza: estacionaria"],
               ["Primera diferencia", "KPSS", "0,032", "> 0,100", "No se rechaza: estacionaria"],
               ["Diferencia regular y estacional", "ADF", "−19,516", "< 0,001", "Se rechaza: estacionaria"],
               ["Diferencia regular y estacional", "KPSS", "0,019", "> 0,100", "No se rechaza: estacionaria"]],
              "Tabla 4.2 de la tesis.", destacar=[2, 3]),
            P("Las dos pruebas coinciden en las tres series, el mejor resultado posible para el diagnóstico. La serie original no es estacionaria; la primera diferencia ya lo es, y agregar una diferencia estacional no cambia la conclusión. Por eso **d = 1 y D = 0**."),
            N("¿Cuántas diferenciaciones hay que hacer? Una regular: con ella ambas pruebas concluyen estacionariedad, y la diferencia estacional adicional no aporta nada. Diferenciar de más también es un problema (sobrediferenciación), así que se aplica solo lo necesario."),
            H3("ACF y PACF"),
            F("r_{k} = Σ_{t=k+1}^{T} (y_{t} − ȳ)(y_{t−k} − ȳ)   / Σ_{t=1}^{T} (y_{t} − ȳ)^{2}", "Ecuación 2.5 · autocorrelación de rezago k"),
            P("La ACF mide cuánto se parece la serie a sí misma desplazada k días; la PACF mide la relación pura con el rezago k, quitando el efecto de los días intermedios. La PACF orienta el orden p (autorregresivo) y la ACF el orden q (media móvil)."),
            P("En la serie original, la ACF supera la banda de confianza en los 40 rezagos y decae lento desde 0,835 en el rezago 1: la firma de una serie no estacionaria. Encima hay un patrón semanal claro: 0,878 en el rezago 7, 0,851 en el 14, 0,821 en el 21 y 0,788 en el 28. El rezago 7 supera al 1, es decir, un día se parece más al mismo día de la semana anterior que al de ayer."),
            P("Lo decisivo es que el patrón semanal sigue después de diferenciar: en la primera diferencia, los rezagos 7, 14, 21 y 28 conservan 0,665, 0,640, 0,628 y 0,607. La diferencia regular no agota el ciclo semanal, y eso justifica los términos estacionales (1,0,1)_{7}. Los órdenes finales se eligieron con la ACF y la PACF, complementadas con el criterio de información de Akaike (AIC) sobre el entrenamiento."),
        ],
    },
    {
        "id": "modelos",
        "titulo": "4. Los modelos y por qué están configurados así",
        "resumen": "Tres familias más dos referencias. Toda configuración se fijó antes de mirar la prueba, con la semilla en 42.",
        "ref": "En la tesis: apartados 2.4, 3.8 y 4.2 · Ecuaciones 2.10 a 2.21 · Tablas 4.4 y 4.5",
        "bloques": [
            T(["Modelo", "Familia", "Cómo usa el tiempo", "Configuración clave"],
              [["Persistencia", "Referencia", "Repite y_{T} los siete días", "Sin parámetros"],
               ["Estacional ingenuo", "Referencia", "Repite el mismo día de la semana anterior", "Sin parámetros"],
               ["SARIMAX(2,1,2)(1,0,1)_{7}", "Estadística", "Rezagos y errores pasados, más 8 exógenas de calendario", "Órdenes por ACF, PACF y AIC"],
               ["Prophet", "Estadística (aditiva)", "Tendencia, estacionalidades y feriados, sin rezagos", "Tendencia lineal por tramos, regularización 0,05, Fourier anual de 10 términos"],
               ["CatBoost", "Aprendizaje automático", "42 predictoras construidas", "600 iteraciones, profundidad 6, tasa 0,05, L2 3,0, pérdida MAE"],
               ["LSTM", "Aprendizaje profundo", "Secuencia de 28 días de la serie tipificada", "32 unidades, dropout 0,1, 7 salidas, Adam 0,001"]]),
            H3("Qué datos informan cada decisión"),
            P("Los órdenes de SARIMAX se determinaron con el entrenamiento. Los hiperparámetros de CatBoost, Prophet y la LSTM se fijaron de antemano, sin búsqueda sobre los datos. La tipificación de la red se ajusta con el histórico de cada origen, y su detención temprana usa una fracción del propio entrenamiento. El umbral de alerta se calibra en validación. La prueba interviene solo en dos decisiones, ambas declaradas como limitaciones: la calibración de k_{e} (sobre la serie completa) y la elección del modelo integrado al esquema."),
            H3("Las referencias"),
            P("La persistencia repite el valor del origen para los siete días; el estacional ingenuo repite, para cada día objetivo, el valor del mismo día de la semana anterior. Ninguna estima parámetros: fijan el piso que todo modelo debe superar, y el estacional ingenuo es la más exigente porque ya incluye el ciclo semanal. Su error es idéntico en los siete horizontes (442,4 MW en prueba), porque el valor que repite no depende del origen, y a siete días coincide con la persistencia, porque el día objetivo cae el mismo día de la semana que el origen."),
            H3("SARIMAX(2,1,2)(1,0,1)₇"),
            F("(1 − φ_{1}B − φ_{2}B^{2})(1 − Φ_{1}B^{7})(1 − B) y_{t}   = Σ_{j} β_{j} x_{j,t} + (1 + θ_{1}B + θ_{2}B^{2})(1 + Θ_{1}B^{7}) ε_{t}", "Ecuación 2.10"),
            P("Tiene una diferencia regular, dos términos autorregresivos y dos de media móvil en la parte regular, y uno de cada tipo en la parte estacional de período 7. Las 8 exógenas son de calendario: fin de semana, feriado, víspera de feriado, día posterior a feriado y los dos primeros pares de senos y cosenos del ciclo anual. Como son conocidas de antemano, el modelo proyecta los siete días sin tener que pronosticar sus entradas. Con temperatura habría que pronosticarla primero, y su error se sumaría al de la demanda."),
            T(["Término", "Coeficiente", "p", "Lectura"],
              [["fin_de_semana", "−620,979", "< 0,001", "Un fin de semana baja cerca de 621 MW"],
               ["feriado", "−497,685", "< 0,001", "Un feriado baja cerca de 498 MW"],
               ["vispera_feriado", "−207,223", "< 0,001", "La víspera ya baja cerca de 207 MW"],
               ["post_feriado", "22,504", "0,264", "No significativo: la demanda se normaliza de inmediato"],
               ["ar.S.L7", "0,887", "< 0,001", "El término más fuerte (z = 40,335): la estructura semanal"],
               ["ma.L1", "−1,460", "< 0,001", "Corrección por el error del día anterior"],
               ["ar.L2", "−0,182", "0,064", "No significativo, en el límite"]],
              "Selección de la Tabla 4.4. Máxima verosimilitud con filtro de Kalman sobre las 2.557 observaciones del entrenamiento. Son significativos 12 de 15 términos; los otros dos son post_feriado y cos_1 (p = 0,362)."),
            P("El coeficiente de fin de semana (−621,0 MW) concuerda con la diferencia descriptiva entre días hábiles y fines de semana (657,9 MW) y con el componente semanal de Prophet (cerca de 590 MW): tres métodos distintos entre 590 y 660 MW. La desviación estándar de los residuos es 250,3 MW."),
            P("El diagnóstico de residuos tiene resultados desfavorables que la tesis declara:"),
            L("**Estacionariedad e invertibilidad:** las raíces quedan fuera del círculo unitario, pero la menor raíz de media móvil es 1,006, casi sobre él. Esa es la firma habitual de una sobrediferenciación: no invalida el modelo, pero el orden de diferenciación admite revisión.",
              "**Ljung-Box:** rechaza la ausencia de autocorrelación en los rezagos 7, 14 y 28 (estadísticos 76,54, 95,22 y 98,89; p < 0,001). Queda estructura semanal sin capturar, y un componente estacional de orden superior podría tomarla.",
              "**Jarque-Bera:** rechaza la normalidad (1.246,58; p < 0,001), con asimetría −0,31 y curtosis 6,37: colas mucho más pesadas que la normal. Los errores grandes se concentran en los días atípicos, justo los que interesa detectar.",
              "**Heterocedasticidad:** estadístico 1,75 con p < 0,001: la varianza de los residuos no es constante en el tiempo."),
            H3("Prophet"),
            F("y(t) = g(t) + s(t) + h(t) + ε_{t}", "Ecuación 2.11"),
            F("s(t) = Σ_{n=1}^{N} [ a_{n} cos(2πnt/P) + b_{n} sen(2πnt/P) ]", "Ecuación 2.12 · estacionalidad con series de Fourier"),
            P("g(t) es la tendencia, lineal por tramos con puntos de quiebre; s(t) la estacionalidad; h(t) los feriados; y ε lo que no explica. A diferencia de SARIMAX no usa rezagos: estima la forma general de la serie en función de la fecha, lo que en horizontes cortos lo deja en desventaja."),
            L("**Tendencia:** regularización de los puntos de quiebre en 0,05, el valor por omisión. Más alto sigue el ruido de corto plazo (sobreajuste); más bajo no captura un cambio de nivel.",
              "**Estacionalidades:** anual con 10 términos de Fourier, semanal con los 3 por omisión y diaria desactivada, porque hay una sola observación por día.",
              "**Modo aditivo:** las estacionalidades se suman a la tendencia, lo que supone que la amplitud de los ciclos es constante en MW.",
              "**Feriados:** calendario legal de Chile con los traslados de la Ley 19.973. Un calendario de otro país pondría efectos en fechas equivocadas.",
              "Su intervalo de incertidumbre no se usó, porque la alerta sale del criterio común a los cuatro modelos."),
            P("Componentes estimados: la tendencia sube más entre mediados de 2020 y mediados de 2021; la semana va de cerca de −455 MW el domingo a +235 MW el lunes (amplitud de unos 690 MW); el máximo anual cae a fines de junio y el mínimo en la segunda quincena de octubre; los feriados restan entre 400 y 500 MW."),
            H3("CatBoost"),
            F("F_{m}(x) = F_{m−1}(x) + v · h_{m}(x)", "Ecuación 2.13 · potenciación del gradiente"),
            F("r_{im} = − ∂L(y_{i}, F(x_{i})) / ∂F(x_{i}),   evaluado en F = F_{m−1}", "Ecuación 2.14 · pseudorresiduo"),
            P("Cada árbol nuevo se ajusta al gradiente negativo de la pérdida (con pérdida cuadrática, al residuo de lo que el conjunto anterior no explicó), y la tasa v limita cuánto aporta. CatBoost agrega la **potenciación ordenada**: calcula el pseudorresiduo de cada observación con un modelo entrenado solo con las que la anteceden en una permutación aleatoria, lo que evita el desplazamiento de predicción que afecta a XGBoost y LightGBM. También trata de forma nativa los valores faltantes y las variables categóricas, y captura relaciones no lineales sin declararlas."),
            P("Configuración: 600 iteraciones, profundidad 6, tasa de aprendizaje 0,05, regularización L2 de 3,0, pérdida MAE y semilla 42. Como un modelo de árboles no genera trayectorias, se usó **estimación directa**: siete modelos, uno por horizonte, con la misma matriz de predictoras y distinta variable objetivo. La alternativa recursiva, que reinyecta el pronóstico como rezago, se descartó porque acumula el error de los pasos previos y obliga a construir predictoras sobre valores estimados."),
            P("Importancia de variables: el calendario concentra entre 31,0% y 47,9% según el horizonte; `crit_f_objetivo` tiene la mayor importancia media (7,26%), seguida de `dow` (6,27%). Y aparece un patrón propio: en cada horizonte, el rezago más importante es el que cae en el mismo día de la semana que el día objetivo, lag_{7−h}. Así ocurre con `lag_6` en h = 1 (8,23%), `lag_3` en h = 4 (12,64%), `lag_2` en h = 5 (11,67%), `lag_1` en h = 6 (12,67%) y `lag_0` en h = 7 (12,17%). Para h = 2 y h = 3 harían falta `lag_5` y `lag_4`, que no se construyeron, y justo esos horizontes tienen los F_{1} más bajos (0,333 y 0,308)."),
            H3("LSTM"),
            F("f_{t} = σ(W_{f}·[h_{t−1}, x_{t}] + b_{f})     i_{t} = σ(W_{i}·[h_{t−1}, x_{t}] + b_{i})     o_{t} = σ(W_{o}·[h_{t−1}, x_{t}] + b_{o})", "Ecuaciones 2.16 a 2.18 · compuertas de olvido, entrada y salida (aquí f es la compuerta, no el factor del criterio)"),
            F("C_{t} = f_{t} ⊙ C_{t−1} + i_{t} ⊙ C̃_{t}        h_{t} = o_{t} ⊙ tanh(C_{t})", "Ecuaciones 2.20 y 2.21 · estado de celda y salida"),
            P("Las redes recurrentes simples sufren desvanecimiento del gradiente: al propagar el error hacia atrás se multiplican derivadas menores que uno. La LSTM lo evita con un estado de celda que pasa de un paso al siguiente multiplicado solo por la compuerta de olvido; si esta es cercana a 1, la información viaja muchos pasos sin degradarse."),
            P("Arquitectura: una capa LSTM de 32 unidades, dropout de 0,1 y una capa densa de 7 salidas, una por día de la trayectoria (estimación directa en un solo modelo). Entrada: ventana de 28 días de la demanda tipificada como única variable, sin calendario. Entrenamiento: pérdida MAE, Adam con tasa 0,001, lotes de 32, hasta 80 épocas, detención temprana con paciencia de 10 y restauración de los mejores pesos. El escalador se ajusta solo con el histórico de cada origen."),
            F("LSTM: 4 × [ 32 × (32 + 1) + 32 ] = 4.352        Densa: 32 × 7 + 7 = 231        Total: 4.583", "De dónde salen los 4.583 parámetros entrenables (conteo estándar de Keras)"),
            P("La curva de pérdida muestra el patrón del sobreajuste: el entrenamiento baja de 0,70 a cerca de 0,39 y la validación interna se estanca en torno a 0,515 desde la época 40; la detención temprana cortó cerca de la época 65. El mecanismo funcionó, pero su validación interna es una fracción del mismo período de entrenamiento: evita memorizar ruido, no adaptarse a un nivel nuevo. En la prueba el error fue de 797,1 MW (R^{2} = −0,667), 131,9% más que en validación (343,7 MW), frente a 12,4% en SARIMAX."),
            N("Si se evalúan validación y prueba juntas (577 días), la LSTM obtiene 510,3 MW y R^{2} = 0,484, cifras que esconden su fracaso. Juntar dos períodos de nivel distinto infla la varianza total de lo observado, que es el denominador del R^{2}, y un modelo que solo reproduce la diferencia de nivel entre ambos parece bueno. Por eso las métricas se reportan por período.", "Ojo con esta trampa", "ojo"),
        ],
    },
    {
        "id": "predictoras",
        "titulo": "5. Las 42 predictoras y la fuga de información",
        "resumen": "Lo que describe el pasado se ancla en el origen; el calendario, en el día objetivo.",
        "ref": "En la tesis: apartado 3.6 · Tabla 3.6 y Anexo A",
        "bloques": [
            P("Desde un origen T se pronostica una trayectoria de siete días. Al pronosticar T + 7, los seis días previos aún no se observan, así que toda variable sobre el comportamiento pasado usa datos hasta y_{T} inclusive y es la misma para los siete horizontes. El calendario es la excepción: el día de la semana, los feriados y los armónicos son los del día T + h, porque se conocen de antemano y no dependen de observaciones futuras."),
            T(["Grupo", "Anclaje", "N.º", "Qué contiene"],
              [["Calendario", "Día objetivo", "8", "dow, fin_de_semana, mes, dia_del_mes, semana_iso, feriado, vispera_feriado y post_feriado"],
               ["Componentes armónicas", "Día objetivo", "4", "Senos y cosenos de 2πd/365,25 y 4πd/365,25: el ciclo anual sin el salto artificial entre diciembre y enero"],
               ["Componentes del criterio", "Origen", "4", "crit_b_origen, crit_sigma_origen, crit_z_origen y crit_f_objetivo (este usa datos hasta y_{T+h−7}): la misma información con que se evalúa la alerta"],
               ["Rezagos", "Origen", "13", "lag_0 a lag_3, lag_6, lag_7, lag_13, lag_14, lag_20, lag_21, lag_27, lag_28 y lag_364"],
               ["Ventanas móviles y diferencias", "Origen", "13", "Medias y medianas de 7, 14 y 28 días; desviaciones de 7, 28 y 90 días; dif_1, dif_7, razón y rango de 28 días"],
               ["Total", "", "42", ""]],
              "Tabla 3.6 de la tesis, con el detalle del Anexo A.", destacar=[5]),
            P("El horizonte no entra como variable: con estimación directa cada horizonte tiene su propio modelo, y la dependencia de h queda en sus parámetros. Los rezagos van en pares semanales (6 y 7, 13 y 14, 20 y 21, 27 y 28) más el mismo día del año anterior (`lag_364`)."),
            H3("La prueba de fuga de información"),
            P("Una fuga es usar sin querer datos que no existían al momento de pronosticar; produce resultados optimistas que no se sostienen en operación, y el riesgo crece con el horizonte. La prueba de perturbación: se multiplicó por 10 la demanda del 19 de marzo de 2025 y se recalculó la matriz completa de predictoras. El primer origen con cambios fue el propio 19 de marzo, y el factor del día de la semana no varió antes del 26 de marzo, siete días después. Ninguna fila anterior cambió, así que ninguna predictora mira el futuro."),
            P("La prueba detecta cualquier fuga sin importar qué variable la cause, porque toda fuga se manifiesta como una fila modificada antes de la fecha alterada. La misma condición se verificó sobre los componentes del criterio de alerta."),
        ],
    },
    {
        "id": "backtesting",
        "titulo": "6. Backtesting de origen móvil",
        "resumen": "Cada día de prueba se simula como si fuera hoy, desde siete orígenes distintos.",
        "ref": "En la tesis: apartados 2.6.1 y 3.9.1 · Figura 3.3",
        "bloques": [
            P("El modelo se ajusta con los datos hasta el origen T, pronostica de T + 1 a T + 7, y la trayectoria se compara con lo observado; luego el origen avanza un día y todo se repite. La validación cruzada aleatoria no sirve en series temporales, porque mezclaría información del futuro en el entrenamiento. El protocolo es idéntico para los seis modelos, condición para que las diferencias se puedan atribuir a los modelos y no al diseño."),
            L("**Dos cadencias:** el origen avanza cada día, pero los parámetros se reajustan cada siete orígenes. El avance diario da más pronósticos y más potencia a los contrastes; usar solo orígenes semanales no solapados reduciría la muestra a un séptimo. El reajuste semanal responde al costo: reajustar en cada origen multiplicaría por siete el cómputo. Se supone que eso no cambia el resultado, porque los parámetros de una serie diaria no varían mucho entre días consecutivos, pero la tesis declara que ese supuesto no se contrastó.",
              "**Entre reajustes** los parámetros quedan fijos, pero cada modelo recibe los datos nuevos: SARIMAX los incorpora a su estado sin reestimarse, CatBoost a través de las predictoras del origen, la LSTM a través de su ventana, las referencias directamente, y Prophet no los necesita porque pronostica solo en función de la fecha.",
              "**Cuentas:** 212 días de prueba × 7 horizontes = **1.484 pronósticos** por modelo, con 212 evaluaciones por horizonte. Cada día de la prueba recibe siete pronósticos, emitidos desde siete orígenes distintos."),
        ],
    },
    {
        "id": "metricas",
        "titulo": "7. Métricas de pronóstico y de detección",
        "resumen": "Cinco métricas para el valor pronosticado y tres para la detección, todas calculadas por horizonte.",
        "ref": "En la tesis: apartados 1.3, 3.9.2, 3.9.3 y 3.9.5 · Ecuaciones 3.5 a 3.12",
        "bloques": [
            F("MAE_{h} = (1/m) Σ | y_{j} − ŷ_{j} |", "Ecuación 3.5 · error absoluto medio (MW)"),
            F("RMSE_{h} = [ (1/m) Σ ( y_{j} − ŷ_{j} )^{2} ]^{1/2}", "Ecuación 3.6 · raíz del error cuadrático medio (MW): castiga más los errores grandes"),
            F("MAPE_{h} = (100/m) Σ | ( ŷ_{j} − y_{j} ) / y_{j} |", "Ecuación 3.7 · error porcentual absoluto medio"),
            F("BIAS_{h} = (100/m) Σ ( ŷ_{j} − y_{j} ) / y_{j}", "Ecuación 3.8 · sesgo: negativo significa que subestima"),
            F("R^{2}_{h} = 1 − Σ ( y_{j} − ŷ_{j} )^{2} / Σ ( y_{j} − ȳ )^{2}", "Ecuación 3.9 · coeficiente de determinación"),
            P("m es el número de orígenes evaluados, y_{j} lo observado en T_{j} + h y ŷ_{j} el pronóstico emitido en T_{j}. Se calculan por horizonte porque el desempeño se degrada con la anticipación, y un promedio único ocultaría hasta cuándo sirve el pronóstico; la media de los siete horizontes se informa solo como resumen."),
            P("MAE, RMSE y BIAS son los indicadores que la Norma Técnica de Coordinación y Operación exige minimizar en las proyecciones de demanda (arts. 2-142 y 2-145) y que el Coordinador publica (art. 2-146). La norma los expresa normalizados por la demanda máxima horaria y la tesis los usa en su forma estándar, así que la correspondencia es de indicador y no de fórmula. MAPE y R^{2} se agregan para comparar con la literatura: el MAPE no depende de la escala y el R^{2} es la medida con que reportan los estudios revisados."),
            H3("Métricas de detección"),
            F("Precisión_{h} = VP / (VP + FP)     Exhaustividad_{h} = VP / (VP + FN)     F_{1,h} = 2 · P · E / (P + E)", "Ecuaciones 3.10 a 3.12"),
            P("Con clases desbalanceadas, la exactitud (accuracy) engaña: un modelo que nunca avisa acierta en casi todos los días. El F_{1} es una media armónica, que castiga cuando una de las dos métricas es muy baja. Un modelo que alertara siempre tendría exhaustividad 1, pero precisión 56/1.484 = 0,038 y F_{1} = 0,073."),
            L("La unidad de evaluación es el **pronóstico**, es decir, un par origen-horizonte: 1.484 en la prueba.",
              "Una **oportunidad** es un pronóstico cuyo día objetivo es un evento: 8 eventos × 7 horizontes = 56.",
              "VP es una oportunidad con alerta, FN una oportunidad sin alerta y FP (falsa alarma) una alerta sobre un día que no es evento.",
              "Las alertas no se agrupan en el tiempo: si varios orígenes señalan el mismo día, o se alerta en días consecutivos, cada una cuenta por separado. Aparte se informa cuántos **eventos distintos** recibieron al menos una alerta, como el «6 de 8»."),
            H3("Diseño en dos etapas"),
            P("Primero cada modelo pronostica la trayectoria; después se aplica el mismo criterio de peak sobre cada valor pronosticado (Ecuación 3.4). Eso tiene tres consecuencias: ningún modelo ve las etiquetas, así que todos compiten con las mismas reglas; se puede incluir a SARIMAX, que entrega un valor y no una probabilidad de clase; y la detección hereda la estructura por horizonte. Entrenar clasificadores directos sobre la etiqueta habría impedido comparar las familias, porque los modelos estadísticos no admiten esa formulación sin transformarse en otro tipo de modelo."),
        ],
    },
    {
        "id": "diebold",
        "titulo": "8. La prueba de Diebold-Mariano y las correcciones",
        "resumen": "Sirve para saber si un modelo gana de forma consistente o si la diferencia es azar del período evaluado.",
        "ref": "En la tesis: apartados 2.6.2, 3.9.4 y 4.3.5 · Ecuaciones 3.13 y 3.14 · Tabla 4.8",
        "bloques": [
            P("Una diferencia de MAE entre dos modelos no prueba por sí sola que uno sea mejor. La prueba de Diebold-Mariano contrasta la hipótesis nula de **igual capacidad predictiva** a partir de las diferencias de pérdida pronóstico a pronóstico. En la tesis la pérdida es el error absoluto, coherente con el MAE como métrica principal, y la prueba se aplica por separado en cada horizonte."),
            F("d_{j} = | e_{1,j} | − | e_{2,j} |        DM = d̄ / V(d̄)^{1/2}", "Ecuación 3.13 · V(d̄) es un estimador de la varianza de d̄; el exponente 1/2 es la raíz cuadrada"),
            P("Si d̄ es negativo y grande respecto de su variabilidad, el modelo 1 se equivoca menos de forma sistemática. El punto técnico es la varianza: con pronósticos de varios días, las trayectorias de orígenes vecinos se superponen y las diferencias d_{j} quedan autocorrelacionadas. Por eso V(d̄) incorpora las autocovarianzas hasta el rezago h − 1. Suponer independencia subestimaría la varianza y haría rechazar la hipótesis nula más veces de lo que corresponde."),
            F("DM* = DM ·   [ ( m + 1 − 2h + h(h − 1)/m ) / m ]^{1/2}", "Ecuación 3.14 · corrección de Harvey, Leybourne y Newbold (1997); DM* se compara con una t de Student con m − 1 grados de libertad"),
            P("La corrección ajusta por muestra pequeña y depende del horizonte: su efecto es marginal en h = 1 y apreciable en h = 7. El contraste es bilateral al 5% y se aplica a 15 pares de modelos en los horizontes 1, 4 y 7. La distribución t se toma de scipy."),
            H3("La corrección de Holm"),
            P("Con muchas pruebas a la vez, algunas salen «significativas» solo por azar. Holm (1979) ordena los valores p de menor a mayor y compara el i-ésimo con α/(n − i + 1): el más chico con α/n, el siguiente con α/(n − 1), y así, hasta el primero que no rechaza, donde se detiene. Controla la probabilidad de cometer al menos un falso positivo y es menos conservadora que Bonferroni."),
            T(["Par de modelos", "DM* h = 1", "p", "DM* h = 4", "p", "DM* h = 7", "p"],
              [["SARIMAX – CatBoost", "−3,794", "< 0,001", "−3,556", "< 0,001", "−2,614", "0,010"],
               ["SARIMAX – Prophet", "−9,438", "< 0,001", "−5,323", "< 0,001", "−5,890", "< 0,001"],
               ["SARIMAX – Estacional ingenuo", "−6,836", "< 0,001", "−3,770", "< 0,001", "−3,567", "< 0,001"],
               ["CatBoost – Estacional ingenuo", "−4,897", "< 0,001", "−0,788", "0,431", "−0,499", "0,618"],
               ["Prophet – Estacional ingenuo", "−0,049", "0,961", "0,290", "0,772", "0,457", "0,648"],
               ["LSTM – Estacional ingenuo", "5,685", "< 0,001", "5,425", "< 0,001", "4,713", "< 0,001"]],
              "Selección de la Tabla 4.8. Un valor negativo indica que el primer modelo del par se equivoca menos."),
            L("SARIMAX supera a todos con significancia en los tres horizontes, aunque frente a CatBoost el estadístico baja de −3,794 a −2,614: la ventaja se estrecha con la anticipación.",
              "CatBoost supera a ambas referencias en h = 1, pero no se distingue del estacional ingenuo en h = 4 ni en h = 7, ni de Prophet en esos dos horizontes.",
              "Prophet no se distingue del estacional ingenuo en ningún horizonte (p = 0,961, 0,772 y 0,648).",
              "La LSTM es significativamente peor que el estacional ingenuo en los tres horizontes.",
              "**Con Holm** por horizonte dejan de ser significativas tres diferencias: Prophet frente a la persistencia en h = 1 (p = 0,019), las dos referencias entre sí en h = 1 (p = 0,040) y SARIMAX frente a CatBoost en h = 7 (p = 0,010). Aplicada sobre las 44 comparaciones juntas, caen las mismas tres."),
            N("Significancia no es relevancia: un p chico dice que la diferencia difícilmente es azar del período, no que sea grande en MW, y eso se juzga con las métricas. Además, el contraste opera sobre pronósticos ya generados, así que cubre la variabilidad del período evaluado y no la del entrenamiento, que se controla fijando la semilla."),
        ],
    },
    {
        "id": "exactitud",
        "titulo": "9. Resultados de exactitud por horizonte",
        "resumen": "SARIMAX es el más exacto en los siete horizontes, tanto en validación como en prueba.",
        "ref": "En la tesis: apartados 4.3.1 y 4.3.2 · Tablas 4.6 y 4.7",
        "bloques": [
            T(["Modelo", "h = 1", "h = 2", "h = 3", "h = 4", "h = 5", "h = 6", "h = 7", "Media"],
              [["SARIMAX", "261,3", "297,1", "315,8", "321,7", "330,5", "336,1", "332,8", "313,6"],
               ["CatBoost", "316,3", "380,1", "410,3", "409,2", "419,3", "441,1", "415,5", "398,8"],
               ["Estacional ingenuo", "442,4", "442,4", "442,4", "442,4", "442,4", "442,4", "442,4", "442,4"],
               ["Prophet", "441,0", "445,4", "449,8", "454,3", "452,9", "456,8", "461,7", "451,7"],
               ["Persistencia", "528,5", "713,2", "723,4", "740,6", "770,5", "643,3", "442,4", "651,7"],
               ["LSTM", "681,5", "808,4", "796,2", "843,7", "855,2", "821,4", "773,4", "797,1"]],
              "MAE en MW sobre la prueba, enero a julio de 2026 (Tabla 4.7, panel A).", destacar=[0]),
            P("En validación el orden es SARIMAX (279,0 MW), CatBoost (300,5), LSTM (343,7), estacional ingenuo (357,1), Prophet (403,9) y persistencia (620,4). En la prueba la LSTM cae al último lugar y CatBoost se aleja de SARIMAX."),
            P("La forma de la degradación es informativa. El error de SARIMAX crece 23,1% entre el día 1 y el 4, y solo 3,5% más hasta el 7: después del cuarto día la información de la dinámica reciente se agota y el pronóstico descansa en el calendario y en el nivel, que no se degradan con el horizonte. CatBoost repite el patrón (29,4% y 1,5%), mientras que Prophet tiene un error casi constante, porque no usa la dinámica reciente."),
            P("Otros indicadores de la prueba: el MAPE medio de SARIMAX es 2,54% (2,12% a un día y 2,70% a siete); su R^{2} va de 0,768 a un día a 0,604 a siete; el R^{2} de la LSTM es negativo en todos los horizontes (−0,667 en promedio), peor que predecir siempre la media. Con RMSE el orden se mantiene, salvo que Prophet supera al estacional ingenuo. El sesgo medio es −0,40% en SARIMAX, −2,11% en CatBoost y −2,69% en Prophet, y en validación todos los modelos salvo las referencias tienen un sesgo negativo que se acentúa con el horizonte."),
        ],
    },
    {
        "id": "hallazgo",
        "titulo": "10. El hallazgo: exactitud no es detección",
        "resumen": "Con el umbral que define el fenómeno los modelos casi no avisan, porque todos recortan los días altos.",
        "ref": "En la tesis: apartados 2.5.1, 4.4.1, 4.4.2 y 4.4.3 · Tablas 4.9 y 4.10",
        "bloques": [
            T(["Modelo", "Alertas", "VP", "FP", "FN", "Precisión", "Exhaustividad", "F₁"],
              [["SARIMAX", "1", "1", "0", "55", "1,000", "0,018", "0,035"],
               ["CatBoost", "0", "0", "0", "56", "—", "0,000", "0,000"],
               ["Prophet", "0", "0", "0", "56", "—", "0,000", "0,000"],
               ["LSTM", "0", "0", "0", "56", "—", "0,000", "0,000"],
               ["Persistencia", "237", "16", "221", "40", "0,068", "0,286", "0,109"],
               ["Estacional ingenuo", "37", "0", "37", "56", "0,000", "0,000", "0,000"]],
              "Detección en la prueba con el umbral de etiquetado k_{e} = 1,75, los siete horizontes juntos (Tabla 4.9). La precisión no está definida cuando no hay alertas."),
            P("El modelo más exacto detecta 1 de 56 oportunidades. El F_{1} más alto es el de la persistencia, pero solo porque alerta en uno de cada 6,3 pronósticos: con esa tasa de activación un esquema no sirve para operar. La conclusión es que el umbral que define el fenómeno no se puede aplicar directamente sobre una serie pronosticada."),
            H3("El sesgo condicional"),
            T(["Decil", "Días", "Demanda media (MW)", "Sesgo (%)", "Sesgo (MW)", "MAE (MW)"],
              [["1 (más baja)", "22", "10.998,4", "+3,25", "+347,3", "416,0"], ["2", "21", "11.598,1", "+0,79", "+91,1", "291,8"],
               ["3", "21", "11.952,8", "+1,80", "+214,2", "408,0"], ["4", "21", "12.141,4", "+1,11", "+134,1", "207,3"],
               ["5", "21", "12.327,8", "−0,54", "−67,0", "236,6"], ["6", "21", "12.456,3", "−1,39", "−172,6", "187,8"],
               ["7", "21", "12.620,4", "−2,17", "−273,4", "287,9"], ["8", "21", "12.874,4", "−2,54", "−326,9", "352,8"],
               ["9", "21", "13.140,7", "−2,86", "−375,0", "474,4"], ["10 (más alta)", "22", "13.588,9", "−3,24", "−443,5", "455,4"]],
              "SARIMAX, horizonte de 7 días, conjunto de prueba (Tabla 4.10). Sesgo = pronóstico menos observado.", destacar=[9]),
            P("El sesgo agregado de SARIMAX a siete días es −0,57%, casi insesgado. Separado por nivel, en cambio, sobrestima 2,02% el quintil de días más bajos y subestima 3,05% el de días más altos: una brecha de 5,07 puntos, y en el decil superior subestima 443,5 MW. Es **reversión a la media**, propia de los pronósticos puntuales de tendencia central: el modelo conserva el centro de la serie y atenúa las desviaciones en ambas direcciones. Eso minimiza el error promedio, pero reduce justo el ẑ de los días que el criterio debe marcar: recorta la punta de los días cuya punta es el objeto de la detección."),
            P("No es un defecto de SARIMAX. Las brechas entre quintiles extremos son 5,07 puntos en SARIMAX, 4,84 en CatBoost, 5,83 en Prophet y 8,66 en la LSTM: tres familias con el mismo comportamiento. Con el horizonte, la brecha crece en los modelos que usan la dinámica reciente (SARIMAX de 3,75 a 5,07; CatBoost de 4,10 a 4,84), se mantiene en Prophet (de 5,98 a 5,83) y hasta baja en la LSTM (de 10,64 a 8,66)."),
            N("Por qué pasa: las funciones de pérdida habituales, como el error cuadrático o el absoluto, llevan el ajuste hacia la zona central de la distribución, donde están casi todos los datos. Los pocos días extremos pesan poco en el promedio que se minimiza, así que un modelo puede tener un error medio bajo y fallar en la cola (apartado 2.5.1).", "La explicación teórica", "defensa"),
        ],
    },
    {
        "id": "alerta",
        "titulo": "11. El umbral de alerta k_{a} y el esquema",
        "resumen": "Dos umbrales para dos preguntas: qué es un peak (k_{e}) y cuándo conviene avisar (k_{a}).",
        "ref": "En la tesis: apartados 3.10, 4.4.4, 4.5.2 y 4.5.3 · Tablas 4.11 y 4.12",
        "bloques": [
            P("k_{e} = 1,75 define el fenómeno y queda fijo, para que los resultados sean comparables. k_{a} responde otra pregunta, y dos razones obligan a separarlos. Una es operacional: el costo es asimétrico, porque no anticipar un evento es peor que una falsa alarma. La otra es estadística: el pronóstico atenúa los días altos, así que un umbral calibrado sobre la serie observada no se traslada a la serie pronosticada."),
            P("El procedimiento: en validación (2025) se evalúa una rejilla de k_{a} entre −1,00 y 2,50 con paso de 0,05, se elige el valor que maximiza el F_{1} y se aplica sin cambios a la prueba. Calibrar sobre la prueba invalidaría la evaluación. k_{a} es un parámetro del esquema: no cambia la definición de peak, las etiquetas ni la comparación entre modelos."),
            T(["Modelo", "k_{a}", "VP", "FP", "FN", "Precisión", "Exhaustividad", "F₁"],
              [["SARIMAX", "+0,65", "24", "219", "46", "0,099", "0,343", "0,153"],
               ["CatBoost", "+0,35", "42", "357", "28", "0,105", "0,600", "0,179"],
               ["Prophet", "+0,60", "44", "285", "26", "0,134", "0,629", "0,221"],
               ["LSTM", "+0,50", "28", "316", "42", "0,081", "0,400", "0,135"],
               ["Persistencia", "+0,70", "35", "801", "35", "0,042", "0,500", "0,077"],
               ["Estacional ingenuo", "+0,95", "10", "214", "60", "0,045", "0,143", "0,068"]],
              "Calibración en validación, 2025: 10 eventos y 70 oportunidades (Tabla 4.11)."),
            P("Todos los modelos alcanzan su mejor detección muy por debajo de 1,75: los cuatro predictivos entre 0,35 y 0,65, un desplazamiento de unas 1,2 unidades de dispersión que es la contrapartida operacional del recorte del hallazgo. El máximo es una región amplia y no un punto aislado, así que la elección no es sensible a cambios menores del valor."),
            T(["Modelo", "k_{a}", "VP", "FP", "FN", "Precisión", "Exhaustividad", "F₁", "Eventos"],
              [["CatBoost", "+0,35", "24", "39", "32", "0,381", "0,429", "0,403", "6 de 8"],
               ["SARIMAX", "+0,65", "24", "93", "32", "0,205", "0,429", "0,277", "7 de 8"],
               ["Prophet", "+0,60", "19", "81", "37", "0,190", "0,339", "0,244", "3 de 8"],
               ["Estacional ingenuo", "+0,95", "14", "119", "42", "0,105", "0,250", "0,148", "2 de 8"],
               ["Persistencia", "+0,70", "32", "429", "24", "0,069", "0,571", "0,124", "8 de 8"],
               ["LSTM", "+0,50", "1", "19", "55", "0,050", "0,018", "0,026", "1 de 8"]],
              "Prueba, enero a julio de 2026, con el umbral calibrado en validación (Tabla 4.12).", destacar=[0]),
            P("La calibración se traslada: CatBoost logra un F_{1} de 0,403, frente a 0,407 si el umbral se hubiera elegido mirando la prueba, apenas 0,004 de diferencia. El esquema anticipa 6 de 8 eventos con 39 falsas alarmas, una tasa de activación de 4,2%. Frente a la persistencia, que anticipa los 8 con 429 falsas alarmas, reduce las falsas alarmas en 90,9% a cambio de dos eventos; SARIMAX anticipa 7, con 93."),
            P("Por horizonte, SARIMAX parte con un F_{1} de 0,438 a un día y baja a 0,200 al séptimo. CatBoost parte en 0,400, baja a 0,333 y 0,308 en los días 2 y 3, sube a 0,462 en los días 5 y 6 y cierra en 0,455. Desde el cuarto día CatBoost queda siempre arriba; en los tres primeros, con 8 eventos por horizonte, un caso mueve la exhaustividad en 0,125 y no hay preferencia clara. Este resultado solo es visible porque se evaluó la trayectoria completa."),
            N("El modelo se eligió por F_{1} y no por MAE, porque el objetivo general es anticipar eventos y la exactitud está disociada de la detección: CatBoost se equivoca 85,2 MW más que SARIMAX, pero detecta mejor. Limitación declarada: la elección se hizo mirando la prueba, así que su desempeño se lee como optimista; en validación el mayor F_{1} habría sido el de Prophet (0,221 frente a 0,179)."),
        ],
    },
    {
        "id": "herramientas",
        "titulo": "12. Herramientas y metodología de trabajo",
        "resumen": "Python en Google Colab, con bibliotecas versionadas, y CRISP-DM para ordenar el proceso.",
        "ref": "En la tesis: apartados 3.2 y 3.11 · Tabla 3.8",
        "bloques": [
            T(["Biblioteca", "Versión", "Uso en el estudio"],
              [["pandas", "2.2.3", "Manipulación de la serie y de las tablas"],
               ["numpy", "2.1.3", "Cálculo numérico"],
               ["statsmodels", "0.15.0", "SARIMAX y pruebas de Dickey-Fuller, KPSS y Ljung-Box"],
               ["scikit-learn", "1.6.1", "Tipificación y métricas auxiliares"],
               ["catboost", "1.2.10", "Potenciación del gradiente"],
               ["prophet", "1.4.0", "Modelo aditivo descomponible"],
               ["tensorflow", "2.21.0", "Red LSTM"],
               ["scipy", "1.16.3", "Distribución t de Student para Diebold-Mariano"],
               ["matplotlib", "3.10.0", "Figuras"],
               ["holidays", "0.105", "Feriados legales de Chile"]],
              "Tabla 3.8 de la tesis. Python 3.13.16 sobre Google Colaboratory."),
            H3("CRISP-DM en la tesis"),
            L("**Comprensión del negocio:** Capítulo I y la normativa del SEN, que fijan la magnitud relevante, las métricas exigidas y el horizonte.",
              "**Comprensión de los datos:** apartados 3.3 y 3.4, con la fuente, el contraste contra la CNE, las ocho pruebas de validación y la ventana de estudio.",
              "**Preparación de los datos:** apartados 3.5, 3.6 y 3.7, con el criterio de peak, las predictoras y la partición; aquí se concentran las decisiones propias del estudio.",
              "**Modelado:** apartado 3.8, con la configuración de los cuatro modelos y las dos referencias.",
              "**Evaluación:** apartado 3.9, con el backtesting, las métricas y Diebold-Mariano.",
              "**Despliegue:** apartado 3.10, con el esquema predictivo y el tablero."),
            P("CRISP-DM es iterativo, no lineal: un hallazgo de una fase puede obligar a volver a la anterior. Se eligió porque es independiente de la herramienta y del sector, y porque sigue siendo el proceso más usado en proyectos de ciencia de datos, lo que hace comparable el trabajo."),
        ],
    },
]

# ---------------------------------------------------------------------------
# PREGUNTAS DE ALTERNATIVAS ("correcta" es el índice de la opción correcta, desde 0)
# ---------------------------------------------------------------------------
PREGUNTAS_ALTERNATIVAS = [
    {"tema": "Estacionariedad",
     "pregunta": "En la serie original, la prueba ADF da p = 0,642 y la KPSS p = 0,010. ¿Qué se concluye?",
     "opciones": ["Que la serie es estacionaria según ambas pruebas.",
                  "Que no es estacionaria según ambas: ADF no rechaza la raíz unitaria y KPSS rechaza la estacionariedad.",
                  "Que las pruebas se contradicen y el diagnóstico queda abierto.",
                  "Que la serie solo necesita una diferencia estacional."],
     "correcta": 1,
     "explicacion": "ADF tiene como hipótesis nula la raíz unitaria: con p = 0,642 no se rechaza, así que no es estacionaria. KPSS tiene como nula la estacionariedad: con p = 0,010 se rechaza. Dos hipótesis opuestas que llegan a lo mismo dan un diagnóstico firme. En la primera diferencia se invierten: ADF p < 0,001 y KPSS p > 0,100.",
     "pista": "Fíjate en la hipótesis nula de cada prueba.", "si_acierta": "Exacto.", "si_falla": "No exactamente."},
    {"tema": "Estacionariedad",
     "pregunta": "¿Qué orden de diferenciación se adoptó y por qué?",
     "opciones": ["d = 1 y D = 0: con una diferencia regular ambas pruebas ya concluyen estacionariedad, y la estacional no cambia el diagnóstico.",
                  "d = 0 y D = 1: el ciclo semanal exige una diferencia estacional.",
                  "d = 2 y D = 0: la serie tiene una tendencia cuadrática.",
                  "d = 1 y D = 1: para eliminar a la vez la tendencia y el ciclo semanal."],
     "correcta": 0,
     "explicacion": "En la primera diferencia, ADF da −13,501 (p < 0,001) y KPSS 0,032 (p > 0,100). Con la diferencia regular y estacional también es estacionaria, pero eso no agrega nada, y diferenciar de más es un problema (sobrediferenciación). De ahí SARIMAX(2,1,2)(1,0,1)₇.",
     "pista": "Busca la menor cantidad de diferencias con la que ambas pruebas coinciden.", "si_acierta": "Correcto.", "si_falla": "Ese no es el orden."},
    {"tema": "Estacionariedad",
     "pregunta": "Si D = 0, ¿por qué el modelo tiene términos estacionales (1,0,1)₇?",
     "opciones": ["Porque la primera diferencia conserva autocorrelaciones altas en los rezagos 7, 14, 21 y 28 (de 0,665 a 0,607): la diferencia regular no agota el ciclo semanal.",
                  "Porque Prophet necesitaba los mismos términos para poder compararse.",
                  "Porque así lo exige la Norma Técnica.",
                  "Porque la prueba KPSS rechazó la estacionariedad de la primera diferencia."],
     "correcta": 0,
     "explicacion": "La serie original ya mostraba el patrón semanal: 0,878 en el rezago 7, más que el 0,835 del rezago 1. Diferenciar quita la tendencia, pero el patrón semanal sigue, así que se modela con un AR y un MA estacionales de período 7 en vez de diferenciarlo. El término ar.S.L7 resultó el más fuerte del modelo (z = 40,335). KPSS no rechazó la estacionariedad de la primera diferencia (p > 0,100).",
     "pista": "Mira qué pasa con la ACF en los múltiplos de 7 después de diferenciar.", "si_acierta": "Bien visto.", "si_falla": "No del todo."},
    {"tema": "Criterio",
     "pregunta": "En el criterio de peak, ¿qué representa el factor f?",
     "opciones": ["La demanda media de los últimos 90 días.",
                  "El promedio, en las últimas ocho semanas, del cociente entre la demanda del mismo día de la semana y su nivel base.",
                  "La desviación estándar de las desviaciones relativas.",
                  "El porcentaje de días hábiles del mes."],
     "correcta": 1,
     "explicacion": "f(t) = (1/8) Σ y(t−7s) / b(t−7s), con s de 1 a 8. Multiplicado por el nivel base da el nivel esperado E = b · f, así una misma desviación significa lo mismo un martes que un domingo. Prueba de que funciona: los 127 eventos se reparten parejo entre los días de la semana.",
     "pista": "Es lo que corrige el nivel base según el día de la semana.", "si_acierta": "Eso es.", "si_falla": "Todavía no."},
    {"tema": "Criterio",
     "pregunta": "¿Por qué el criterio no se puede calcular antes del 24 de junio de 2018?",
     "opciones": ["Porque antes no había datos del SEN.",
                  "Porque su cadena de ventanas retrocede 174 días: 90 de la dispersión, 56 del factor semanal y 28 del nivel base.",
                  "Porque el rezago anual de las predictoras necesita 364 días.",
                  "Porque esos días se usaron para calibrar kₑ."],
     "correcta": 1,
     "explicacion": "σ usa 90 días de desviaciones relativas; cada una necesita su factor f, que mira ocho semanas atrás (56 días); y cada f necesita niveles base de 28 días: 90 + 56 + 28 = 174. El rezago anual (lag_364) es otra cosa: explica por qué las observaciones utilizables para modelar empiezan recién el 7 de enero de 2019.",
     "pista": "Suma las ventanas del criterio, encadenadas.", "si_acierta": "Justo eso.", "si_falla": "Esa explica otra fecha."},
    {"tema": "Criterio",
     "pregunta": "En la Ecuación 3.4, ¿qué componente del criterio corresponde al día objetivo y no al origen?",
     "opciones": ["El nivel base b.", "La dispersión σ.", "El factor del día de la semana f.", "Ninguno: todos quedan congelados en el origen."],
     "correcta": 2,
     "explicacion": "b y σ se evalúan en T + 1 y quedan fijos para los siete días. f(T+h) sí es del día objetivo, porque solo necesita datos hasta y(T+h−7), disponibles en el origen para todo h ≤ 7. Por eso el horizonte de siete días calza con el ciclo semanal sin fuga de información.",
     "pista": "¿Cuál de los tres mira ocho semanas hacia atrás?", "si_acierta": "Correcto.", "si_falla": "Ese queda congelado en el origen."},
    {"tema": "Diebold-Mariano",
     "pregunta": "¿Por qué la varianza del estadístico de Diebold-Mariano incorpora autocovarianzas hasta el rezago h − 1?",
     "opciones": ["Porque las trayectorias de orígenes consecutivos se superponen y las diferencias de pérdida quedan autocorrelacionadas; suponer independencia subestimaría la varianza.",
                  "Porque la prueba solo es válida para el horizonte de un día.",
                  "Porque así se corrigen las comparaciones múltiples.",
                  "Porque la serie original no es estacionaria."],
     "correcta": 0,
     "explicacion": "Un pronóstico a h días desde T y otro desde T + 1 comparten información, así que sus errores se parecen. Ignorar esa dependencia achica la varianza estimada, infla el estadístico y hace rechazar la hipótesis nula más de lo debido. Las comparaciones múltiples se corrigen aparte, con Holm.",
     "pista": "Piensa en qué comparten dos pronósticos emitidos desde orígenes vecinos.", "si_acierta": "Muy bien.", "si_falla": "No es eso."},
    {"tema": "Diebold-Mariano",
     "pregunta": "¿Qué hace la corrección de Harvey, Leybourne y Newbold (1997)?",
     "opciones": ["Ajusta el estadístico DM por muestra pequeña según el horizonte, y lo compara con una t de Student con m − 1 grados de libertad.",
                  "Ajusta los valores p por haber hecho muchas comparaciones.",
                  "Cambia la pérdida absoluta por la cuadrática.",
                  "Elimina los días con eventos extremos antes de comparar."],
     "correcta": 0,
     "explicacion": "DM* = DM · √[(m + 1 − 2h + h(h − 1)/m) / m]. Su efecto es marginal en h = 1 y apreciable en h = 7. La corrección por comparaciones múltiples es la de Holm, que es otra cosa.",
     "pista": "Su fórmula depende de m y de h.", "si_acierta": "Exacto.", "si_falla": "Esa es otra corrección."},
    {"tema": "Diebold-Mariano",
     "pregunta": "Con la corrección de Holm, ¿qué diferencia deja de ser significativa en el séptimo horizonte?",
     "opciones": ["SARIMAX frente a CatBoost (p = 0,010).", "SARIMAX frente a Prophet.", "Prophet frente al estacional ingenuo.", "La LSTM frente al estacional ingenuo."],
     "correcta": 0,
     "explicacion": "Caen tres diferencias: en h = 1, Prophet frente a la persistencia (0,019) y las dos referencias entre sí (0,040); en h = 7, SARIMAX frente a CatBoost (0,010). Prophet frente al estacional ingenuo nunca fue significativa (p = 0,961, 0,772 y 0,648), así que no puede dejar de serlo.",
     "pista": "Es la ventaja que ya venía estrechándose con el horizonte.", "si_acierta": "Así es.", "si_falla": "Revisa la Tabla 4.8."},
    {"tema": "Modelos",
     "pregunta": "¿Por qué CatBoost usa siete modelos, uno por horizonte, en vez de una estrategia recursiva?",
     "opciones": ["Porque la recursiva acumula el error de los pasos previos y obliga a construir predictoras sobre valores estimados.",
                  "Porque CatBoost no admite más de 42 variables.",
                  "Porque así se entrena más rápido.",
                  "Porque la Norma Técnica exige un modelo por día."],
     "correcta": 0,
     "explicacion": "La estimación directa ajusta un modelo independiente por horizonte sobre la misma matriz de predictoras, cambiando solo la variable objetivo; la dependencia de h queda en los parámetros, y por eso el horizonte no entra como variable. La LSTM también estima los siete horizontes de forma directa, pero en un solo modelo con siete salidas.",
     "pista": "Piensa en qué pasa al reinyectar un pronóstico como si fuera un dato.", "si_acierta": "Correcto.", "si_falla": "No es esa la razón."},
    {"tema": "Modelos",
     "pregunta": "¿De dónde salen los 4.583 parámetros entrenables de la LSTM?",
     "opciones": ["4.352 de la capa LSTM (4 × [32 × (32 + 1) + 32]) y 231 de la capa densa (32 × 7 + 7).",
                  "Uno por cada día del entrenamiento.",
                  "De multiplicar las 42 predictoras por los 109 eventos del entrenamiento.",
                  "De 28 días de ventana por 32 unidades por 5 capas."],
     "correcta": 0,
     "explicacion": "Cada una de las cuatro transformaciones de la LSTM (las tres compuertas y el candidato C̃) tiene pesos para el estado oculto (32 × 32), para la entrada (32 × 1) y sesgos (32): 1.088 × 4 = 4.352. La capa de salida suma 32 × 7 pesos y 7 sesgos: 231. La tesis advierte que 2.557 observaciones son una muestra reducida para 4.583 parámetros.",
     "pista": "Una entrada, 32 unidades y 7 salidas.", "si_acierta": "Bien calculado.", "si_falla": "Haz la cuenta por capa."},
    {"tema": "Modelos",
     "pregunta": "Si se evalúan juntos validación y prueba, la LSTM obtiene R² = 0,484. ¿Por qué ese número engaña?",
     "opciones": ["Porque juntar dos períodos de nivel distinto infla la varianza total, el denominador del R², y reproducir solo la diferencia de nivel ya da un valor favorable.",
                  "Porque el R² no se puede calcular sobre más de 365 días.",
                  "Porque en validación la red tenía más eventos.",
                  "Porque el R² ignora los errores grandes."],
     "correcta": 0,
     "explicacion": "Por separado, en la prueba la red tiene R² = −0,667: peor que predecir siempre la media. Juntando los 577 días sale 510,3 MW de error y R² = 0,484. Por eso las métricas se reportan por período.",
     "pista": "Mira el denominador del R².", "si_acierta": "Exacto.", "si_falla": "No es eso."},
    {"tema": "Modelos",
     "pregunta": "¿Qué indica que la menor raíz de media móvil de SARIMAX sea 1,006?",
     "opciones": ["Que está casi sobre el círculo unitario, la firma habitual de una sobrediferenciación: no invalida el modelo, pero el orden de diferenciación admite revisión.",
                  "Que el modelo no es estacionario y hay que diferenciar otra vez.",
                  "Que los residuos son normales.",
                  "Que los términos de media móvil deben eliminarse porque no son significativos."],
     "correcta": 0,
     "explicacion": "Que las raíces queden fuera del círculo unitario garantiza estacionariedad e invertibilidad, y se cumple, pero 1,006 está en el borde. Es llamativo porque ADF y KPSS sí pedían una diferencia regular. Los términos ma.L1 y ma.L2 son significativos (p < 0,001 y 0,002), y los residuos no son normales (curtosis 6,37).",
     "pista": "¿Qué suele indicar una raíz MA pegada a 1?", "si_acierta": "Muy bien.", "si_falla": "No del todo."},
    {"tema": "Detección",
     "pregunta": "¿Por qué la detección se mide con precisión, exhaustividad y F₁ y no con exactitud (accuracy)?",
     "opciones": ["Porque las clases están desbalanceadas: un modelo que nunca avisa acertaría en casi todos los pronósticos.",
                  "Porque la exactitud no se puede calcular por horizonte.",
                  "Porque la Norma Técnica prohíbe usar la exactitud.",
                  "Porque el F₁ siempre es mayor que la exactitud."],
     "correcta": 0,
     "explicacion": "Con 56 oportunidades entre 1.484 pronósticos, no avisar nunca daría una exactitud cercana a 96%. El F₁ es una media armónica, que castiga cuando una de las dos métricas es muy baja: alertar siempre daría exhaustividad 1, precisión 0,038 y F₁ 0,073.",
     "pista": "Piensa en cuántos días no son evento.", "si_acierta": "Correcto.", "si_falla": "Revisa el desbalance."},
]

# ---------------------------------------------------------------------------
# PREGUNTAS ABIERTAS, con una respuesta sugerida
# ---------------------------------------------------------------------------
PREGUNTAS_ABIERTAS = [
    {"tema": "Estacionariedad", "pregunta": "¿Qué diferencia hay entre ADF y KPSS, y por qué usaron las dos?",
     "respuesta": "Tienen hipótesis nulas opuestas: ADF supone raíz unitaria (no estacionaria) y KPSS supone estacionariedad. Si coinciden, la conclusión es firme; si se contradicen, la serie está en un caso intermedio. En la tesis coinciden en las tres series: la original no es estacionaria (ADF p = 0,642; KPSS p = 0,010) y la primera diferencia sí (ADF p < 0,001; KPSS p > 0,100)."},
    {"tema": "Estacionariedad", "pregunta": "¿Cómo determinaron los órdenes (2,1,2)(1,0,1)₇?",
     "respuesta": "d = 1 y D = 0 salen de ADF y KPSS. Los órdenes p, q, P y Q se orientaron con la PACF y la ACF, complementadas con el criterio de Akaike sobre el entrenamiento. El período 7 responde al patrón semanal, que sigue presente en la primera diferencia (0,665 en el rezago 7). Todo se fijó con el entrenamiento, antes de ver la prueba."},
    {"tema": "Estacionariedad", "pregunta": "¿Qué significa que SARIMAX no pase la prueba de Ljung-Box?",
     "respuesta": "Que los residuos conservan autocorrelación en los rezagos 7, 14 y 28 (p < 0,001): el componente estacional (1,0,1)₇ no agotó toda la estructura semanal. No invalida los resultados, que se miden fuera de muestra, pero indica que un estacional de orden superior podría mejorar el modelo. La tesis lo declara junto con la no normalidad (curtosis 6,37) y la heterocedasticidad."},
    {"tema": "Criterio", "pregunta": "¿Por qué usaron la mediana de 28 días y no la media?",
     "respuesta": "Porque la mediana es robusta frente a los propios eventos: un peak reciente no sube el nivel base ni tapa los eventos siguientes. Y 28 días son cuatro semanas completas, con el mismo número de cada día de la semana, así que el nivel no queda sesgado por el día en que se calcula."},
    {"tema": "Criterio", "pregunta": "¿Por qué el factor del día de la semana puede usar el día objetivo sin fuga de información?",
     "respuesta": "Porque f(T+h) promedia ocho semanas hacia atrás y solo necesita datos hasta y(T+h−7). Para todo horizonte de hasta siete días, ese dato ya existe en el origen. Por eso el horizonte de siete días calza con el ciclo semanal; con más días no se podría."},
    {"tema": "Criterio", "pregunta": "¿Calibrar kₑ sobre la serie completa no contamina la prueba?",
     "respuesta": "Es una limitación declarada, pero acotada. La calibración no usa el desempeño de ningún modelo, así que no favorece a ninguno. Recalibrado solo con el entrenamiento, 1,75 da 4,57% de eventos y toda la rejilla difiere en menos de un punto, así que se habría elegido el mismo valor. Y como las etiquetas usan solo días anteriores, los eventos de prueba serían idénticos."},
    {"tema": "Datos y evaluación", "pregunta": "¿Por qué no usaron una partición aleatoria o validación cruzada?",
     "respuesta": "Porque en series temporales mezclar días al azar mete información del futuro en el entrenamiento y da un desempeño optimista. La partición es estrictamente temporal (2018 a 2024, 2025 y enero a julio de 2026) y la evaluación es un backtesting de origen móvil, que reproduce lo que el operador sabe en cada momento."},
    {"tema": "Datos y evaluación", "pregunta": "¿Por qué reajustaron los modelos cada siete orígenes y no en cada uno?",
     "respuesta": "Por costo computacional: reajustar en cada origen multiplicaría por siete el tiempo de cómputo. El origen igual avanza cada día, y entre reajustes cada modelo recibe los datos nuevos por su estado, sus predictoras o su ventana. Se supone que los parámetros no cambian mucho entre días consecutivos, aunque la tesis declara que ese supuesto no se contrastó."},
    {"tema": "Datos y evaluación", "pregunta": "¿Por qué reportan las métricas por horizonte?",
     "respuesta": "Porque el desempeño se degrada con la anticipación, y un promedio de los siete días ocultaría hasta cuándo sirve el pronóstico. Por ejemplo, el error de SARIMAX crece 23,1% del día 1 al 4 y solo 3,5% más hasta el 7. El promedio se informa solo como resumen."},
    {"tema": "Datos y evaluación", "pregunta": "¿Por qué el MAE es la métrica principal?",
     "respuesta": "Porque MAE, RMSE y BIAS son los indicadores que la Norma Técnica de Coordinación y Operación exige minimizar en las proyecciones de demanda, y el MAE se lee directo en MW. Además, CatBoost y la LSTM se entrenaron con pérdida MAE y la prueba de Diebold-Mariano usa la pérdida absoluta, así que todo el diseño es coherente."},
    {"tema": "Diebold-Mariano", "pregunta": "Explique la prueba de Diebold-Mariano con sus palabras.",
     "respuesta": "Compara dos modelos pronóstico a pronóstico. Para cada uno se resta el error absoluto de un modelo menos el del otro, y se ve si el promedio de esas diferencias se aleja de cero más de lo que permite su variabilidad. La hipótesis nula es igual capacidad predictiva. Como las trayectorias se superponen, la varianza incluye autocovarianzas hasta h − 1, y se aplica la corrección de Harvey para muestras pequeñas, con una t de Student."},
    {"tema": "Diebold-Mariano", "pregunta": "¿Para qué sirve la corrección de Holm y qué cambió con ella?",
     "respuesta": "Con 15 pares por horizonte, algunas diferencias saldrían significativas por azar. Holm ordena los valores p y los compara con umbrales cada vez menos exigentes (α/n, α/(n − 1) y así), deteniéndose en el primero que no rechaza. Cayeron tres diferencias: Prophet frente a la persistencia y las dos referencias entre sí en h = 1, y SARIMAX frente a CatBoost en h = 7."},
    {"tema": "Modelos", "pregunta": "¿Por qué CatBoost y no XGBoost o LightGBM?",
     "respuesta": "Por la potenciación ordenada: CatBoost calcula el gradiente de cada observación con un modelo que no la vio, lo que evita el desplazamiento de predicción de las otras implementaciones. Además trata de forma nativa los valores faltantes y las variables categóricas, como el día de la semana y el mes, y captura relaciones no lineales sin declararlas."},
    {"tema": "Modelos", "pregunta": "¿Por qué los árboles no extrapolan y qué consecuencia tiene?",
     "respuesta": "Porque la predicción de un árbol es el promedio de las observaciones de entrenamiento que caen en una hoja: no puede entregar valores fuera del rango visto. Con la prueba por encima del máximo del entrenamiento, es una diferencia estructural frente a SARIMAX, que trabaja con la serie diferenciada, y frente a Prophet, que proyecta su tendencia. El reajuste cada siete días la mitiga al incorporar el nuevo régimen."},
    {"tema": "Modelos", "pregunta": "¿Por qué la LSTM funcionó en validación y falló en la prueba?",
     "respuesta": "En validación quedó tercera (343,7 MW); en prueba se equivocó 797,1 MW, 131,9% más. La mediana de la prueba supera en 391,9 MW el máximo del entrenamiento, y una red que aprende la serie en su escala queda acotada a los niveles que vio. Se suman la implementación (solo la serie, sin calendario, configuración fija y una semilla) y una muestra chica: 2.557 observaciones para 4.583 parámetros. La detención temprana operó bien, pero su validación interna es del mismo régimen."},
    {"tema": "Detección", "pregunta": "Si el sesgo de SARIMAX es casi cero, ¿por qué detecta tan mal?",
     "respuesta": "Porque el sesgo agregado (−0,57% a siete días) esconde un sesgo que depende del nivel: sobrestima 2,02% los días más bajos y subestima 3,05% los más altos. Es reversión a la media, propia de los pronósticos de tendencia central. Al recortar los días altos, baja justo el ẑ de los días que el criterio debe marcar."},
    {"tema": "Detección", "pregunta": "¿Cómo calibraron el umbral de alerta y por qué no es hacer trampa?",
     "respuesta": "En validación (2025), con una rejilla de −1,00 a 2,50 cada 0,05, eligiendo el valor que maximiza el F₁; luego se aplica sin cambios en la prueba. No toca kₑ ni las etiquetas. Y se verificó que se traslada: CatBoost logra F₁ 0,403 en la prueba y 0,407 con el óptimo mirando la prueba."},
    {"tema": "Detección", "pregunta": "¿Por qué no entrenaron un clasificador de peaks directamente?",
     "respuesta": "Porque SARIMAX y Prophet entregan valores, no probabilidades, y la comparación entre familias se perdería. En dos etapas, cada modelo pronostica la demanda y después se aplica el mismo criterio a todos: ninguno ve las etiquetas, y la detección hereda la estructura por horizonte."},
]

# ---------------------------------------------------------------------------
# Plantilla
# ---------------------------------------------------------------------------
PLANTILLA = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Guía técnica de la tesis</title>
<meta name="description" content="Todo lo técnico de la tesis sobre peaks extremos de demanda en el SEN: criterio, estacionariedad, modelos, Diebold-Mariano y umbrales, con preguntas para practicar.">
<style>
:root {
  --navy: #003784; --blue: #3386CD; --celeste: #5CB9E1;
  --bg: #F4F6FA; --surface: #FFFFFF; --ink: #15203A; --muted: #586178; --line: #DCE2EC;
  --accent: #003784; --accent-soft: #E6EEF9; --btn: #003784; --btn-ink: #FFFFFF;
  --ok: #1D7447; --ok-bg: #E5F3EB; --bad: #B3261E; --bad-bg: #FBE9E8;
  --warn: #9A5B00; --warn-bg: #FDF1DC;
  --radius: 14px;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #0D1320; --surface: #161F31; --ink: #E7ECF5; --muted: #A2ACC0; --line: #2A3650;
    --accent: #8DBBEF; --accent-soft: #1C2A44; --btn: #3B78C8; --btn-ink: #FFFFFF;
    --ok: #63CC9C; --ok-bg: #11301F; --bad: #F2938C; --bad-bg: #3A1817;
    --warn: #F2B65C; --warn-bg: #352610;
    color-scheme: dark;
  }
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; scroll-behavior: smooth; }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
body { margin: 0; background: var(--bg); color: var(--ink); font: 16px/1.6 system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
a { color: var(--accent); }
.top { max-width: 1120px; margin: 0 auto; padding: 28px 16px 8px; }
.volver { display: inline-block; font-size: 14.5px; font-weight: 600; margin-bottom: 14px; text-decoration: none; }
.volver:hover { text-decoration: underline; }
.eyebrow { margin: 0; font-size: 13px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--blue); }
h1 { margin: 4px 0 6px; font-size: 32px; line-height: 1.15; color: var(--accent); }
.tesis { margin: 0 0 6px; color: var(--muted); font-size: 15px; }
.intro { margin: 10px 0 0; max-width: 760px; }
.layout { max-width: 1120px; margin: 0 auto; padding: 16px 16px 56px; display: grid; grid-template-columns: minmax(0, 1fr); gap: 24px; }
.indice-movil { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 4px 16px; }
.indice-movil summary { cursor: pointer; font-weight: 700; padding: 10px 0; min-height: 44px; display: flex; align-items: center; }
.indice-lateral { display: none; }
.indice ol { list-style: none; margin: 0; padding: 0 0 8px; }
.indice li a { display: block; padding: 6px 10px; border-radius: 8px; text-decoration: none; color: var(--ink); font-size: 14.5px; line-height: 1.35; }
.indice li a:hover { background: var(--accent-soft); }
.indice li a[aria-current="true"] { background: var(--accent-soft); color: var(--accent); font-weight: 700; }
@media (min-width: 1000px) {
  .layout { grid-template-columns: 260px minmax(0, 1fr); }
  .indice-movil { display: none; }
  .indice-lateral { display: block; position: sticky; top: 16px; align-self: start; max-height: calc(100vh - 32px); overflow: auto; background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 12px 8px; }
  .indice-lateral .titulo-indice { margin: 4px 10px 8px; font-size: 13px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); }
}
main { min-width: 0; }
.seccion { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); padding: 24px 24px 20px; margin: 0 0 20px; scroll-margin-top: 16px; }
.seccion h2 { margin: 0 0 6px; font-size: 24px; line-height: 1.25; color: var(--accent); }
.seccion .resumen { margin: 0 0 4px; font-size: 17px; font-weight: 600; }
.seccion .ref { margin: 0 0 12px; font-size: 13.5px; color: var(--muted); }
.seccion h3 { margin: 24px 0 6px; font-size: 18.5px; line-height: 1.3; }
.seccion p { margin: 10px 0; max-width: 760px; }
.seccion ul { margin: 10px 0; padding-left: 22px; max-width: 760px; }
.seccion li { margin: 6px 0; }
code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: .9em; background: var(--accent-soft); padding: 1px 5px; border-radius: 5px; }
sub, sup { font-size: .72em; line-height: 0; }
.formula { margin: 14px 0; padding: 12px 16px; background: var(--accent-soft); border-radius: 10px; overflow-x: auto; }
.formula .expr { font-family: "Cambria Math", "STIX Two Math", "Latin Modern Math", "Times New Roman", serif; font-size: 18.5px; white-space: nowrap; }
.formula .etq { margin-top: 4px; font-size: 13.5px; color: var(--muted); }
.formula .expr { white-space: normal; }
.formula .parte { display: inline-block; white-space: nowrap; margin: 2px 2.2em 2px 0; }
.formula .parte:last-child { margin-right: 0; }
.formula .sans { font-family: system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif; }
.tabla { margin: 14px 0; overflow-x: auto; border: 1px solid var(--line); border-radius: 10px; }
.tabla table { border-collapse: collapse; width: 100%; font-size: 14.5px; }
.tabla th, .tabla td { padding: 8px 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
.tabla th { background: var(--accent-soft); font-weight: 700; white-space: nowrap; }
.tabla tr:last-child td { border-bottom: 0; }
.tabla td.num, .tabla th.num { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
.tabla tr.destacar td { font-weight: 700; background: var(--accent-soft); }
.tabla-nota { margin: -6px 0 14px; font-size: 13.5px; color: var(--muted); }
.nota { margin: 16px 0; padding: 12px 16px; border-radius: 10px; border-left: 4px solid var(--blue); background: var(--accent-soft); max-width: 760px; }
.nota.ojo { border-left-color: var(--warn); background: var(--warn-bg); }
.nota .etq { margin: 0 0 4px; font-size: 13px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--accent); }
.nota.ojo .etq { color: var(--warn); }
.nota p { margin: 0; }
/* Preguntas */
.tabs { display: grid; grid-template-columns: repeat(2, 1fr); gap: 4px; padding: 4px; background: var(--bg); border: 1px solid var(--line); border-radius: 12px; margin-top: 12px; max-width: 520px; }
.tabs button { appearance: none; border: 0; background: transparent; color: var(--ink); font: inherit; font-weight: 600; font-size: 15px; padding: 10px 6px; border-radius: 9px; cursor: pointer; min-height: 44px; }
.tabs button[aria-selected="true"] { background: var(--btn); color: var(--btn-ink); }
.panel { margin-top: 16px; }
.meta { display: flex; justify-content: space-between; align-items: center; gap: 12px; font-size: 14px; color: var(--muted); }
.barra { height: 6px; background: var(--line); border-radius: 99px; overflow: hidden; margin: 10px 0 16px; }
.barra > span { display: block; height: 100%; background: var(--blue); transition: width .3s; }
.chip { display: inline-block; font-size: 13px; font-weight: 600; color: var(--accent); background: var(--accent-soft); padding: 3px 10px; border-radius: 99px; }
.seccion h3.prompt { font-size: 19px; line-height: 1.4; margin: 12px 0 16px; outline: none; }
.seccion .lista-falladas { padding: 0; }
.opciones { display: grid; gap: 10px; }
.opcion { display: flex; gap: 12px; align-items: flex-start; text-align: left; width: 100%; padding: 12px 14px; border: 1.5px solid var(--line); border-radius: 12px; background: var(--surface); color: var(--ink); font: inherit; line-height: 1.45; cursor: pointer; }
.opcion .letra { flex: none; width: 28px; height: 28px; border-radius: 50%; display: grid; place-items: center; font-weight: 700; font-size: 14px; background: var(--accent-soft); color: var(--accent); }
.opcion .texto { padding-top: 2px; }
.opcion:hover:not(:disabled) { border-color: var(--blue); }
.opcion:disabled { cursor: default; }
.opcion:disabled:not(.ok):not(.mal) { opacity: .55; }
.opcion.ok { border-color: var(--ok); background: var(--ok-bg); }
.opcion.ok .letra { background: var(--ok); color: var(--surface); }
.opcion.mal { border-color: var(--bad); background: var(--bad-bg); }
.opcion.mal .letra { background: var(--bad); color: var(--surface); }
.feedback { margin-top: 16px; padding: 14px 16px; border-radius: 12px; border-left: 4px solid; outline: none; }
.feedback.ok { border-color: var(--ok); background: var(--ok-bg); }
.feedback.mal { border-color: var(--bad); background: var(--bad-bg); }
.feedback p { margin: 0; }
.feedback p + p { margin-top: 8px; }
.pista { margin: 14px 0 0; color: var(--muted); font-style: italic; }
.acciones { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px; align-items: center; }
.btn { appearance: none; border: 1.5px solid var(--btn); background: var(--btn); color: var(--btn-ink); font: inherit; font-weight: 600; font-size: 15px; padding: 10px 16px; border-radius: 10px; cursor: pointer; min-height: 44px; }
.btn.sec { background: transparent; color: var(--accent); border-color: var(--line); }
.btn:hover { filter: brightness(1.08); }
.tabs button:focus-visible, .btn:focus-visible, .opcion:focus-visible, .filtro:focus-visible, .indice a:focus-visible, .volver:focus-visible, summary:focus-visible { outline: 3px solid var(--celeste); outline-offset: 2px; }
.resultado { font-size: 46px; font-weight: 800; line-height: 1; color: var(--accent); margin: 8px 0 4px; outline: none; }
.lista-falladas { margin: 16px 0 0; padding: 0; list-style: none; display: grid; gap: 10px; }
.lista-falladas li { border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px; margin: 0; }
.lista-falladas p { margin: 6px 0 0; }
.muted { color: var(--muted); }
.filtros { display: flex; flex-wrap: wrap; gap: 8px; }
.filtro { appearance: none; border: 1.5px solid var(--line); background: var(--surface); color: var(--ink); font: inherit; font-size: 14px; font-weight: 600; padding: 6px 12px; border-radius: 99px; cursor: pointer; min-height: 36px; }
.filtro[aria-pressed="true"] { background: var(--btn); border-color: var(--btn); color: var(--btn-ink); }
.seccion h3.pregunta-abierta { font-size: 21px; line-height: 1.35; margin: 12px 0 4px; outline: none; }
.reloj { display: flex; align-items: center; gap: 12px; margin-top: 14px; }
.reloj .cuenta { font-variant-numeric: tabular-nums; font-weight: 700; font-size: 18px; min-width: 52px; }
.reloj .barra { flex: 1; margin: 0; }
.reloj.fin .cuenta { color: var(--bad); }
.respuesta-sugerida { margin-top: 16px; padding: 14px 16px; border-radius: 12px; background: var(--accent-soft); border-left: 4px solid var(--accent); }
.respuesta-sugerida p { margin: 0; }
.respuesta-sugerida .etq { font-size: 13px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--accent); margin-bottom: 6px; }
.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
footer { font-size: 13.5px; color: var(--muted); }
footer p { margin: 4px 0; }
@media (max-width: 520px) {
  h1 { font-size: 27px; }
  .seccion { padding: 18px 16px 14px; }
  .seccion h2 { font-size: 21px; }
  .formula .expr { font-size: 15.5px; }
  .seccion h3.prompt { font-size: 18px; }
  .seccion h3.pregunta-abierta { font-size: 19px; }
  .acciones .btn { flex: 1 1 auto; }
}
@media (prefers-reduced-motion: reduce) { .barra > span { transition: none; } }
</style>
</head>
<body>
<header class="top">
  <a class="volver" href="index.html">← Volver a la práctica</a>
  <p class="eyebrow">Ensayo de defensa</p>
  <h1>Guía técnica de la tesis</h1>
  <p class="tesis">__TITULO__</p>
  <p class="intro">Cada sección explica una parte técnica de la tesis: las fórmulas, las decisiones y sus razones, con las cifras tal como aparecen en ella y el apartado donde buscarlas. Al final hay preguntas técnicas para practicar, de alternativas y abiertas.</p>
</header>
<div class="layout">
  <details class="indice-movil indice"><summary>Índice</summary><nav aria-label="Índice">__INDICE__</nav></details>
  <aside class="indice-lateral indice"><p class="titulo-indice">Índice</p><nav aria-label="Índice">__INDICE__</nav></aside>
  <main>
__CONTENIDO__
    <section class="seccion" id="preguntas" aria-labelledby="titulo-preguntas">
      <h2 id="titulo-preguntas">13. Preguntas técnicas</h2>
      <p class="resumen">Para practicar lo de arriba: alternativas con explicación y preguntas abiertas como las de la comisión.</p>
      <div class="tabs" role="tablist" aria-label="Tipo de pregunta">
        <button type="button" role="tab" id="tab-alt" aria-controls="panel-alt" data-panel="alt">Alternativas</button>
        <button type="button" role="tab" id="tab-abi" aria-controls="panel-abi" data-panel="abi">Abiertas</button>
      </div>
      <div id="panel-alt" class="panel" role="tabpanel" aria-labelledby="tab-alt"></div>
      <div id="panel-abi" class="panel" role="tabpanel" aria-labelledby="tab-abi" hidden></div>
    </section>
    <footer>
      <p>Las cifras vienen de la tesis. Tu avance en las preguntas se guarda solo en este navegador.</p>
      <p>Página generada con generar_tecnica.py.</p>
    </footer>
  </main>
</div>
<script type="application/json" id="datos-preguntas">__DATOS__</script>
<script>
(function () {
  'use strict';
  var D = JSON.parse(document.getElementById('datos-preguntas').textContent);
  var Q = D.alternativas, A = D.abiertas;
  var LETRAS = ['A', 'B', 'C', 'D', 'E', 'F'];
  var PREFIJO = 'guia-tecnica:';
  var store = {
    get: function (k, d) { try { var v = localStorage.getItem(PREFIJO + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set: function (k, v) { try { localStorage.setItem(PREFIJO + k, JSON.stringify(v)); } catch (e) {} }
  };
  function barajar(a) { var b = a.slice(); for (var i = b.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = b[i]; b[i] = b[j]; b[j] = t; } return b; }
  function rango(n) { var r = []; for (var i = 0; i < n; i++) r.push(i); return r; }
  function h(tag, props) {
    var n = document.createElement(tag); props = props || {};
    Object.keys(props).forEach(function (k) {
      var v = props[k]; if (v === null || v === undefined || v === false) return;
      if (k === 'class') n.className = v; else if (k === 'text') n.textContent = v;
      else if (k.indexOf('on') === 0) n.addEventListener(k.slice(2), v);
      else n.setAttribute(k, v === true ? '' : String(v));
    });
    for (var i = 2; i < arguments.length; i++) agregar(n, arguments[i]);
    return n;
  }
  function agregar(n, c) {
    if (c === null || c === undefined || c === false) return;
    if (Array.isArray(c)) { c.forEach(function (x) { agregar(n, x); }); return; }
    n.appendChild(c.nodeType ? c : document.createTextNode(String(c)));
  }
  function boton(texto, fn, sec, extra) { var p = { class: 'btn' + (sec ? ' sec' : ''), type: 'button', text: texto, onclick: fn }; if (extra) Object.keys(extra).forEach(function (k) { p[k] = extra[k]; }); return h('button', p); }
  function enfocar(sel) { var e = document.querySelector(sel); if (e) e.focus(); }

  // ------------------------------------------------------------- índice activo
  var enlaces = {};
  document.querySelectorAll('.indice-lateral a').forEach(function (a) { enlaces[a.getAttribute('href').slice(1)] = a; });
  document.querySelectorAll('.indice-movil a').forEach(function (a) { a.addEventListener('click', function () { var d = document.querySelector('.indice-movil'); if (d) d.open = false; }); });
  var secciones = Array.prototype.slice.call(document.querySelectorAll('main .seccion'));
  var pendiente = false;
  function actualizarIndice() {
    pendiente = false;
    var actual = secciones.length ? secciones[0].id : null;
    for (var i = 0; i < secciones.length; i++) { if (secciones[i].getBoundingClientRect().top <= 140) actual = secciones[i].id; else break; }
    Object.keys(enlaces).forEach(function (id) { enlaces[id].setAttribute('aria-current', id === actual ? 'true' : 'false'); });
  }
  window.addEventListener('scroll', function () { if (!pendiente) { pendiente = true; requestAnimationFrame(actualizarIndice); } }, { passive: true });
  actualizarIndice();

  // ------------------------------------------------------------- pestañas de preguntas
  var panelActual = 'alt';
  function mostrarPanel(p) {
    panelActual = p === 'abi' ? 'abi' : 'alt';
    document.querySelectorAll('#preguntas [role=tab]').forEach(function (b) { var on = b.getAttribute('data-panel') === panelActual; b.setAttribute('aria-selected', on ? 'true' : 'false'); b.tabIndex = on ? 0 : -1; });
    document.getElementById('panel-alt').hidden = panelActual !== 'alt';
    document.getElementById('panel-abi').hidden = panelActual !== 'abi';
    if (panelActual !== 'abi') pararReloj();
    store.set('panel', panelActual);
  }
  document.querySelectorAll('#preguntas [role=tab]').forEach(function (b, i, todos) {
    b.addEventListener('click', function () { mostrarPanel(b.getAttribute('data-panel')); });
    b.addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      e.preventDefault(); var k = (i + 1) % todos.length; todos[k].focus(); mostrarPanel(todos[k].getAttribute('data-panel'));
    });
  });

  // ------------------------------------------------------------- alternativas
  var qz;
  function nuevoQuiz(indices) { qz = { orden: indices, pos: 0, aciertos: 0, falladas: [], fin: false, completo: indices.length === Q.length }; preparar(); pintarQuiz(); }
  function preparar() { var q = Q[qz.orden[qz.pos]]; qz.opciones = barajar(rango(q.opciones.length)); qz.respondida = null; qz.pista = false; }
  function responder(i) {
    if (qz.respondida !== null) return;
    var idx = qz.orden[qz.pos]; qz.respondida = i;
    if (i === Q[idx].correcta) qz.aciertos++; else qz.falladas.push(idx);
    pintarQuiz(); enfocar('#panel-alt .feedback');
  }
  function siguiente() {
    if (qz.pos < qz.orden.length - 1) { qz.pos++; preparar(); pintarQuiz(); enfocar('#panel-alt .prompt'); }
    else { qz.fin = true; pintarQuiz(); enfocar('#panel-alt .resultado'); }
  }
  function pintarQuiz() {
    var cont = document.getElementById('panel-alt'); cont.textContent = '';
    if (qz.fin) { pintarResultado(cont); return; }
    var idx = qz.orden[qz.pos], q = Q[idx], n = qz.orden.length, r = qz.respondida, ok = r === q.correcta;
    var hechas = qz.pos + (r !== null ? 1 : 0);
    var opciones = qz.opciones.map(function (oi, k) {
      var cls = 'opcion'; if (r !== null) { if (oi === q.correcta) cls += ' ok'; else if (oi === r) cls += ' mal'; }
      return h('button', { class: cls, type: 'button', disabled: r !== null, onclick: function () { responder(oi); } },
        h('span', { class: 'letra', 'aria-hidden': 'true', text: LETRAS[k] }), h('span', { class: 'texto', text: q.opciones[oi] }));
    });
    var fb = null;
    if (r !== null) fb = h('div', { class: 'feedback ' + (ok ? 'ok' : 'mal'), tabindex: '-1', role: 'status' },
      h('p', {}, h('strong', { text: ok ? q.si_acierta : q.si_falla }), ok ? null : ' Respuesta correcta: ' + q.opciones[q.correcta]),
      h('p', { text: q.explicacion }));
    var acc = [];
    if (r === null && q.pista && !qz.pista) acc.push(boton('Ver pista', function () { qz.pista = true; pintarQuiz(); }, true));
    if (r !== null) acc.push(boton(qz.pos < n - 1 ? 'Siguiente' : 'Ver resultado', siguiente));
    cont.appendChild(h('div', {},
      h('div', { class: 'meta' }, h('span', { text: 'Pregunta ' + (qz.pos + 1) + ' de ' + n }), h('span', { text: 'Aciertos: ' + qz.aciertos })),
      h('div', { class: 'barra', role: 'progressbar', 'aria-label': 'Avance', 'aria-valuemin': '0', 'aria-valuemax': String(n), 'aria-valuenow': String(hechas) }, h('span', { style: 'width:' + (hechas / n * 100) + '%' })),
      h('span', { class: 'chip', text: q.tema }),
      h('h3', { class: 'prompt', tabindex: '-1', text: q.pregunta }),
      h('div', { class: 'opciones', role: 'group', 'aria-label': 'Alternativas' }, opciones),
      qz.pista && r === null ? h('p', { class: 'pista', text: 'Pista: ' + q.pista }) : null,
      fb,
      acc.length ? h('div', { class: 'acciones' }, acc) : null));
  }
  function pintarResultado(cont) {
    var n = qz.orden.length, a = qz.aciertos;
    if (qz.completo) { var prev = store.get('mejor', null); if (prev === null || a > prev) store.set('mejor', a); }
    var mejor = store.get('mejor', null);
    var msg = a === n ? 'Perfecto. Prueba ahora con las preguntas abiertas.' : a >= Math.ceil(n * 0.7) ? 'Bien. Repasa las que fallaste y vuelve a intentarlo.' : 'Vale la pena repasar las secciones de arriba y repetir.';
    var lista = qz.falladas.length ? h('ul', { class: 'lista-falladas' }, qz.falladas.map(function (i) {
      var q = Q[i]; return h('li', {}, h('span', { class: 'chip', text: q.tema }), h('p', { text: q.pregunta }), h('p', {}, h('strong', { text: 'Respuesta: ' }), q.opciones[q.correcta]));
    })) : null;
    var acc = [];
    if (qz.falladas.length) { var f = qz.falladas.slice(); acc.push(boton('Repasar las que fallé', function () { nuevoQuiz(f); enfocar('#panel-alt .prompt'); })); }
    acc.push(boton('Empezar de nuevo', function () { nuevoQuiz(rango(Q.length)); enfocar('#panel-alt .prompt'); }, qz.falladas.length > 0));
    acc.push(boton('Ir a las abiertas', function () { mostrarPanel('abi'); }, true));
    cont.appendChild(h('div', {},
      h('p', { class: 'muted', style: 'margin:0', text: qz.completo ? 'Resultado' : 'Resultado del repaso' }),
      h('p', { class: 'resultado', tabindex: '-1', text: a + ' de ' + n }),
      h('p', { style: 'margin:0', text: msg }),
      mejor !== null ? h('p', { class: 'muted', style: 'margin:6px 0 0', text: 'Tu mejor resultado: ' + mejor + ' de ' + Q.length }) : null,
      lista, h('div', { class: 'acciones' }, acc)));
  }

  // ------------------------------------------------------------- abiertas
  var TEMAS = ['Todas']; A.forEach(function (c) { if (TEMAS.indexOf(c.tema) < 0) TEMAS.push(c.tema); });
  var ab = { tema: 'Todas', pos: 0, ver: false };
  var reloj = { id: null, fin: 0, total: 60 };
  function listaAbiertas() { return rango(A.length).filter(function (i) { return ab.tema === 'Todas' || A[i].tema === ab.tema; }); }
  function pararReloj() { if (reloj.id) { clearInterval(reloj.id); reloj.id = null; } }
  function formatear(s) { return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2); }
  function tick() {
    var caja = document.querySelector('#panel-abi .reloj'); if (!caja) { pararReloj(); return; }
    var resta = Math.max(0, Math.ceil((reloj.fin - Date.now()) / 1000));
    caja.querySelector('.cuenta').textContent = formatear(resta);
    caja.querySelector('.barra > span').style.width = (resta / reloj.total * 100) + '%';
    if (resta <= 0) { pararReloj(); caja.classList.add('fin'); caja.querySelector('.sr').textContent = 'Se acabó el minuto.'; caja.querySelector('button').textContent = 'Otro minuto'; }
  }
  function alternarReloj() {
    var caja = document.querySelector('#panel-abi .reloj');
    if (reloj.id) { pararReloj(); caja.querySelector('button').textContent = 'Responder en 1 minuto'; caja.querySelector('.sr').textContent = 'Detenido.'; return; }
    caja.classList.remove('fin'); reloj.fin = Date.now() + reloj.total * 1000;
    caja.querySelector('button').textContent = 'Detener'; caja.querySelector('.sr').textContent = 'Corriendo.';
    tick(); reloj.id = setInterval(tick, 250);
  }
  function moverAbierta(d, azar) {
    var l = listaAbiertas(); if (!l.length) return; pararReloj();
    if (azar && l.length > 1) { var p; do { p = Math.floor(Math.random() * l.length); } while (p === ab.pos); ab.pos = p; }
    else ab.pos = (ab.pos + d + l.length) % l.length;
    ab.ver = false; pintarAbiertas(); enfocar('#panel-abi .pregunta-abierta');
  }
  function pintarAbiertas() {
    var cont = document.getElementById('panel-abi'); cont.textContent = '';
    var l = listaAbiertas(); if (ab.pos >= l.length) ab.pos = 0;
    var c = A[l[ab.pos]];
    cont.appendChild(h('p', { class: 'muted', style: 'margin:0 0 12px', text: 'Responde en voz alta antes de mirar la respuesta sugerida. De a dos: uno pregunta y el otro responde.' }));
    cont.appendChild(h('div', { class: 'filtros', role: 'group', 'aria-label': 'Filtrar por tema' }, TEMAS.map(function (t) {
      return h('button', { class: 'filtro', type: 'button', 'aria-pressed': t === ab.tema ? 'true' : 'false', text: t, onclick: function () { pararReloj(); ab.tema = t; ab.pos = 0; ab.ver = false; pintarAbiertas(); } });
    })));
    var relojCaja = h('div', { class: 'reloj' }, boton('Responder en 1 minuto', alternarReloj, true),
      h('span', { class: 'cuenta', 'aria-hidden': 'true', text: formatear(reloj.total) }),
      h('div', { class: 'barra', 'aria-hidden': 'true' }, h('span', { style: 'width:100%' })),
      h('span', { class: 'sr', role: 'status' }));
    cont.appendChild(h('div', { style: 'margin-top:16px' },
      h('div', { class: 'meta' }, h('span', { text: 'Pregunta ' + (ab.pos + 1) + ' de ' + l.length }), h('span', { class: 'chip', text: c.tema })),
      h('h3', { class: 'pregunta-abierta', tabindex: '-1', text: c.pregunta }),
      relojCaja,
      ab.ver ? h('div', { class: 'respuesta-sugerida', role: 'region', 'aria-label': 'Respuesta sugerida' }, h('p', { class: 'etq', text: 'Respuesta sugerida' }), h('p', { text: c.respuesta })) : null,
      h('div', { class: 'acciones' },
        boton(ab.ver ? 'Ocultar respuesta' : 'Ver respuesta sugerida', function () { ab.ver = !ab.ver; repintarSinReloj(); }),
        boton('Anterior', function () { moverAbierta(-1); }, true),
        boton('Siguiente', function () { moverAbierta(1); }, true),
        l.length > 1 ? boton('Al azar', function () { moverAbierta(0, true); }, true) : null)));
  }
  function repintarSinReloj() {
    var corriendo = !!reloj.id, caja = document.querySelector('#panel-abi .reloj');
    var estado = caja ? { cuenta: caja.querySelector('.cuenta').textContent, ancho: caja.querySelector('.barra > span').style.width, fin: caja.classList.contains('fin'), boton: caja.querySelector('button').textContent, sr: caja.querySelector('.sr').textContent } : null;
    pintarAbiertas();
    var nueva = document.querySelector('#panel-abi .reloj');
    if (nueva && estado) { nueva.querySelector('.cuenta').textContent = estado.cuenta; nueva.querySelector('.barra > span').style.width = estado.ancho; nueva.classList.toggle('fin', estado.fin); nueva.querySelector('button').textContent = estado.boton; nueva.querySelector('.sr').textContent = estado.sr; }
    if (corriendo && !reloj.id) reloj.id = setInterval(tick, 250);
    var r = document.querySelector('#panel-abi .respuesta-sugerida'); if (r) r.scrollIntoView({ block: 'nearest' });
  }

  // Atajos de teclado solo dentro de las alternativas (1 a 4 para responder, Enter para seguir)
  document.getElementById('panel-alt').addEventListener('keydown', function (e) {
    if (e.altKey || e.ctrlKey || e.metaKey || !qz || qz.fin) return;
    var t = e.target, enBoton = t && t.tagName === 'BUTTON';
    if (qz.respondida === null) {
      var k = '1234'.indexOf(e.key); if (k < 0) k = 'abcd'.indexOf((e.key || '').toLowerCase());
      if (k >= 0 && k < qz.opciones.length) { e.preventDefault(); responder(qz.opciones[k]); }
    } else if (e.key === 'Enter' && !enBoton) { e.preventDefault(); siguiente(); }
  });

  nuevoQuiz(rango(Q.length));
  pintarAbiertas();
  mostrarPanel(store.get('panel', 'alt'));
})();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Generación del HTML
# ---------------------------------------------------------------------------
NUMERICO = re.compile(r"^[−+\-<>]?\s*[\d.,]+\s*%?$|^—$|^[<>]\s*[\d.,]+$")


def inline(texto):
    s = html.escape(texto, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    s = re.sub(r"_\{([^{}]*)\}", r"<sub>\1</sub>", s)
    s = re.sub(r"\^\{([^{}]*)\}", r"<sup>\1</sup>", s)
    return s


def simbolos(s):
    """Dibuja con fuente sans los símbolos que algunas fuentes serif muestran mal."""
    for g in ("C̃", "d̄", "V̂"):
        s = s.replace(g, '<span class="sans">' + g + "</span>")
    return s


def texto_plano(texto):
    """Versión sin marcas, para el índice y los atributos."""
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", texto)
    s = re.sub(r"`(.+?)`", r"\1", s)
    s = s.replace("_{e}", "ₑ").replace("_{a}", "ₐ")
    s = re.sub(r"_\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\^\{([^{}]*)\}", r"\1", s)
    return s


def bloque(b):
    t = b["tipo"]
    if t == "p":
        return f"<p>{inline(b['texto'])}</p>"
    if t == "h3":
        return f"<h3>{inline(b['texto'])}</h3>"
    if t == "f":
        etq = f"<div class=\"etq\">{inline(b['etiqueta'])}</div>" if b["etiqueta"] else ""
        partes = [x for x in re.split(r" {3,}", b["texto"]) if x.strip()]
        expr = "".join('<span class="parte">' + simbolos(inline(x)) + "</span>" for x in partes)
        return f"<div class=\"formula\" role=\"group\" aria-label=\"{html.escape(texto_plano(b['etiqueta'] or 'Fórmula'))}\"><div class=\"expr\">{expr}</div>{etq}</div>"
    if t == "lista":
        return "<ul>" + "".join(f"<li>{inline(i)}</li>" for i in b["items"]) + "</ul>"
    if t == "nota":
        return f"<aside class=\"nota {b['clase']}\"><p class=\"etq\">{inline(b['etiqueta'])}</p><p>{inline(b['texto'])}</p></aside>"
    if t == "tabla":
        cols = b["columnas"]
        num_col = []
        for j in range(len(cols)):
            celdas = [f[j] for f in b["filas"] if j < len(f) and f[j]]
            num_col.append(bool(celdas) and all(NUMERICO.match(c.strip()) for c in celdas))
        clase_num = ' class="num"'
        cab = "".join(
            "<th scope=\"col\"" + (clase_num if num_col[j] else "") + ">" + inline(c) + "</th>"
            for j, c in enumerate(cols))
        filas = []
        for i, f in enumerate(b["filas"]):
            cls = ' class="destacar"' if i in b["destacar"] else ""
            celdas = "".join(
                "<td" + (clase_num if num_col[j] else "") + ">" + inline(c) + "</td>"
                for j, c in enumerate(f))
            filas.append("<tr" + cls + ">" + celdas + "</tr>")
        nota = f"<p class=\"tabla-nota\">{inline(b['nota'])}</p>" if b["nota"] else ""
        return f"<div class=\"tabla\" role=\"region\" aria-label=\"Tabla\" tabindex=\"0\"><table><thead><tr>{cab}</tr></thead><tbody>{''.join(filas)}</tbody></table></div>{nota}"
    raise ValueError(f"Tipo de bloque desconocido: {t}")


def validar():
    ids = set()
    for s in SECCIONES:
        for k in ("id", "titulo", "resumen", "bloques"):
            if k not in s:
                raise ValueError(f"Sección sin '{k}': {s.get('titulo', '?')}")
        if s["id"] in ids:
            raise ValueError(f"Identificador repetido: {s['id']}")
        ids.add(s["id"])
        for b in s["bloques"]:
            if b["tipo"] == "tabla":
                n = len(b["columnas"])
                for f in b["filas"]:
                    if len(f) != n:
                        raise ValueError(f"Tabla en '{s['titulo']}': una fila tiene {len(f)} celdas y la cabecera {n}.")
    for n, q in enumerate(PREGUNTAS_ALTERNATIVAS, 1):
        for k in ("tema", "pregunta", "opciones", "correcta", "explicacion", "pista", "si_acierta", "si_falla"):
            if k not in q:
                raise ValueError(f"Alternativas, pregunta {n}: falta '{k}'.")
        if not 0 <= q["correcta"] < len(q["opciones"]):
            raise ValueError(f"Alternativas, pregunta {n}: 'correcta' fuera de rango.")
    for n, c in enumerate(PREGUNTAS_ABIERTAS, 1):
        for k in ("tema", "pregunta", "respuesta"):
            if not c.get(k):
                raise ValueError(f"Abiertas, pregunta {n}: falta '{k}'.")


def generar(salida="tecnica.html"):
    validar()
    indice = "<ol>" + "".join(
        f"<li><a href=\"#{s['id']}\">{html.escape(texto_plano(s['titulo']))}</a></li>" for s in SECCIONES
    ) + "<li><a href=\"#preguntas\">13. Preguntas técnicas</a></li></ol>"
    partes = []
    for s in SECCIONES:
        cuerpo = "\n".join(bloque(b) for b in s["bloques"])
        ref = f"<p class=\"ref\">{inline(s['ref'])}</p>" if s.get("ref") else ""
        partes.append(
            f"    <section class=\"seccion\" id=\"{s['id']}\" aria-labelledby=\"t-{s['id']}\">\n"
            f"      <h2 id=\"t-{s['id']}\">{inline(s['titulo'])}</h2>\n"
            f"      <p class=\"resumen\">{inline(s['resumen'])}</p>\n      {ref}\n{cuerpo}\n    </section>"
        )
    datos = {"alternativas": PREGUNTAS_ALTERNATIVAS, "abiertas": PREGUNTAS_ABIERTAS}
    json_datos = json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")
    pagina = (PLANTILLA.replace("__TITULO__", html.escape(TITULO_TESIS))
              .replace("__INDICE__", indice)
              .replace("__CONTENIDO__", "\n".join(partes))
              .replace("__DATOS__", json_datos))
    Path(salida).write_text(pagina, encoding="utf-8")
    print(f"Listo: {salida} con {len(SECCIONES)} secciones, {len(PREGUNTAS_ALTERNATIVAS)} preguntas de alternativas "
          f"y {len(PREGUNTAS_ABIERTAS)} abiertas.")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    generar(args[0] if args and args[0].endswith(".html") else "tecnica.html")

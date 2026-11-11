# -*- coding: utf-8 -*-
"""
Genera la página de práctica para la defensa de tesis (quiz, tarjetas y preguntas de la comisión).

Uso:
    python generar_practica.py              -> escribe index.html en la carpeta actual
    python generar_practica.py otra.html    -> escribe con otro nombre

En Google Colab: sube este archivo y ejecuta  !python generar_practica.py  (o pega todo en una celda).

GitHub Pages solo publica archivos estáticos, así que Python arma la página una vez y
GitHub publica el index.html que resulta. Para cambiar o agregar preguntas, edita las
listas QUIZ y COMISION, vuelve a ejecutar el script y sube el index.html nuevo.
"""

import json
import sys
from pathlib import Path

TITULO_TESIS = (
    "Predicción de Peaks Extremos de Demanda Eléctrica en el Sistema Eléctrico Nacional "
    "de Chile mediante Modelos de Machine Learning"
)

# ---------------------------------------------------------------------------
# QUIZ: preguntas de alternativas. "correcta" es el índice de la opción correcta
# (0 = la primera). En la página las opciones se muestran en orden aleatorio.
# Las mismas preguntas se usan como tarjetas (pregunta adelante, respuesta atrás).
# ---------------------------------------------------------------------------
QUIZ = [
    {
        "seccion": "1. Introducción",
        "pregunta": "¿Por qué la tesis pone el foco en la punta de la demanda y no en su promedio?",
        "opciones": [
            "Porque la normativa solo exige pronosticar la demanda máxima.",
            "Porque el sistema se dimensiona por la punta: la capacidad y la reserva deben alcanzar para el instante de mayor exigencia.",
            "Porque el promedio de la demanda casi no ha cambiado desde 2018.",
            "Porque los modelos de pronóstico no logran estimar bien el promedio.",
        ],
        "correcta": 1,
        "explicacion": "Así lo plantea el apartado 1.3: un error en el promedio se traduce en ineficiencia económica, pero un error en la punta compromete la seguridad del suministro. Por eso el estudio mide si los modelos anticipan los días extremos, y no solo si siguen el nivel general.",
        "pista": "Piensa en para qué instante tienen que alcanzar la capacidad instalada y la reserva.",
        "si_acierta": "Exacto.",
        "si_falla": "No exactamente.",
    },
    {
        "seccion": "2. Problemática",
        "pregunta": "La relación valle-punta estuvo entre 0,777 y 0,790 durante ocho años, y en 2026 cayó a 0,673. ¿Qué indica esa caída?",
        "opciones": [
            "Que la demanda máxima diaria bajó en 2026.",
            "Que la curva diaria se deforma: el valle queda cada vez más lejos de la punta.",
            "Que la demanda se volvió más pareja a lo largo del día.",
            "Que la demanda mínima creció más rápido que la máxima.",
        ],
        "correcta": 1,
        "explicacion": "Es el cociente entre el valle y la punta del día. Entre enero y julio de 2026, la demanda máxima promedio subió 13,5% y la mínima bajó 1,5%, así que la amplitud entre ambas creció 62,5% (de 2.493 a 4.053 MW). La tesis lo asocia con lo documentado en sistemas con alta penetración solar, donde la punta se desplaza y se estrecha.",
        "pista": "Si el cociente entre el mínimo y el máximo del día baja, ¿la distancia entre ambos crece o se achica?",
        "si_acierta": "Bien leído.",
        "si_falla": "Casi, revisa qué mide el cociente.",
    },
    {
        "seccion": "3. Objetivos",
        "pregunta": "Una pregunta secundaria es si las diferencias de desempeño entre los modelos son estadísticamente significativas. ¿Qué objetivo específico la responde?",
        "opciones": [
            "El OE1",
            "El OE2",
            "El OE3",
            "Ninguno: queda como trabajo futuro",
        ],
        "correcta": 1,
        "explicacion": "El OE2 compara los modelos con un protocolo común, métricas homogéneas y pruebas estadísticas de comparación: la prueba de Diebold-Mariano, con las correcciones de Harvey y de Holm. El OE1 responde cómo definir un peak extremo, y el OE3, cómo integrar el mejor modelo en un esquema que emita alertas.",
        "pista": "Busca el objetivo que menciona «pruebas estadísticas de comparación».",
        "si_acierta": "Correcto.",
        "si_falla": "Ese no es.",
    },
    {
        "seccion": "4. Identificación cualitativa del problema",
        "pregunta": "El árbol de problemas tiene cuatro causas. ¿Cuál de ellas no la ataca ningún objetivo, porque no depende del pronóstico?",
        "opciones": [
            "Demanda acelerada",
            "Sin definición replicable",
            "Comparaciones dispares",
            "Modelos hechos para el promedio",
        ],
        "correcta": 0,
        "explicacion": "La demanda acelerada es el contexto del problema. Las otras tres dependen de cómo se pronostica y se compara: la falta de definición la resuelve el OE1, las comparaciones dispares el OE2, y el sesgo de los modelos hacia el promedio lo mide el OE2 y lo compensa el OE3.",
        "pista": "Tres causas hablan de modelos, criterios o comparaciones; una es un hecho del sistema eléctrico.",
        "si_acierta": "Justo esa.",
        "si_falla": "Esa sí la aborda un objetivo.",
    },
    {
        "seccion": "5. Desarrollo del Objetivo Específico 1",
        "pregunta": "Según el criterio de la tesis (OE1), ¿cuándo un día es un peak extremo?",
        "opciones": [
            "Cuando su demanda supera el percentil 95 de toda la serie 2018-2026.",
            "Cuando su desviación respecto del nivel esperado, tipificada con la dispersión de los 90 días previos, supera kₑ = 1,75.",
            "Cuando su demanda supera el máximo del año anterior.",
            "Cuando su demanda supera los 14.000 MW.",
        ],
        "correcta": 1,
        "explicacion": "El nivel base b es la mediana de los 28 días previos; al multiplicarlo por el factor del día de la semana f queda el nivel esperado E = b·f. Luego z = (y/E − 1)/σ, con σ de los 90 días previos, y el día es peak extremo si z supera 1,75. Todo usa solo información pasada, por eso es replicable y se puede calcular en tiempo real. Un percentil de toda la serie usaría datos del futuro.",
        "pista": "La clave del criterio es que solo usa información anterior al día evaluado.",
        "si_acierta": "Eso es.",
        "si_falla": "Todavía no.",
    },
    {
        "seccion": "6. Desarrollo del Objetivo Específico 2",
        "pregunta": "La LSTM quedó tercera en validación (343,7 MW de error) y última en la prueba (797,1 MW). ¿A qué atribuye la tesis, en buena medida, ese deterioro?",
        "opciones": [
            "A que recibía demasiadas variables de calendario.",
            "Al desplazamiento del nivel de demanda: la mediana de la prueba supera en 391,9 MW el máximo que la red vio al entrenar.",
            "A que la prueba usaba datos horarios y la validación, diarios.",
            "A que se entrenó con una semilla distinta para cada horizonte.",
        ],
        "correcta": 1,
        "explicacion": "La red aprendió la serie en su escala original, y la prueba está en un nivel que nunca vio; SARIMAX trabaja sobre la serie diferenciada y Prophet proyecta su tendencia, así que no quedan acotados de la misma forma. Se suman la implementación (una sola variable de entrada, sin calendario, configuración fija y una semilla) y una muestra chica para la red: 2.557 observaciones para 4.583 parámetros. Su error creció 131,9% entre validación y prueba, frente a 12,4% en SARIMAX.",
        "pista": "Compara el nivel de demanda que la red vio al entrenar con el de enero a julio de 2026.",
        "si_acierta": "Bien.",
        "si_falla": "No es eso.",
    },
    {
        "seccion": "6. Desarrollo del Objetivo Específico 2",
        "pregunta": "Si sobre los pronósticos se aplica el mismo umbral que define un peak (kₑ = 1,75), ¿cuántas de las 56 oportunidades de la prueba detecta SARIMAX, el modelo más exacto?",
        "opciones": ["1", "24", "42", "56"],
        "correcta": 0,
        "explicacion": "Detecta 1 de 56, y CatBoost, Prophet y la LSTM, ninguna. Es la reversión a la media: un pronóstico puntual busca equivocarse poco en promedio, así que sobreestima los días bajos y subestima los altos (en el 20% de días más altos, SARIMAX subestima 3,05%). Hay 56 oportunidades porque son 8 eventos y cada día se pronostica desde 7 orígenes.",
        "pista": "El hallazgo central es que un error bajo no se traduce en detección.",
        "si_acierta": "Así es, solo una.",
        "si_falla": "Son menos de las que parece.",
    },
    {
        "seccion": "7. Desarrollo del Objetivo Específico 3",
        "pregunta": "El esquema avisa con kₐ = 0,35, mucho más abajo que kₑ = 1,75. ¿Por qué eso no es hacer trampa?",
        "opciones": [
            "Porque kₐ no cambia qué es un peak ni las etiquetas, y se calibró en 2025 para aplicarse sin cambios a 2026.",
            "Porque kₐ se eligió con los eventos de 2026 para maximizar el F₁.",
            "Porque al bajar kₐ también cambia la definición de peak extremo.",
            "Porque la norma técnica fija el umbral de alerta en 0,35.",
        ],
        "correcta": 0,
        "explicacion": "Son dos preguntas distintas: kₑ define el fenómeno y queda fijo; kₐ decide cuándo avisar. Como los pronósticos recortan los días altos, conviene avisar antes, igual que llamar al médico a 37,5 °C si se sabe que el termómetro marca medio grado menos. Y la calibración se traslada: F₁ de 0,403 en la prueba, frente a 0,407 si el umbral se hubiera elegido mirando la prueba.",
        "pista": "Fíjate en con qué datos se calibró kₐ y si toca la definición del fenómeno.",
        "si_acierta": "Muy bien.",
        "si_falla": "No del todo.",
    },
    {
        "seccion": "7. Desarrollo del Objetivo Específico 3",
        "pregunta": "¿Por qué el esquema integra CatBoost y no SARIMAX, si SARIMAX se equivoca menos?",
        "opciones": [
            "Porque CatBoost tiene el menor error absoluto medio en la prueba.",
            "Porque el modelo se eligió por su detección: CatBoost logra un F₁ de 0,403, frente a 0,277 de SARIMAX.",
            "Porque CatBoost anticipa los 8 eventos de la prueba.",
            "Porque SARIMAX no puede pronosticar más de un día.",
        ],
        "correcta": 1,
        "explicacion": "El objetivo general es anticipar eventos, no minimizar el error medio. CatBoost se equivoca 85,2 MW más en promedio, pero anticipa 6 de 8 eventos con 39 falsas alarmas; SARIMAX anticipa 7, con 93. Ojo con la letra chica: la elección se hizo mirando la prueba, así que el resultado se lee como optimista; en validación, el mejor F₁ habría sido el de Prophet (0,221 frente a 0,179).",
        "pista": "¿Qué pide el objetivo general: equivocarse poco o anticipar los eventos?",
        "si_acierta": "Correcto.",
        "si_falla": "Revisa el criterio de elección.",
    },
    {
        "seccion": "8. Conclusiones",
        "pregunta": "En el cierre, ¿cuál es la principal limitación que reconocen?",
        "opciones": [
            "Que el criterio de peak usa información del futuro.",
            "Que la prueba tiene solo 8 eventos, así que un solo evento mueve la exhaustividad en 0,125.",
            "Que se trabajó con datos horarios en vez de máximos diarios.",
            "Que la prueba incluye días de 2025 que se usaron para entrenar.",
        ],
        "correcta": 1,
        "explicacion": "Con tan pocos eventos, las métricas de detección son sensibles a un solo caso. El guion menciona también que se usaron máximos diarios, sin la hora de la punta ni temperatura; que el esquema es un prototipo evaluado sobre datos históricos, y que el modelo integrado se eligió mirando la prueba. Como trabajo futuro propone corregir el sesgo según el nivel de demanda, agregar a CatBoost los rezagos de 4 y 5 días, incorporar temperatura y pronóstico probabilístico, pasar a resolución horaria y validar con especialistas del Coordinador.",
        "pista": "Piensa en cuántos eventos tiene el período de prueba.",
        "si_acierta": "Exacto.",
        "si_falla": "No es esa.",
    },
]

# ---------------------------------------------------------------------------
# COMISION: preguntas abiertas para responder en voz alta, con una respuesta sugerida.
# ---------------------------------------------------------------------------
COMISION = [
    {
        "tema": "Para abrir",
        "pregunta": "En pocas palabras, ¿qué problema aborda su tesis y cuál es su hallazgo principal?",
        "respuesta": "La tesis evalúa si los modelos de pronóstico permiten anticipar, con hasta siete días, los peaks extremos de demanda del SEN. Para eso define un criterio replicable de peak, compara seis modelos con el mismo protocolo y diseña un esquema de alerta. El hallazgo principal es que el modelo que mejor pronostica no es el que mejor avisa: SARIMAX tiene el menor error, pero con el umbral que define un peak detecta 1 de 56 oportunidades, porque todos los modelos recortan los días altos. Por eso el esquema separa dos umbrales y elige el modelo por detección: CatBoost anticipa 6 de 8 eventos con 39 falsas alarmas.",
    },
    {
        "tema": "El problema",
        "pregunta": "¿Por qué un árbol de problemas?",
        "respuesta": "Porque ordena el problema en causas y efectos antes de medir, y muestra qué causas atacan los objetivos: la falta de definición, la comparación y la conversión del pronóstico en alertas. El crecimiento de la demanda queda como contexto, porque la tesis lo describe pero no lo explica.",
    },
    {
        "tema": "El problema",
        "pregunta": "¿Qué está causando el cambio en la curva de demanda?",
        "respuesta": "La tesis no lo afirma. Describe un cambio coherente con lo documentado en sistemas con mucha energía solar, pero establecer la causa exigiría datos horarios y series de generación, fuera del alcance.",
    },
    {
        "tema": "El problema",
        "pregunta": "Si hay una identificación cualitativa, ¿la tesis es cualitativa?",
        "respuesta": "No. La investigación es cuantitativa: la variable es una magnitud física en MW y las conclusiones salen de comparar modelos con números. Lo cualitativo es la descripción del problema, no el método.",
    },
    {
        "tema": "El criterio y los datos",
        "pregunta": "¿Por qué siete días?",
        "respuesta": "Es el límite del pronóstico de corto plazo y coincide con el ciclo semanal. Así cada día pronosticado se corrige por su propio día de la semana sin usar datos futuros, cosa imposible con más de siete días.",
    },
    {
        "tema": "El criterio y los datos",
        "pregunta": "¿No es arbitrario el umbral de 1,75?",
        "respuesta": "Es una decisión declarada: deja del orden de un evento cada 24 días, suficientes para evaluar y pocos para que tengan sentido operacional. Recalibrado solo con el entrenamiento da el mismo valor, y los eventos de prueba no cambian.",
    },
    {
        "tema": "El criterio y los datos",
        "pregunta": "¿Por qué excluyeron los datos anteriores a 2018?",
        "respuesta": "Antes de la interconexión el SIC y el SING tenían su punta a distinta hora, y sumar sus máximos sobreestimaría la demanda del sistema conjunto.",
    },
    {
        "tema": "El criterio y los datos",
        "pregunta": "¿Cómo saben que no hay fuga de información?",
        "respuesta": "Se multiplicó por 10 la demanda del 19 de marzo de 2025 y ninguna predictora de días anteriores cambió. Además la partición es estrictamente temporal y el criterio usa solo días previos.",
    },
    {
        "tema": "Los modelos",
        "pregunta": "¿Por qué CatBoost si SARIMAX se equivoca menos?",
        "respuesta": "Porque el objetivo es anticipar eventos y en detección CatBoost logra F₁ 0,403 frente a 0,277, con ventaja desde el cuarto día. Reconocemos que la elección miró la prueba y por eso su resultado es optimista.",
    },
    {
        "tema": "Los modelos",
        "pregunta": "¿La LSTM quedó mal implementada?",
        "respuesta": "En validación quedó tercera; el problema apareció en 2026, cuando la demanda superó todo lo visto en el entrenamiento. Su detención temprana funcionó, pero eso evita memorizar, no adaptarse a un nivel nuevo, y además usaba solo la serie y una configuración.",
    },
    {
        "tema": "Los modelos",
        "pregunta": "¿Por qué no usaron la temperatura?",
        "respuesta": "A siete días habría que pronosticar también la temperatura, y ese error se sumaría al de la demanda. Se dejó fuera por alcance y se propone como trabajo futuro; el calendario, en cambio, se conoce de antemano.",
    },
    {
        "tema": "Los modelos",
        "pregunta": "¿Por qué Prophet no supera al estacional ingenuo?",
        "respuesta": "Prophet describe la forma general del año y de la semana, pero no usa lo que pasó en los últimos días. Para pronosticar días individuales esa dinámica importa, y repetir la semana anterior ya captura lo esencial.",
    },
    {
        "tema": "Los modelos",
        "pregunta": "¿Por qué el estacional ingenuo tiene el mismo error en todos los horizontes?",
        "respuesta": "Porque para cada día repite el valor de siete días antes, sin importar desde qué origen se pronostique. Por la misma razón, al séptimo día coincide con la persistencia.",
    },
    {
        "tema": "Los modelos",
        "pregunta": "¿Por qué no entrenaron los modelos para predecir directamente si habrá peak?",
        "respuesta": "Porque SARIMAX y Prophet entregan valores y no probabilidades, y la comparación entre familias se habría perdido. Con el diseño en dos etapas todos compiten con las mismas reglas.",
    },
    {
        "tema": "La evaluación y el esquema",
        "pregunta": "¿Bajar el umbral de alerta no es acomodar los resultados?",
        "respuesta": "No: la definición de peak queda fija en 1,75. El umbral de alerta se calibró en 2025 y se aplicó sin cambios en 2026, donde dio F₁ 0,403 frente a un óptimo de 0,407.",
    },
    {
        "tema": "La evaluación y el esquema",
        "pregunta": "¿Se puede concluir algo con solo 8 eventos?",
        "respuesta": "Sí, con cautela: las tendencias se sostienen, pero las diferencias pequeñas son indicativas, porque un caso cambia la exhaustividad en 0,125. Por eso se informa también cuántos eventos distintos se anticiparon.",
    },
    {
        "tema": "La evaluación y el esquema",
        "pregunta": "¿Un F₁ de 0,403 es bueno?",
        "respuesta": "Es el mejor de los seis modelos y supera con amplitud a las referencias, pero significa acertar algo más de una alerta de cada tres y perder 2 de 8 eventos. Sirve como apoyo a la operación, no como sistema autónomo.",
    },
    {
        "tema": "La evaluación y el esquema",
        "pregunta": "¿Qué hace la corrección de Holm?",
        "respuesta": "Ajusta los valores p cuando se hacen muchas comparaciones, para que no aparezcan diferencias «significativas» por azar. Con ella dejan de ser significativas tres diferencias, entre ellas la de SARIMAX frente a CatBoost a siete días.",
    },
    {
        "tema": "La evaluación y el esquema",
        "pregunta": "¿El Coordinador podría usar esto mañana?",
        "respuesta": "No directamente: es un prototipo evaluado sobre datos históricos. Faltaría validarlo en operación, con los retrasos reales del dato, y definir con especialistas cuánto cuesta una falsa alarma frente a un evento perdido.",
    },
]

# ---------------------------------------------------------------------------
# Plantilla de la página. __DATOS__ se reemplaza por las preguntas en formato JSON.
# ---------------------------------------------------------------------------
PLANTILLA = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Práctica para la defensa</title>
<meta name="description" content="Quiz, tarjetas y preguntas de la comisión para practicar la defensa de la tesis sobre peaks extremos de demanda eléctrica en el SEN.">
<style>
:root {
  --navy: #003784; --blue: #3386CD; --celeste: #5CB9E1;
  --bg: #F4F6FA; --surface: #FFFFFF; --ink: #15203A; --muted: #586178; --line: #DCE2EC;
  --accent: #003784; --accent-soft: #E6EEF9; --btn: #003784; --btn-ink: #FFFFFF;
  --ok: #1D7447; --ok-bg: #E5F3EB; --bad: #B3261E; --bad-bg: #FBE9E8;
  --radius: 14px;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #0D1320; --surface: #161F31; --ink: #E7ECF5; --muted: #A2ACC0; --line: #2A3650;
    --accent: #8DBBEF; --accent-soft: #1C2A44; --btn: #3B78C8; --btn-ink: #FFFFFF;
    --ok: #63CC9C; --ok-bg: #11301F; --bad: #F2938C; --bad-bg: #3A1817;
    color-scheme: dark;
  }
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 16px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
.wrap { max-width: 760px; margin: 0 auto; padding: 28px 16px 48px; }
.eyebrow { margin: 0; font-size: 13px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--blue); }
h1 { margin: 4px 0 6px; font-size: 30px; line-height: 1.15; color: var(--accent); }
.tesis { margin: 0 0 20px; color: var(--muted); font-size: 15px; }
.tabs { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px; padding: 4px; background: var(--surface); border: 1px solid var(--line); border-radius: 12px; }
.tabs button { appearance: none; border: 0; background: transparent; color: var(--ink); font: inherit; font-weight: 600; font-size: 15px; padding: 10px 6px; border-radius: 9px; cursor: pointer; min-height: 44px; }
.tabs button[aria-selected="true"] { background: var(--btn); color: var(--btn-ink); }
.card { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); padding: 20px; margin-top: 16px; }
.meta { display: flex; justify-content: space-between; align-items: center; gap: 12px; font-size: 14px; color: var(--muted); }
.barra { height: 6px; background: var(--line); border-radius: 99px; overflow: hidden; margin: 10px 0 16px; }
.barra > span { display: block; height: 100%; background: var(--blue); transition: width .3s; }
.chip { display: inline-block; font-size: 13px; font-weight: 600; color: var(--accent); background: var(--accent-soft); padding: 3px 10px; border-radius: 99px; }
.prompt { font-size: 20px; line-height: 1.35; margin: 12px 0 16px; outline: none; }
.opciones { display: grid; gap: 10px; }
.opcion { display: flex; gap: 12px; align-items: flex-start; text-align: left; width: 100%; padding: 12px 14px; border: 1.5px solid var(--line); border-radius: 12px; background: var(--surface); color: var(--ink); font: inherit; cursor: pointer; }
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
.btn.sec[aria-pressed="true"] { background: var(--accent-soft); border-color: var(--accent); }
.btn:hover { filter: brightness(1.08); }
.tabs button:focus-visible, .btn:focus-visible, .opcion:focus-visible, .flip-inner:focus-visible, .filtro:focus-visible, .check:focus-within { outline: 3px solid var(--celeste); outline-offset: 2px; }
.check { display: inline-flex; gap: 8px; align-items: center; font-size: 15px; color: var(--muted); cursor: pointer; border-radius: 8px; }
.check input { width: 18px; height: 18px; accent-color: var(--btn); }
.resultado { font-size: 48px; font-weight: 800; line-height: 1; color: var(--accent); margin: 8px 0 4px; outline: none; }
.lista-falladas { margin: 16px 0 0; padding: 0; list-style: none; display: grid; gap: 10px; }
.lista-falladas li { border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px; }
.lista-falladas p { margin: 6px 0 0; }
.muted { color: var(--muted); }
.flip { perspective: 1400px; margin-top: 16px; }
.flip-inner { display: grid; transition: transform .5s; transform-style: preserve-3d; cursor: pointer; border-radius: var(--radius); outline: none; }
.flip.volteada .flip-inner { transform: rotateY(180deg); }
.cara { grid-area: 1 / 1; -webkit-backface-visibility: hidden; backface-visibility: hidden; background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); padding: 24px 20px; min-height: 280px; display: flex; flex-direction: column; gap: 12px; }
.cara.atras { transform: rotateY(180deg); border-color: var(--blue); }
.cara .pregunta-tarjeta { font-size: 21px; line-height: 1.35; margin: 4px 0 0; font-weight: 600; }
.cara .ayuda { margin: auto 0 0; font-size: 14px; color: var(--muted); }
.cara .etq { margin: 0; font-size: 13px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--blue); }
.cara .respuesta { margin: 0; font-size: 18px; font-weight: 600; line-height: 1.4; }
.cara .explicacion { margin: 0; color: var(--ink); }
.filtros { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }
.filtro { appearance: none; border: 1.5px solid var(--line); background: var(--surface); color: var(--ink); font: inherit; font-size: 14px; font-weight: 600; padding: 6px 12px; border-radius: 99px; cursor: pointer; min-height: 36px; }
.filtro[aria-pressed="true"] { background: var(--btn); border-color: var(--btn); color: var(--btn-ink); }
.consejo { margin: 16px 0 0; font-size: 15px; color: var(--muted); }
.pregunta-comision { font-size: 22px; line-height: 1.35; margin: 12px 0 4px; outline: none; }
.reloj { display: flex; align-items: center; gap: 12px; margin-top: 14px; }
.reloj .cuenta { font-variant-numeric: tabular-nums; font-weight: 700; font-size: 18px; min-width: 52px; }
.reloj .barra { flex: 1; margin: 0; }
.reloj.fin .cuenta { color: var(--bad); }
.respuesta-sugerida { margin-top: 16px; padding: 14px 16px; border-radius: 12px; background: var(--accent-soft); border-left: 4px solid var(--accent); }
.respuesta-sugerida p { margin: 0; }
.respuesta-sugerida .etq { font-size: 13px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--accent); margin-bottom: 6px; }
footer { margin-top: 32px; font-size: 13.5px; color: var(--muted); }
footer p { margin: 4px 0; }
@media (max-width: 520px) {
  h1 { font-size: 26px; }
  .prompt { font-size: 18px; }
  .pregunta-comision, .cara .pregunta-tarjeta { font-size: 19px; }
  .card { padding: 16px; }
  .acciones .btn { flex: 1 1 auto; }
}
@media (prefers-reduced-motion: reduce) {
  .flip-inner, .barra > span { transition: none; }
}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <p class="eyebrow">Ensayo de defensa</p>
    <h1>Práctica para la defensa</h1>
    <p class="tesis" id="tesis"></p>
    <div class="tabs" role="tablist" aria-label="Modo de práctica">
      <button type="button" role="tab" id="tab-quiz" aria-controls="vista-quiz" data-vista="quiz">Quiz</button>
      <button type="button" role="tab" id="tab-tarjetas" aria-controls="vista-tarjetas" data-vista="tarjetas">Tarjetas</button>
      <button type="button" role="tab" id="tab-comision" aria-controls="vista-comision" data-vista="comision">Comisión</button>
    </div>
  </header>
  <main>
    <section id="vista-quiz" role="tabpanel" aria-labelledby="tab-quiz"></section>
    <section id="vista-tarjetas" role="tabpanel" aria-labelledby="tab-tarjetas" hidden></section>
    <section id="vista-comision" role="tabpanel" aria-labelledby="tab-comision" hidden></section>
  </main>
  <footer>
    <p>Las cifras vienen de la tesis. Tu avance se guarda solo en este navegador.</p>
    <p>Página generada con generar_practica.py.</p>
  </footer>
</div>
<script type="application/json" id="datos">__DATOS__</script>
<script>
(function () {
  'use strict';
  var D = JSON.parse(document.getElementById('datos').textContent);
  var Q = D.quiz, C = D.comision;
  var LETRAS = ['A', 'B', 'C', 'D', 'E', 'F'];
  var VISTAS = ['quiz', 'tarjetas', 'comision'];
  var PREFIJO = 'practica-defensa:';

  var store = {
    get: function (k, d) { try { var v = localStorage.getItem(PREFIJO + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set: function (k, v) { try { localStorage.setItem(PREFIJO + k, JSON.stringify(v)); } catch (e) {} }
  };

  function barajar(a) {
    var b = a.slice();
    for (var i = b.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = b[i]; b[i] = b[j]; b[j] = t; }
    return b;
  }
  function rango(n) { var r = []; for (var i = 0; i < n; i++) r.push(i); return r; }

  // h('tag', {props}, hijos...) crea elementos sin usar innerHTML
  function h(tag, props) {
    var n = document.createElement(tag);
    props = props || {};
    Object.keys(props).forEach(function (k) {
      var v = props[k];
      if (v === null || v === undefined || v === false) return;
      if (k === 'class') n.className = v;
      else if (k === 'text') n.textContent = v;
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
  function boton(texto, fn, sec, extra) {
    var p = { class: 'btn' + (sec ? ' sec' : ''), type: 'button', text: texto, onclick: fn };
    if (extra) Object.keys(extra).forEach(function (k) { p[k] = extra[k]; });
    return h('button', p);
  }
  function enfocar(sel) { var e = document.querySelector(sel); if (e) e.focus({ preventScroll: false }); }

  document.getElementById('tesis').textContent = D.titulo;

  // ------------------------------------------------------------------ pestañas
  var vistaActual = 'quiz';
  function mostrar(v, porUsuario) {
    if (VISTAS.indexOf(v) < 0) v = 'quiz';
    vistaActual = v;
    document.querySelectorAll('.tabs [role=tab]').forEach(function (b) {
      var on = b.getAttribute('data-vista') === v;
      b.setAttribute('aria-selected', on ? 'true' : 'false');
      b.tabIndex = on ? 0 : -1;
    });
    VISTAS.forEach(function (x) { document.getElementById('vista-' + x).hidden = x !== v; });
    if (v !== 'comision') pararReloj();
    store.set('vista', v);
    if (porUsuario && location.hash !== '#' + v) { try { history.replaceState(null, '', '#' + v); } catch (e) {} }
  }
  document.querySelectorAll('.tabs [role=tab]').forEach(function (b, i, todos) {
    b.addEventListener('click', function () { mostrar(b.getAttribute('data-vista'), true); });
    b.addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      e.preventDefault();
      var k = (i + (e.key === 'ArrowRight' ? 1 : todos.length - 1)) % todos.length;
      todos[k].focus(); mostrar(todos[k].getAttribute('data-vista'), true);
    });
  });

  // ------------------------------------------------------------------ quiz
  var qz;
  function nuevoQuiz(indices) {
    qz = { orden: indices, pos: 0, aciertos: 0, falladas: [], fin: false, completo: indices.length === Q.length };
    prepararPregunta();
    pintarQuiz();
  }
  function prepararPregunta() {
    var q = Q[qz.orden[qz.pos]];
    qz.opciones = barajar(rango(q.opciones.length));
    qz.respondida = null;
    qz.pista = false;
  }
  function responder(i) {
    if (qz.respondida !== null) return;
    var idx = qz.orden[qz.pos];
    qz.respondida = i;
    if (i === Q[idx].correcta) qz.aciertos++; else qz.falladas.push(idx);
    pintarQuiz();
    enfocar('#vista-quiz .feedback');
  }
  function siguiente() {
    if (qz.pos < qz.orden.length - 1) { qz.pos++; prepararPregunta(); pintarQuiz(); enfocar('#vista-quiz .prompt'); }
    else { qz.fin = true; pintarQuiz(); enfocar('#vista-quiz .resultado'); }
  }
  function pintarQuiz() {
    var cont = document.getElementById('vista-quiz');
    cont.textContent = '';
    if (qz.fin) { pintarResultado(cont); return; }
    var idx = qz.orden[qz.pos], q = Q[idx], n = qz.orden.length, r = qz.respondida, ok = r === q.correcta;
    var hechas = qz.pos + (r !== null ? 1 : 0);
    var opciones = qz.opciones.map(function (oi, k) {
      var cls = 'opcion';
      if (r !== null) { if (oi === q.correcta) cls += ' ok'; else if (oi === r) cls += ' mal'; }
      return h('button', { class: cls, type: 'button', disabled: r !== null, onclick: function () { responder(oi); } },
        h('span', { class: 'letra', 'aria-hidden': 'true', text: LETRAS[k] }),
        h('span', { class: 'texto', text: q.opciones[oi] }));
    });
    var feedback = null;
    if (r !== null) {
      feedback = h('div', { class: 'feedback ' + (ok ? 'ok' : 'mal'), tabindex: '-1', role: 'status' },
        h('p', {}, h('strong', { text: ok ? q.si_acierta : q.si_falla }), ok ? null : ' Respuesta correcta: ' + q.opciones[q.correcta]),
        h('p', { text: q.explicacion }));
    }
    var acciones = [];
    if (r === null && q.pista && !qz.pista) acciones.push(boton('Ver pista', function () { qz.pista = true; pintarQuiz(); }, true));
    if (r !== null) acciones.push(boton(qz.pos < n - 1 ? 'Siguiente' : 'Ver resultado', siguiente));
    cont.appendChild(h('div', { class: 'card' },
      h('div', { class: 'meta' }, h('span', { text: 'Pregunta ' + (qz.pos + 1) + ' de ' + n }), h('span', { text: 'Aciertos: ' + qz.aciertos })),
      h('div', { class: 'barra', role: 'progressbar', 'aria-label': 'Avance del quiz', 'aria-valuemin': '0', 'aria-valuemax': String(n), 'aria-valuenow': String(hechas) },
        h('span', { style: 'width:' + (hechas / n * 100) + '%' })),
      h('span', { class: 'chip', text: q.seccion }),
      h('h2', { class: 'prompt', tabindex: '-1', text: q.pregunta }),
      h('div', { class: 'opciones', role: 'group', 'aria-label': 'Alternativas' }, opciones),
      qz.pista && r === null ? h('p', { class: 'pista', text: 'Pista: ' + q.pista }) : null,
      feedback,
      acciones.length ? h('div', { class: 'acciones' }, acciones) : null));
  }
  function pintarResultado(cont) {
    var n = qz.orden.length, a = qz.aciertos;
    if (qz.completo) { var prev = store.get('mejor', null); if (prev === null || a > prev) store.set('mejor', a); }
    var mejor = store.get('mejor', null);
    var msg = a === n ? 'Perfecto. Ahora prueba con las preguntas de la comisión.'
      : a >= Math.ceil(n * 0.7) ? 'Bien. Repasa las que fallaste y vuelve a intentarlo.'
      : 'Vale la pena una segunda vuelta: lee las explicaciones y repite.';
    var lista = qz.falladas.length ? h('ul', { class: 'lista-falladas' }, qz.falladas.map(function (i) {
      var q = Q[i];
      return h('li', {}, h('span', { class: 'chip', text: q.seccion }), h('p', { text: q.pregunta }),
        h('p', {}, h('strong', { text: 'Respuesta: ' }), q.opciones[q.correcta]));
    })) : null;
    var acciones = [];
    if (qz.falladas.length) { var f = qz.falladas.slice(); acciones.push(boton('Repasar las que fallé', function () { nuevoQuiz(f); enfocar('#vista-quiz .prompt'); })); }
    acciones.push(boton('Empezar de nuevo', function () { nuevoQuiz(rango(Q.length)); enfocar('#vista-quiz .prompt'); }, qz.falladas.length > 0));
    acciones.push(boton('Ir a las tarjetas', function () { mostrar('tarjetas', true); }, true));
    cont.appendChild(h('div', { class: 'card' },
      h('p', { class: 'muted', style: 'margin:0', text: qz.completo ? 'Resultado del quiz' : 'Resultado del repaso' }),
      h('p', { class: 'resultado', tabindex: '-1', text: a + ' de ' + n }),
      h('p', { style: 'margin:0', text: msg }),
      mejor !== null ? h('p', { class: 'muted', style: 'margin:6px 0 0', text: 'Tu mejor resultado: ' + mejor + ' de ' + Q.length }) : null,
      lista,
      h('div', { class: 'acciones' }, acciones)));
  }

  // ------------------------------------------------------------------ tarjetas
  var sabidas = {};
  (store.get('sabidas', []) || []).forEach(function (i) { if (i >= 0 && i < Q.length) sabidas[i] = true; });
  var tj = { orden: rango(Q.length), pos: 0, solo: false };
  function cuantasSabidas() { return Object.keys(sabidas).length; }
  function guardarSabidas() { store.set('sabidas', Object.keys(sabidas).map(Number)); }
  function listaTarjetas() { return tj.solo ? tj.orden.filter(function (i) { return !sabidas[i]; }) : tj.orden; }
  function moverTarjeta(d) {
    var l = listaTarjetas(); if (!l.length) return;
    tj.pos = (tj.pos + d + l.length) % l.length; pintarTarjetas(); enfocar('#vista-tarjetas .flip-inner');
  }
  function voltear() {
    var f = document.querySelector('#vista-tarjetas .flip'); if (!f) return;
    var v = !f.classList.contains('volteada');
    f.classList.toggle('volteada', v);
    f.querySelector('.frente').setAttribute('aria-hidden', v ? 'true' : 'false');
    f.querySelector('.atras').setAttribute('aria-hidden', v ? 'false' : 'true');
    f.querySelector('.flip-inner').setAttribute('aria-label', v ? 'Tarjeta con la respuesta. Toca para volver a la pregunta.' : 'Tarjeta con la pregunta. Toca para ver la respuesta.');
  }
  function pintarTarjetas() {
    var cont = document.getElementById('vista-tarjetas');
    cont.textContent = '';
    var l = listaTarjetas();
    var meta = h('div', { class: 'meta', style: 'margin-top:16px' },
      h('span', { text: l.length ? 'Tarjeta ' + (Math.min(tj.pos, l.length - 1) + 1) + ' de ' + l.length : 'Sin tarjetas pendientes' }),
      h('span', { text: 'La sé: ' + cuantasSabidas() + ' de ' + Q.length }));
    cont.appendChild(meta);
    if (!l.length) {
      cont.appendChild(h('div', { class: 'card' },
        h('p', { style: 'margin:0', text: 'Marcaste todas las tarjetas como sabidas.' }),
        h('div', { class: 'acciones' },
          boton('Mostrar todas', function () { tj.solo = false; tj.pos = 0; pintarTarjetas(); }),
          boton('Reiniciar marcas', function () { sabidas = {}; guardarSabidas(); tj.pos = 0; pintarTarjetas(); }, true))));
      return;
    }
    if (tj.pos >= l.length) tj.pos = 0;
    var idx = l[tj.pos], q = Q[idx], sabe = !!sabidas[idx];
    var inner = h('div', { class: 'flip-inner', role: 'button', tabindex: '0', 'aria-label': 'Tarjeta con la pregunta. Toca para ver la respuesta.',
        onclick: voltear,
        onkeydown: function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); voltear(); } } },
      h('div', { class: 'cara frente', 'aria-hidden': 'false' },
        h('span', { class: 'chip', style: 'align-self:flex-start', text: q.seccion }),
        h('p', { class: 'pregunta-tarjeta', text: q.pregunta }),
        h('p', { class: 'ayuda', text: 'Toca la tarjeta para ver la respuesta' })),
      h('div', { class: 'cara atras', 'aria-hidden': 'true' },
        h('p', { class: 'etq', text: 'Respuesta' }),
        h('p', { class: 'respuesta', text: q.opciones[q.correcta] }),
        h('p', { class: 'explicacion', text: q.explicacion })));
    cont.appendChild(h('div', { class: 'flip' }, inner));
    cont.appendChild(h('div', { class: 'acciones' },
      boton('Anterior', function () { moverTarjeta(-1); }, true),
      boton('Voltear', voltear),
      boton('Siguiente', function () { moverTarjeta(1); }, true)));
    cont.appendChild(h('div', { class: 'acciones' },
      boton(sabe ? 'La sé ✓' : 'Marcar como sabida', function () {
        if (sabidas[idx]) delete sabidas[idx]; else sabidas[idx] = true;
        guardarSabidas();
        if (tj.solo && sabidas[idx]) { pintarTarjetas(); enfocar('#vista-tarjetas .flip-inner'); }
        else pintarTarjetas();
      }, true, { 'aria-pressed': sabe ? 'true' : 'false' }),
      boton('Mezclar', function () { tj.orden = barajar(tj.orden); tj.pos = 0; pintarTarjetas(); }, true),
      h('label', { class: 'check' },
        h('input', { type: 'checkbox', checked: tj.solo, onchange: function (e) { tj.solo = e.target.checked; tj.pos = 0; pintarTarjetas(); } }),
        'Solo las que no sé')));
  }

  // ------------------------------------------------------------------ comisión
  var TEMAS = ['Todas'];
  C.forEach(function (c) { if (TEMAS.indexOf(c.tema) < 0) TEMAS.push(c.tema); });
  var cm = { tema: 'Todas', pos: 0, ver: false };
  var reloj = { id: null, fin: 0, total: 60 };
  function listaComision() {
    return rango(C.length).filter(function (i) { return cm.tema === 'Todas' || C[i].tema === cm.tema; });
  }
  function pararReloj() { if (reloj.id) { clearInterval(reloj.id); reloj.id = null; } }
  function formatear(s) { return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2); }
  function tickReloj() {
    var caja = document.querySelector('#vista-comision .reloj'); if (!caja) { pararReloj(); return; }
    var resta = Math.max(0, Math.ceil((reloj.fin - Date.now()) / 1000));
    caja.querySelector('.cuenta').textContent = formatear(resta);
    caja.querySelector('.barra > span').style.width = (resta / reloj.total * 100) + '%';
    if (resta <= 0) {
      pararReloj();
      caja.classList.add('fin');
      caja.querySelector('.estado').textContent = 'Se acabó el minuto.';
      var b = caja.querySelector('button'); if (b) b.textContent = 'Otro minuto';
    }
  }
  function alternarReloj() {
    var caja = document.querySelector('#vista-comision .reloj');
    if (reloj.id) {
      pararReloj();
      caja.querySelector('button').textContent = 'Responder en 1 minuto';
      caja.querySelector('.estado').textContent = 'Detenido.';
      return;
    }
    caja.classList.remove('fin');
    reloj.fin = Date.now() + reloj.total * 1000;
    caja.querySelector('button').textContent = 'Detener';
    caja.querySelector('.estado').textContent = 'Corriendo.';
    tickReloj();
    reloj.id = setInterval(tickReloj, 250);
  }
  function moverComision(d, azar) {
    var l = listaComision(); if (!l.length) return;
    pararReloj();
    if (azar && l.length > 1) { var p; do { p = Math.floor(Math.random() * l.length); } while (p === cm.pos); cm.pos = p; }
    else cm.pos = (cm.pos + d + l.length) % l.length;
    cm.ver = false;
    pintarComision();
    enfocar('#vista-comision .pregunta-comision');
  }
  function pintarComision() {
    var cont = document.getElementById('vista-comision');
    cont.textContent = '';
    var l = listaComision();
    if (cm.pos >= l.length) cm.pos = 0;
    var c = C[l[cm.pos]];
    cont.appendChild(h('p', { class: 'consejo', text: 'De a dos: uno lee la pregunta y el otro responde en voz alta, como frente a la comisión. Después comparen con la respuesta sugerida.' }));
    cont.appendChild(h('div', { class: 'filtros', role: 'group', 'aria-label': 'Filtrar por tema' }, TEMAS.map(function (t) {
      return h('button', { class: 'filtro', type: 'button', 'aria-pressed': t === cm.tema ? 'true' : 'false', text: t,
        onclick: function () { pararReloj(); cm.tema = t; cm.pos = 0; cm.ver = false; pintarComision(); } });
    })));
    var relojCaja = h('div', { class: 'reloj' },
      boton('Responder en 1 minuto', alternarReloj, true),
      h('span', { class: 'cuenta', 'aria-hidden': 'true', text: formatear(reloj.total) }),
      h('div', { class: 'barra', 'aria-hidden': 'true' }, h('span', { style: 'width:100%' })),
      h('span', { class: 'estado', role: 'status', style: 'position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)' }));
    cont.appendChild(h('div', { class: 'card' },
      h('div', { class: 'meta' }, h('span', { text: 'Pregunta ' + (cm.pos + 1) + ' de ' + l.length }), h('span', { class: 'chip', text: c.tema })),
      h('h2', { class: 'pregunta-comision', tabindex: '-1', text: c.pregunta }),
      relojCaja,
      cm.ver ? h('div', { class: 'respuesta-sugerida', role: 'region', 'aria-label': 'Respuesta sugerida' },
        h('p', { class: 'etq', text: 'Respuesta sugerida' }), h('p', { text: c.respuesta })) : null,
      h('div', { class: 'acciones' },
        boton(cm.ver ? 'Ocultar respuesta' : 'Ver respuesta sugerida', function () { cm.ver = !cm.ver; pintarComisionSinReloj(); }),
        boton('Anterior', function () { moverComision(-1); }, true),
        boton('Siguiente', function () { moverComision(1); }, true),
        l.length > 1 ? boton('Al azar', function () { moverComision(0, true); }, true) : null)));
  }
  // Mostrar u ocultar la respuesta sin reiniciar el reloj que está corriendo
  function pintarComisionSinReloj() {
    var corriendo = !!reloj.id;
    var caja = document.querySelector('#vista-comision .reloj');
    var cuenta = caja ? caja.querySelector('.cuenta').textContent : null;
    var ancho = caja ? caja.querySelector('.barra > span').style.width : null;
    var terminado = caja ? caja.classList.contains('fin') : false;
    var textoBoton = caja ? caja.querySelector('button').textContent : null;
    var estado = caja ? caja.querySelector('.estado').textContent : '';
    pintarComision();
    var nueva = document.querySelector('#vista-comision .reloj');
    if (nueva && cuenta !== null) {
      nueva.querySelector('.cuenta').textContent = cuenta;
      nueva.querySelector('.barra > span').style.width = ancho;
      nueva.classList.toggle('fin', terminado);
      nueva.querySelector('button').textContent = textoBoton;
      nueva.querySelector('.estado').textContent = estado;
    }
    if (corriendo && !reloj.id) reloj.id = setInterval(tickReloj, 250);
    var r = document.querySelector('#vista-comision .respuesta-sugerida');
    if (r) r.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }

  // ------------------------------------------------------------------ teclado
  document.addEventListener('keydown', function (e) {
    if (e.altKey || e.ctrlKey || e.metaKey) return;
    var t = e.target, tag = t && t.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
    var enBoton = tag === 'BUTTON' || (t && t.getAttribute && t.getAttribute('role') === 'button');
    if (vistaActual === 'quiz' && qz && !qz.fin) {
      if (qz.respondida === null) {
        var k = '1234'.indexOf(e.key); if (k < 0) k = 'abcd'.indexOf(e.key.toLowerCase());
        if (k >= 0 && k < qz.opciones.length) { e.preventDefault(); responder(qz.opciones[k]); }
      } else if (e.key === 'Enter' && !enBoton) { e.preventDefault(); siguiente(); }
    } else if (vistaActual === 'tarjetas') {
      if (e.key === 'ArrowRight') { e.preventDefault(); moverTarjeta(1); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); moverTarjeta(-1); }
      else if (e.key === ' ' && !enBoton) { e.preventDefault(); voltear(); }
    } else if (vistaActual === 'comision' && !enBoton) {
      if (e.key === 'ArrowRight') { e.preventDefault(); moverComision(1); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); moverComision(-1); }
    }
  });

  // ------------------------------------------------------------------ inicio
  nuevoQuiz(rango(Q.length));
  pintarTarjetas();
  pintarComision();
  var inicial = (location.hash || '').replace('#', '');
  mostrar(VISTAS.indexOf(inicial) >= 0 ? inicial : store.get('vista', 'quiz'), false);
  window.addEventListener('hashchange', function () {
    var v = (location.hash || '').replace('#', '');
    if (VISTAS.indexOf(v) >= 0) mostrar(v, false);
  });
})();
</script>
</body>
</html>
"""


def validar():
    """Revisa que las preguntas estén completas antes de generar la página."""
    claves_quiz = ["seccion", "pregunta", "opciones", "correcta", "explicacion", "pista", "si_acierta", "si_falla"]
    for n, q in enumerate(QUIZ, 1):
        for k in claves_quiz:
            if k not in q:
                raise ValueError(f"Quiz, pregunta {n}: falta el campo '{k}'.")
        if len(q["opciones"]) < 2:
            raise ValueError(f"Quiz, pregunta {n}: necesita al menos dos opciones.")
        if not 0 <= q["correcta"] < len(q["opciones"]):
            raise ValueError(f"Quiz, pregunta {n}: 'correcta' debe estar entre 0 y {len(q['opciones']) - 1}.")
    for n, c in enumerate(COMISION, 1):
        for k in ["tema", "pregunta", "respuesta"]:
            if not c.get(k):
                raise ValueError(f"Comisión, pregunta {n}: falta el campo '{k}'.")


def generar(salida="index.html"):
    validar()
    datos = {"titulo": TITULO_TESIS, "quiz": QUIZ, "comision": COMISION}
    # "</" se escapa para que ningún texto pueda cerrar el bloque <script> por accidente
    json_datos = json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")
    html = PLANTILLA.replace("__DATOS__", json_datos)
    Path(salida).write_text(html, encoding="utf-8")
    print(f"Listo: {salida} con {len(QUIZ)} preguntas de quiz y {len(COMISION)} preguntas de la comisión.")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]  # Colab agrega argumentos propios que empiezan con "-"
    generar(args[0] if args and args[0].endswith(".html") else "index.html")

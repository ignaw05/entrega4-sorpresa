"""Aplicación de la Entrega 4: ¿La sorpresa del balance mueve la acción?

Correr local:   streamlit run app.py
Datos: silver_stocks_2.csv (el Silver del pipeline). Si no está en la carpeta, se baja del Drive del proyecto.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

import graficos as g
import contenido as c
import modelo as m

AQUI = Path(__file__).parent
ARCHIVO = AQUI / 'silver_stocks_2.csv'
DRIVE_ID = '1EFASiJezcUvgZku6Z-ixgfOc2740E9M_'

st.set_page_config(page_title='¿La sorpresa del balance mueve la acción?', layout='wide',
                   initial_sidebar_state='expanded')


@st.cache_data(show_spinner='Cargando los balances…')
def cargar_datos():
    if not ARCHIVO.is_file():
        import gdown
        gdown.download(id=DRIVE_ID, output=str(ARCHIVO), quiet=True)
    df = pd.read_csv(ARCHIVO, low_memory=False)
    df['reported_date'] = pd.to_datetime(df['reported_date'], errors='coerce')
    return df.replace([np.inf, -np.inf], np.nan)


def html(texto):
    """Escribe HTML sin sangría (en markdown, 4 espacios al inicio serían un bloque de código)."""
    st.markdown('\n'.join(linea.strip() for linea in texto.strip().splitlines()), unsafe_allow_html=True)


def grafico(chart):
    st.altair_chart(g.estilo(chart), width='content', theme=None)


# ---------- Estilo ----------
st.markdown(f'<style>{(AQUI / "estilo.css").read_text()}</style>', unsafe_allow_html=True)

with st.sidebar:
    html("""
    <div class="menu">
    <p class="marca">Ciencia de Datos · UTN FRM · 2026<br>Proyecto Integrador</p>
    <div class="tallo"><h3>La historia</h3><ol>
    <li><a href="#portada">El proyecto</a></li>
    <li><a href="#datos">Los datos</a></li>
    <li><a href="#hallazgos">Lo que encontramos</a></li>
    <li><a href="#modelo">El modelo</a></li></ol></div>
    <div class="copa"><h3>Tu turno</h3><ol>
    <li><a href="#explora">Explorá los balances</a></li>
    <li><a href="#proba">Probá el modelo</a></li>
    <li><a href="#simula">Simulá una inversión</a></li></ol>
    <p class="copa-nota">La historia se lee en orden. Acá las preguntas las hacés vos.</p></div>
    </div>
    """)

df_stocks = cargar_datos()

import joblib

ARCH_MODELO, ARCH_PRED = AQUI / 'modelo_final.joblib', AQUI / 'predicciones.csv'


def completar_metricas(artefacto, predicciones, datos):
    """Completa métricas del piso y valida que el test guardado corresponda al Silver actual."""
    predicciones['reported_date'] = pd.to_datetime(predicciones['reported_date'], errors='coerce')
    _, train, val, test = m.preparar(datos)
    test_guardado = predicciones[predicciones['conjunto'] == 'Test'].copy()
    columnas = ['ticker', 'reported_date', m.OBJETIVO]
    actual = test[columnas].sort_values(columnas[:2]).reset_index(drop=True)
    guardado = test_guardado[columnas + ['prediccion']].sort_values(columnas[:2]).reset_index(drop=True)
    if len(actual) != len(guardado) or not actual[columnas[:2]].equals(guardado[columnas[:2]]):
        return False
    if not np.allclose(actual[m.OBJETIVO], guardado[m.OBJETIVO], equal_nan=False):
        return False

    metricas = dict(artefacto.get('metricas', {}))
    mae_modelo_test = float(np.mean(np.abs(actual[m.OBJETIVO].to_numpy() - guardado['prediccion'].to_numpy())))
    train_val = pd.concat([train, val])
    mae_piso_test = float(np.mean(np.abs(test[m.OBJETIVO].to_numpy() - train_val[m.OBJETIVO].mean())))
    anios_cv = sorted(train['anio'].unique())[-5:]
    errores_piso = []
    for anio in anios_cv:
        anterior = train[train['anio'] < anio]
        siguiente = train[train['anio'] == anio]
        errores_piso.append(float(np.mean(np.abs(
            siguiente[m.OBJETIVO].to_numpy() - anterior[m.OBJETIVO].mean()))))
    metricas.update({
        'objetivo': m.VERSION_OBJETIVO,
        'mae_test': mae_modelo_test,
        'mae_piso_test': mae_piso_test,
        'mae_piso_cv': float(np.mean(errores_piso)),
        'mae_piso_cv_desvio': float(np.std(errores_piso, ddof=1)),
        'mejora_mae_test_pct': float((mae_piso_test - mae_modelo_test) / mae_piso_test * 100),
    })
    artefacto['metricas'] = metricas
    artefacto['objetivo'] = m.VERSION_OBJETIVO
    return True


@st.cache_resource(show_spinner='Preparando el modelo de reacción a tres ruedas…')
def cargar_modelo(_datos, version_datos):
    """Carga el artefacto de la reacción a tres ruedas o lo entrena si el archivo no corresponde."""
    art = pred = None
    if ARCH_MODELO.is_file() and ARCH_PRED.is_file():
        try:
            guardado = joblib.load(ARCH_MODELO)
            pred_guardado = pd.read_csv(ARCH_PRED)
            mismo_objetivo = (guardado.get('objetivo') in (None, m.VERSION_OBJETIVO)
                              and m.OBJETIVO in pred_guardado.columns)
            if mismo_objetivo and completar_metricas(guardado, pred_guardado, _datos):
                art, pred = guardado, pred_guardado
                joblib.dump(art, ARCH_MODELO, compress=3)
        except Exception:
            art = pred = None
    if art is None or pred is None:
        with st.spinner('Entrenando con el objetivo corregido. La primera carga puede tardar unos minutos…'):
            resultado = m.entrenar(_datos)
        art = {k: resultado[k] for k in ['pipe', 'calibrador', 'umbral', 'metricas', 'referencia']}
        art['objetivo'] = m.VERSION_OBJETIVO
        pred = resultado['predicciones']
        try:
            joblib.dump(art, ARCH_MODELO, compress=3)
            columnas = list(dict.fromkeys([
                'ticker', 'reported_date', 'trimestre', 'conjunto', *m.COLUMNAS_CRUDAS, 'open_adj_lead',
                'close_adj_lead3', m.OBJETIVO, 'retorno_operable', 'retorno_esperado', 'confianza', 'compraria'
            ]))
            pred[columnas].to_csv(ARCH_PRED, index=False)
        except OSError:
            pass
    pred['reported_date'] = pd.to_datetime(pred['reported_date'], errors='coerce')
    return art, pred


version_datos = (ARCHIVO.stat().st_mtime_ns, ARCHIVO.stat().st_size)
ART, PRED = cargar_modelo(df_stocks, version_datos)
UMBRAL = ART['umbral']
U_TXT = f'{UMBRAL:g} %'.replace('.', ',')


def num(v, dec=2):
    return f'{v:,.{dec}f}'.replace(',', 'X').replace('.', ',').replace('X', '.').replace('-', '−')


TEST_PRED = PRED[PRED['conjunto'] == 'Test'].copy()
TEST_MONTOS = m.simular_presupuesto(
    m.peso_modelo(TEST_PRED['retorno_esperado'], TEST_PRED['confianza'], UMBRAL),
    TEST_PRED['open_adj_lead'], 1000)
TEST_RESUMEN = m.resultado(TEST_MONTOS, TEST_PRED['retorno_operable'], 1000)
TEST_GANADORAS = int((TEST_PRED.loc[TEST_MONTOS > 0, 'retorno_operable'] > 0).sum())
TEST_COMPRAS = int((TEST_MONTOS > 0).sum())

# ---------- Portada ----------
html(f"""
<div id="portada"></div>
<p class="etapa tallo">El proyecto</p>
<h1>¿Los datos publicados con el balance anticipan la reacción de la acción en las tres ruedas siguientes?</h1>
<p class="lead">Cada trimestre una empresa presenta su balance, y su dato más esperado es la ganancia por acción (EPS).
Días antes, los analistas publican cuánto esperan. Si la diferencia entre lo esperado y lo real —la sorpresa— dice algo
sobre la empresa, el precio de la acción tendría que reaccionar a ella.</p>
<p class="oracion">El modelo estima el retorno hasta el cierre de la tercera rueda usando la información del balance y datos previos, sin usar la apertura siguiente como predictor; después compara el precio estimado con esa apertura para evaluar una compra.</p>
<div class="nums">
<div class="num"><span>+24,4 pp</span><p>más probabilidad de caída fuerte con sorpresa negativa que con positiva, a igual magnitud</p></div>
<div class="num"><span>{num(ART['metricas']['mae_test'])} pp</span><p>MAE del modelo en el test: retorno del cierre previo al cierre de la tercera rueda</p></div>
<div class="num"><span>{num(ART['metricas']['mae_piso_test'])} pp</span><p>MAE de la referencia que predice la media, sobre el mismo test</p></div>
</div>
<p class="nota">Test temporal 2026Q3: {num(len(TEST_PRED), 0)} balances; con 1.000 USD simulados, {TEST_COMPRAS} compras ({TEST_GANADORAS} ganadoras), resultado {num(TEST_RESUMEN['ganancia (USD)'])} USD antes de costos. Captura del pipeline: 26/10/2026.</p>
""")

# ---------- Los datos ----------
html("""
<div id="datos" class="seccion"></div>
<p class="etapa tallo">Los datos</p>
<h2>La sorpresa separa grupos de reacción, aunque el movimiento a tres ruedas sigue siendo disperso</h2>
<p>Cada empresa presenta datos fundamentales —márgenes, flujo de caja, deuda— y su dato más importante, la ganancia
por acción (EPS). Los analistas predicen el EPS, y la diferencia entre lo predicho y lo real es la sorpresa. Con la
sorpresa y los fundamentales se quiere anticipar cuánto sube o baja la acción en los tres días siguientes.</p>
<p>Cada columna reúne balances con sorpresas similares, de menor a mayor. El retorno se mide desde el último cierre previo
hasta el cierre de la tercera rueda. La marca naranja indica la mediana;
la caja y la línea muestran la dispersión. Compará cuánto se superponen los grupos antes de concluir que la sorpresa anticipa el movimiento.</p>
""")
grafico(g.grafico_datos(df_stocks))
with st.expander('Cómo lo sabemos'):
    html(f"""
    <h4>De dónde salen y cómo se obtienen</h4>
    <p>Los datos los obtiene el pipeline de Airflow del proyecto, que integra resultados, perfiles y precios de Yahoo Finance
    con información contable de SEC EDGAR. La captura usada es del 26 de octubre de 2026; los anuncios abarcan del
    25 de enero de 2008 al 23 de octubre de 2026.</p>
    <h4>Qué es una fila</h4>
    <p>Cada fila es el anuncio trimestral de una empresa en un período fiscal, identificado por <code>ticker</code> y
    <code>fiscal_quarter_end</code>. No hay dos anuncios de la misma empresa en el mismo trimestre.</p>
    <h4>Qué se filtró, paso por paso</h4>
    <p>El punto de partida es el Silver que deja el pipeline: 11.317 anuncios de 585 empresas, con 37 columnas.</p>
    {c.T_FILTROS}
    <h4>Cómo se reparten las 11.235 filas</h4>
    <p>La partición es por fecha, no al azar, porque el modelo se usa para predecir balances futuros: se ajusta con todo
    lo anterior a 2026, se elige con 2026Q1 y Q2 y se mide una sola vez con 2026Q3, el último trimestre completo.</p>
    {c.T_PARTICION}
    <h4>Columnas descartadas por fuga</h4>
    <p><code>ma30</code> sigue en el dataset pero no entra al modelo, porque el promedio de 30 días incluye la rueda de
    reacción al anuncio. Los precios posteriores (<code>open_adj_lead</code>, <code>close_adj_lead3</code> y
    <code>close_adj_lead7</code>) no son predictores: <code>close_adj_lead3</code> define el resultado estimado, mientras
    que la apertura se usa después para decidir si el precio estimado deja margen de compra. Los fundamentales se vinculan por trimestre fiscal, pero el dataset no conserva la fecha histórica de
    disponibilidad por campo; hay que verificar su publicación antes de tratarlos como conocidos al anunciarse.</p>
    """)

# ---------- Lo que encontramos ----------
html("""
<div id="hallazgos" class="seccion"></div>
<p class="etapa tallo">Lo que encontramos</p>
<h2>A igual magnitud, las sorpresas negativas se asocian con más caídas en la primera apertura</h2>
<p>Este hallazgo describe el salto entre el cierre previo y la apertura negociable; no es el objetivo apertura→tercera
rueda del modelo. Dentro de cada grupo de magnitud, compará la frecuencia de caídas para cada signo de sorpresa.</p>
""")
grafico(g.grafico_hallazgo(df_stocks))
with st.expander('Cómo lo sabemos'):
    html("""
    <h4>Una hipótesis que se sostuvo en el EDA: a igual magnitud, las negativas se asocian con más caídas al abrir</h4>
    <p>En el análisis de la Entrega 2, entre anuncios con una sorpresa de magnitud parecida, los que quedaron por debajo del consenso tuvieron
    <b>24,4 puntos porcentuales más</b> de probabilidad de una caída fuerte que los que quedaron por encima
    (IC 95 % por empresa: 21,4 a 26,9 pp). Está en verde (≥ 15 pp) y se repite en los cuatro grupos de magnitud: en el de
    mayor sorpresa, cae fuerte el 50,0 % de las negativas y el 12,7 % de las positivas. Una caída fuerte es un retorno de
    −1,98 % o menos entre el cierre previo y la primera apertura negociable (el primer cuartil de ese retorno). Esta
    diferencia es una asociación descriptiva, no una prueba causal.</p>
    <h4>Una que no: los anuncios pre-market no reaccionan distinto que los post-market</h4>
    <p>El movimiento a 3 días es parecido: 4,98 % en promedio, sin importar el signo, para los 6.589 anuncios pre-market,
    contra 5,39 % para los 4.600 post-market. La diferencia de 0,4 pp da un d de Cohen de 0,08 (IC 95 % por empresa:
    0,02 a 0,17), muy por debajo del corte de 0,20: rojo. Tampoco cambia la dirección (mediana de +0,41 % contra +0,50 %)
    ni cuánto pesa la sorpresa: la correlación de Spearman entre sorpresa y retorno es 0,27 pre-market y 0,25 post-market.
    Quedan afuera los 64 anuncios sin hora informada.</p>
    <h4>Qué se compara</h4>
    <p>Los anuncios se dividen en cuatro grupos del mismo tamaño según la magnitud de la sorpresa (su valor absoluto), y
    dentro de cada grupo se compara cuántos tuvieron una caída fuerte entre las sorpresas negativas y las positivas; así se
    compara a igual magnitud. Para pre-market y post-market se compara el tamaño del movimiento a 3 días, sin importar si
    subió o bajó, con el d de Cohen (rojo &lt; 0,20, amarillo hasta 0,80, verde desde 0,80).</p>
    """)

# ---------- El modelo ----------
html(f"""
<div id="modelo" class="seccion"></div>
<p class="etapa tallo">El modelo</p>
<h2>El modelo anticipa el cierre de la tercera rueda sin conocer la apertura siguiente</h2>
<p>La salida del Random Forest es el retorno desde el último cierre previo al anuncio hasta el cierre de la tercera rueda.
La apertura siguiente no entra al modelo: luego se usa para traducir ese cierre estimado a un retorno potencial de compra.
El umbral de {U_TXT} se ajusta en validación y la decisión se evalúa aparte en el trimestre de test.</p>
""")
grafico(g.grafico_mae(ART['metricas']))
html(f"""
<h3 class="sub">La métrica, el piso y la validación</h3>
<p>El objetivo es el retorno porcentual entre el cierre previo al anuncio (<code>close_adj_lag1</code>) y el cierre de la
tercera rueda (<code>close_adj_lead3</code>). Se mide el error absoluto medio en puntos porcentuales.
El piso predice siempre la media del entrenamiento. La validación cruzada respeta el orden temporal y el test 2026Q3
queda separado de la selección.</p>
""")
with st.expander('Cómo lo sabemos'):
    html(f"""
    <h4>La comparación completa</h4>
    {c.tabla_metricas(ART['metricas'])}
    <p>Mejora del MAE en test frente al piso: {num(ART['metricas']['mejora_mae_test_pct'])} %. Si la mejora es pequeña
    frente a la variación entre años, no hay evidencia suficiente para presentar el modelo como un predictor fuerte.</p>
    <h4>Cómo se fijó el umbral</h4>
    <p>El umbral de {U_TXT} se elige usando la validación temporal, no el test. La búsqueda maximiza el retorno medio
    simulado sobre los presupuestos y exige un mínimo de compras. Como se selecciona dentro de la validación, ese retorno
    es una decisión de ajuste, no una estimación independiente de rendimiento.</p>
    <h4>Cómo decide cuáles comprar</h4>
    <p>Se compra una acción solo si su retorno esperado desde la apertura supera el umbral. El presupuesto se gasta una sola
    vez y se reparte entre las acciones que lo superan, según la confianza calibrada del modelo (la probabilidad de que la
    acción suba): cada una recibe una parte proporcional a cuánto pasa esa probabilidad del 50 %, y si no pasa del 50 % no
    se compra. Se compran acciones enteras al precio de apertura, lo que sobra del redondeo se usa para sumar acciones de
    las de mayor confianza, se vende al cierre del 3er día hábil, y el resultado es la ganancia sobre el presupuesto.</p>
    <p>Primero se reconstruye el cierre estimado: <code>close_adj_lag1 × (1 + retorno_predicho / 100)</code>. Después se
    compara con la apertura negociable: <code>(cierre_estimado / open_adj_lead − 1) × 100</code>. Esta segunda cuenta se
    hace fuera del modelo; la apertura no altera la predicción.</p>
    <h4>Simulación del test, con 1.000 USD</h4>
    <p>En 2026Q3 el modelo habría realizado {TEST_COMPRAS} compras, {TEST_GANADORAS} con retorno positivo, con un resultado
    de {num(TEST_RESUMEN['ganancia (USD)'])} USD ({num(TEST_RESUMEN['retorno s/ presupuesto (%)'])} % del presupuesto),
    antes de comisiones, impuestos y deslizamiento. El trimestre contiene {num(len(TEST_PRED), 0)} balances; por eso la
    simulación es un resultado de una ventana temporal acotada, no una garantía de rendimiento futuro.</p>
    """)

# ---------- Tu turno ----------
@st.cache_resource(show_spinner=False)
def chart_explora(_pred, umbral):
    return g.estilo(g.grafico_explora(_pred, umbral))

def delta(v):   # con el guion común, para que Streamlit pinte la flecha según el signo
    return f'{v:+.2f} % del presupuesto'.replace('.', ',')


# ---------- Explorá ----------
html("""
<div id="explora" class="seccion"></div>
<p class="etapa copa">Tu turno · Explorá</p>
<h2>Los balances del último trimestre: lo que esperaba el modelo, lo que pasó y si hubiera comprado</h2>
<p>Cada punto es un balance de 2026Q3 (julio a septiembre de 2026). A la derecha, los que el modelo esperaba que más
subieran; arriba, los que más subieron. El modelo compra los que quedan a la derecha del umbral de """ + U_TXT + """
(si además su confianza en que suba pasa el 50 %). Pasá el mouse por un punto para ver el detalle, y con los controles de
abajo del gráfico elegís un sector o te quedás con los que hubiera comprado.</p>
<p class="nota">Todo se mide como decide el modelo: desde el precio de apertura posterior al anuncio, el primero al que
se puede comprar sabiendo el balance, hasta el cierre del 3er día hábil. El modelo que predice estos balances es el
final, entrenado con todo lo anterior a julio de 2026: no los vio.</p>
""")
st.altair_chart(chart_explora(PRED, UMBRAL), width='content', theme=None)


# ---------- Probá el modelo ----------
html(f"""
<div id="proba" class="seccion"></div>
<p class="etapa copa">Tu turno · Probá el modelo</p>
<h2>Armá un balance y mirá cuánto esperaría subir la acción</h2>
<p>Cargá los datos publicados con un balance, o partí de uno real y cambiale lo que quieras. El modelo estima la reacción
hasta el cierre de la tercera rueda sin usar la apertura siguiente como predictor. La apertura se usa después para calcular
el retorno potencial de una compra.</p>
""")

REF = ART['referencia']


MILLONES = ['total_assets', 'total_current_assets', 'total_current_liabilities', 'total_revenue', 'net_income',
            'ebitda', 'operating_cashflow', 'capital_expenditures', 'dividend_payout', 'cash_and_equivalents']
PORCENTAJES = ['gross_margin', 'operating_margin', 'free_cash_flow_margin', 'debt_to_assets']
NOMBRES = {'total_assets': 'Activos totales', 'total_current_assets': 'Activo corriente',
           'total_current_liabilities': 'Pasivo corriente', 'total_revenue': 'Ventas', 'net_income': 'Ganancia neta',
           'ebitda': 'EBITDA', 'operating_cashflow': 'Flujo operativo', 'capital_expenditures': 'Inversión (capex)',
           'dividend_payout': 'Dividendos pagados', 'cash_and_equivalents': 'Caja', 'gross_margin': 'Margen bruto',
           'operating_margin': 'Margen operativo', 'free_cash_flow_margin': 'Margen de flujo libre',
           'debt_to_assets': 'Deuda / activos', 'close_adj_lag1': 'Precio de cierre previo',
           'surprise': 'Sorpresa (USD por acción)', 'surprise_pct': 'Sorpresa (%)'}

EJEMPLOS = df_stocks.dropna(subset=['reported_eps', 'consensus_eps', 'close_adj_lag1']).copy()
EJEMPLOS = EJEMPLOS[EJEMPLOS['reported_date'] >= '2025-01-01'].sort_values(['ticker', 'reported_date'])
EJEMPLOS['opcion'] = (EJEMPLOS['ticker'] + ' · ' + EJEMPLOS['reported_date'].dt.strftime('%d/%m/%Y') + ' · '
                      + EJEMPLOS['sector'].fillna('sin sector'))
OPCIONES = EJEMPLOS['opcion'].tolist()
DEFECTO = next((o for o in OPCIONES if o.startswith('NVDA · 25/02/2026')), OPCIONES[0])


def a_widgets(fila):
    """Pasa un balance real a los valores de los campos (millones de USD y porcentajes)."""
    ss = st.session_state
    for c in m.CATEGORICAS:
        ss[f'p_{c}'] = fila[c] if pd.notna(fila[c]) else REF['categorias'][c][0]
    if pd.isna(fila['report_time']):
        ss['p_report_time'] = 'desconocido'
    ss['p_reported_eps'], ss['p_consensus_eps'] = float(fila['reported_eps']), float(fila['consensus_eps'])
    ss['p_close_adj_lag1'] = float(fila['close_adj_lag1'])
    ss['p_open_adj_lead'] = float(fila['open_adj_lead']) if pd.notna(fila['open_adj_lead']) else 1.0
    for c in MILLONES:
        ss[f'p_{c}'] = float(fila[c] / 1e6) if pd.notna(fila[c]) else float(REF['mediana'][c] / 1e6)
    for c in PORCENTAJES:
        ss[f'p_{c}'] = float(fila[c] * 100) if pd.notna(fila[c]) else float(REF['mediana'][c] * 100)


def elegir_ejemplo():
    a_widgets(EJEMPLOS.loc[EJEMPLOS['opcion'] == st.session_state['p_ejemplo']].iloc[0])


if 'p_reported_eps' not in st.session_state:
    st.session_state['p_ejemplo'] = DEFECTO
    elegir_ejemplo()


def sorpresa_pct():
    ss = st.session_state
    return (ss['p_reported_eps'] - ss['p_consensus_eps']) / abs(ss['p_consensus_eps']) * 100 if ss['p_consensus_eps'] != 0 else np.nan


@st.fragment
def probar():
    st.selectbox('Partir de un balance real (desde 2025)', OPCIONES, key='p_ejemplo', on_change=elegir_ejemplo)
    izq, der = st.columns([1.05, 1], gap='large')
    with izq:
        with st.expander('La empresa', expanded=True):
            sectores = REF['categorias']['sector']
            st.selectbox('Sector', sectores, key='p_sector')
            industrias = REF['industrias_por_sector'].get(st.session_state['p_sector'], REF['categorias']['industry'])
            if st.session_state.get('p_industry') not in industrias:
                st.session_state['p_industry'] = industrias[0]
            st.selectbox('Industria', industrias, key='p_industry')
            a, b = st.columns(2)
            a.selectbox('Bolsa', REF['categorias']['exchange'], key='p_exchange')
            b.selectbox('Cuándo reporta', REF['categorias']['report_time'], key='p_report_time')
        with st.expander('La sorpresa y el precio', expanded=True):
            a, b = st.columns(2)
            a.number_input('EPS reportado (USD)', key='p_reported_eps', step=0.01, format='%.2f')
            b.number_input('EPS esperado por los analistas (USD)', key='p_consensus_eps', step=0.01, format='%.2f')
            a.number_input('Cierre previo al anuncio (USD)', key='p_close_adj_lag1', min_value=0.01, step=1.0, format='%.2f',
                           help='Dato previo al anuncio; se usa para construir variables de contexto.')
            b.number_input('Primera apertura negociable (USD)', key='p_open_adj_lead', min_value=0.01, step=1.0, format='%.2f',
                           help='Precio de entrada. No se usa como predictor: sirve para traducir el retorno estimado a un precio estimado.')
            st.metric('Sorpresa porcentual', f'{num(sorpresa_pct(), 1)} %' if np.isfinite(sorpresa_pct()) else '—')
        with st.expander('Resultados y balance (millones de USD)'):
            a, b = st.columns(2)
            for i, c in enumerate(MILLONES):
                (a if i % 2 == 0 else b).number_input(NOMBRES[c], key=f'p_{c}', step=10.0, format='%.1f')
        with st.expander('Márgenes y deuda (%)'):
            a, b = st.columns(2)
            for i, c in enumerate(PORCENTAJES):
                (a if i % 2 == 0 else b).number_input(NOMBRES[c], key=f'p_{c}', step=1.0, format='%.1f')

    ss = st.session_state
    caso = {c: ss[f'p_{c}'] for c in m.CATEGORICAS}
    caso['surprise'] = ss['p_reported_eps'] - ss['p_consensus_eps']
    caso['surprise_pct'] = caso['surprise'] / abs(ss['p_consensus_eps']) * 100 if ss['p_consensus_eps'] != 0 else np.nan
    caso['close_adj_lag1'] = ss['p_close_adj_lag1']
    precio_entrada = float(ss['p_open_adj_lead'])
    caso.update({c: ss[f'p_{c}'] * 1e6 for c in MILLONES})
    caso.update({c: ss[f'p_{c}'] / 100 for c in PORCENTAJES})
    X = pd.DataFrame([caso])[m.COLUMNAS_CRUDAS]
    pred = float(ART['pipe'].predict(X)[0])
    precio_estimado_3r = float(caso['close_adj_lag1'] * (1 + pred / 100))
    retorno_desde_apertura = float(m.esperado_desde_apertura(pd.DataFrame([caso | {
        'open_adj_lead': precio_entrada}], index=[0]), [pred])[0])
    probabilidad_subida = float(m.prob_subida(ART['calibrador'], [retorno_desde_apertura])[0])
    decision_compra = retorno_desde_apertura > UMBRAL and probabilidad_subida > 0.5

    fuera = [NOMBRES.get(c, c) for c in m.ENTRADA_NUM
             if pd.notna(caso[c]) and not (REF['rango'][c][0] <= caso[c] <= REF['rango'][c][1])]
    with der:
        st.metric('Reacción estimada por el modelo (cierre previo → cierre de 3 ruedas)', f'{num(pred)} %')
        st.metric('Potencial desde la apertura siguiente', f'{num(retorno_desde_apertura)} %',
                  delta='supera el umbral' if decision_compra else 'no supera el umbral')
        st.caption(f'Precio estimado al cierre de la tercera rueda: {num(precio_estimado_3r)} USD. '
                   f'Confianza estimada de retorno positivo: {num(probabilidad_subida * 100, 1)} %. '
                   'La apertura se usa solo después de predecir, para comparar el precio de entrada con la salida estimada.')
        if fuera:
            st.warning('Fuera de lo que vio el entrenamiento: ' + ', '.join(fuera) + '. El modelo no aprendió nada de '
                       'valores así; el Random Forest los trata como el valor más extremo que conoce, y la predicción '
                       'no es confiable.')


probar()


# ---------- Simulá una inversión ----------
html(f"""
<div id="simula" class="seccion"></div>
<p class="etapa copa">Tu turno · Simulá una inversión</p>
<h2>Elegí un presupuesto, un sector y un tamaño de empresa, y mirá cuánto habrías ganado</h2>
<p>Con los balances de 2026Q3 (julio a septiembre de 2026), que el modelo no vio. Es la regla de la Entrega 3, con el
umbral fijo en {U_TXT}: compra las acciones cuyo retorno esperado desde la apertura supera el umbral, reparte el
presupuesto según la confianza, compra acciones enteras en la apertura y vende al cierre del 3er día hábil. Con 1.000 USD y
todos los sectores da las mismas 4 compras de «El modelo».</p>
""")

T1, T2 = REF['terciles_activos']
PRED['tamano'] = pd.cut(PRED['total_assets'], [-np.inf, T1, T2, np.inf], labels=['Chicas', 'Medianas', 'Grandes']).astype(str)
Q3 = PRED['conjunto'] == 'Test'   # 2026Q3


@st.fragment
def simular():
    presupuesto = st.select_slider('Presupuesto (USD)', options=m.PRESUPUESTOS, value=1000)
    a, b = st.columns(2)
    todos_sect = sorted(PRED.loc[Q3, 'sector'].dropna().unique())
    sectores = a.multiselect('Sectores', todos_sect, default=todos_sect, placeholder='Elegí al menos uno')
    tamanos = b.multiselect('Tamaño de empresa (por activos totales)', ['Chicas', 'Medianas', 'Grandes'],
                            default=['Chicas', 'Medianas', 'Grandes'], placeholder='Elegí al menos uno',
                            help='Tercios de los activos totales del entrenamiento, como en la Entrega 3.')
    d = PRED[Q3 & PRED['sector'].isin(sectores) & PRED['tamano'].isin(tamanos)].reset_index(drop=True)
    if d.empty:
        st.info('No hay balances con esos filtros.')
        return
    precio, real = d['open_adj_lead'].to_numpy(), d['retorno_operable'].to_numpy()
    mod = m.simular_presupuesto(m.peso_modelo(d['retorno_esperado'], d['confianza'], UMBRAL), precio, presupuesto)
    r_mod = m.resultado(mod, real, presupuesto)

    k = st.columns(3)
    k[0].metric('Balances en el universo', num(len(d), 0))
    k[1].metric('Compras del modelo', r_mod['compras'])
    k[2].metric('Ganancia del modelo', f'{num(r_mod["ganancia (USD)"])} USD', delta(r_mod["retorno s/ presupuesto (%)"]))

    c = mod > 0
    if not c.any():
        st.info(f'En este universo ningún balance supera el umbral de {U_TXT} con confianza mayor a 50 %: el modelo no '
                'compra nada y el presupuesto queda sin usar. Probá con más sectores u otro tamaño.')
        return
    compras = d.loc[c, ['ticker', 'reported_date', 'sector', 'open_adj_lead', 'retorno_operable', 'retorno_esperado', 'confianza']].copy()
    compras['pago'] = mod[c]
    compras['acciones'] = np.round(mod[c] / precio[c]).astype(int)
    compras['ganancia'] = mod[c] * real[c] / 100
    compras['fecha'] = compras['reported_date'].dt.strftime('%d/%m/%Y')
    compras['confianza_pct'] = compras['confianza'] * 100
    st.altair_chart(g.estilo(g.grafico_simula_compras(compras)), width='content', theme=None)
    tabla = compras.sort_values('ganancia', ascending=False)[
        ['ticker', 'fecha', 'sector', 'acciones', 'open_adj_lead', 'pago', 'ganancia', 'retorno_operable', 'retorno_esperado', 'confianza_pct']]
    tabla.columns = ['Ticker', 'Fecha del balance', 'Sector', 'Acciones', 'Precio de compra (USD)', 'Pagó (USD)',
                     'Ganancia (USD)', 'Retorno real (%)', 'Retorno esperado (%)', 'Confianza (%)']
    fmt2 = {c: st.column_config.NumberColumn(format='%.2f') for c in tabla.columns[4:]}
    st.dataframe(tabla, hide_index=True, column_config=fmt2)


simular()

html("""<footer>Ciencia de Datos · UTN FRM · 2026 · Datos: Yahoo Finance y SEC EDGAR, captura del 26/10/2026.</footer>""")

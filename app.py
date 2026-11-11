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


# ---------- Estilo (el mismo de la versión HTML) ----------
st.markdown(f'<style>{(AQUI / "estilo.css").read_text()}</style>', unsafe_allow_html=True)
st.markdown("""<style>
.block-container{max-width:1010px;padding-top:2rem}
section[data-testid="stSidebar"]{background:#fafbfc;width:250px!important}
section[data-testid="stSidebar"]{width:260px!important}
.menu .marca{font-size:13px;color:var(--gris);margin:0 0 22px}
.menu h3{font-size:12px;letter-spacing:.08em;text-transform:uppercase;margin:22px 0 6px;padding:0}
.menu .tallo h3{color:var(--acento)} .menu .copa h3{color:var(--copa)}
.menu ol{list-style:none;margin:0;padding:0 0 0 4px}
.menu .tallo ol{border-left:3px solid var(--acento)} .menu .copa ol{border-left:3px solid var(--copa)}
.menu li{margin:0}
.menu li a{display:block;padding:5px 0 5px 12px;color:var(--tinta)!important;text-decoration:none!important;font-size:15px}
.menu .tallo li a:hover{color:var(--acento)!important;font-weight:600} .menu .copa li a:hover{color:var(--copa)!important;font-weight:600}
.menu .copa-nota{font-size:12.5px;color:var(--gris);margin:8px 0 0;line-height:1.4}
.stMain section{border:none;padding:0;max-width:none}
.seccion{border-top:1px solid var(--linea);padding-top:40px;margin-top:40px}
[data-testid="stExpander"] details{background:var(--suave);border-radius:8px;border:none}
[data-testid="stExpander"] summary p{font-weight:600;color:var(--acento);font-size:17px}
[data-testid="stExpander"] h4{margin:16px 0 6px;font-size:17px}
[data-testid="stExpander"] p{font-size:16px}
[data-testid="stMetricValue"]{font-size:30px}
h3.sub{font-size:20px;margin:28px 0 8px}
</style>""", unsafe_allow_html=True)

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

# ---------- Portada ----------
html("""
<div id="portada"></div>
<p class="etapa tallo">El proyecto</p>
<h1>¿En qué medida la sorpresa de resultados explica cuánto se mueve una acción en los tres días posteriores al anuncio?</h1>
<p class="lead">Cada trimestre una empresa presenta su balance, y su dato más esperado es la ganancia por acción (EPS).
Días antes, los analistas publican cuánto esperan. Si la diferencia entre lo esperado y lo real —la sorpresa— dice algo
sobre la empresa, el precio de la acción tendría que reaccionar a ella.</p>
<p class="oracion">Una sorpresa negativa eleva 24 puntos el riesgo de una caída fuerte, y con esa señal un Random Forest
elige compras que ganan 6,6 % del presupuesto en validación, aunque predice el retorno apenas mejor que la media.</p>
<div class="nums">
<div class="num"><span>+24,4 pp</span><p>más probabilidad de caída fuerte con sorpresa negativa que con positiva, a igual magnitud</p></div>
<div class="num"><span>6,6 %</span><p>de retorno sobre el presupuesto en validación, contra 0,3 % de comprar todo</p></div>
<div class="num"><span>−4 %</span><p>de error (MAE 5,15 contra 5,38 pp del piso): menos que el desvío entre folds</p></div>
</div>
<p class="nota">Medido sobre 11.235 balances trimestrales de 585 empresas, del 25/01/2008 al 30/09/2026
(captura del pipeline del 26/10/2026).</p>
""")

# ---------- Los datos ----------
html("""
<div id="datos" class="seccion"></div>
<p class="etapa tallo">Los datos</p>
<h2>Las empresas presentan su balance trimestral, el mercado predice su ganancia días antes, y una gran sorpresa mueve más el precio de la acción</h2>
<p>Cada empresa presenta datos fundamentales —márgenes, flujo de caja, deuda— y su dato más importante, la ganancia
por acción (EPS). Los analistas predicen el EPS, y la diferencia entre lo predicho y lo real es la sorpresa. Con la
sorpresa y los fundamentales se quiere anticipar cuánto sube o baja la acción en los tres días siguientes.</p>
<p>Cada columna es un grupo de balances con sorpresas parecidas, ordenados de la más negativa a la más positiva.
Mirá la marca naranja: el retorno típico pasa de negativo a positivo a medida que la sorpresa mejora, y en los
extremos la caja se estira.</p>
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
    reacción al anuncio. Los precios posteriores al anuncio (<code>open_adj_lead</code>, <code>close_adj_lead3</code> y
    <code>close_adj_lead7</code>) tampoco son entradas: se usan solo para definir el retorno y para medir cuánto se gana
    o se pierde.</p>
    """)

# ---------- Lo que encontramos ----------
html("""
<div id="hallazgos" class="seccion"></div>
<p class="etapa tallo">Lo que encontramos</p>
<h2>Una sorpresa negativa casi siempre viene acompañada de un retorno malo, y el efecto crece a medida que la sorpresa es más negativa</h2>
<p>La magnitud de la sorpresa por sí sola no tiene una relación fuerte con el retorno; el signo, sí. Dentro de cada
grupo de magnitud, la barra naranja (sorpresa negativa) es siempre mucho más alta que la azul (positiva).</p>
""")
grafico(g.grafico_hallazgo(df_stocks))
with st.expander('Cómo lo sabemos'):
    html("""
    <h4>Una hipótesis que se sostuvo: a igual magnitud de sorpresa, las negativas elevan el riesgo de caída fuerte</h4>
    <p>Entre anuncios con una sorpresa de magnitud parecida, los que quedaron por debajo del consenso tuvieron
    <b>24,4 puntos porcentuales más</b> de probabilidad de una caída fuerte que los que quedaron por encima
    (IC 95 % por empresa: 21,4 a 26,9 pp). Está en verde (≥ 15 pp) y se repite en los cuatro grupos de magnitud: en el de
    mayor sorpresa, cae fuerte el 50,0 % de las negativas y el 12,7 % de las positivas. Una caída fuerte es un retorno de
    −1,98 % o menos entre el cierre previo y la apertura posterior al anuncio (el primer cuartil de ese retorno).</p>
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
html("""
<div id="modelo" class="seccion"></div>
<p class="etapa tallo">El modelo</p>
<h2>Random Forest es el modelo que más dinero gana: con un presupuesto acotado, es el que obtiene más ganancia</h2>
<p>Con un umbral de 18,5 %, el modelo compra una acción solo si espera que suba 18,5 % o más. Con un presupuesto
limitado, decide en qué acciones invertir según la confianza que tiene en cada subida. La barra con borde negro es el
elegido; las dos de la derecha son las referencias sin modelo.</p>
""")
grafico(g.grafico_modelos())
html("""
<h3 class="sub">La métrica, el piso y la validación</h3>
<p>El modelo predice el retorno a 3 días y se mide con el MAE, en puntos porcentuales del retorno. El piso es un
modelo que predice siempre el retorno medio. Los modelos se comparan con validación cruzada temporal sobre el
entrenamiento: cada pedazo entrena con los años anteriores y valida en el siguiente. Todos le ganan al piso, pero por
menos que el desvío entre pedazos.</p>
""")
grafico(g.grafico_mae())
with st.expander('Cómo lo sabemos'):
    html(f"""
    <h4>La comparación completa</h4>
    {c.T_MAE}
    <h4>Cómo se eligió: la ganancia en validación</h4>
    <p>En validación, cada modelo se probó con 28 presupuestos (de 100 a 10.000 USD) y umbrales de 0 a 44,5 %, y se eligió
    un único umbral para todos los presupuestos: el que da mayor retorno promedio sobre el presupuesto, siempre que deje
    comprar al menos 3 acciones. El modelo final es el de mayor retorno promedio con su umbral.</p>
    {c.T_RETORNO}
    <h4>Cómo decide cuáles comprar</h4>
    <p>Se compra una acción solo si su retorno esperado desde la apertura supera el umbral. El presupuesto se gasta una sola
    vez y se reparte entre las acciones que lo superan, según la confianza calibrada del modelo (la probabilidad de que la
    acción suba): cada una recibe una parte proporcional a cuánto pasa esa probabilidad del 50 %, y si no pasa del 50 % no
    se compra. Se compran acciones enteras al precio de apertura, lo que sobra del redondeo se usa para sumar acciones de
    las de mayor confianza, se vende al cierre del 3er día hábil, y el resultado es la ganancia sobre el presupuesto.</p>
    <h4>En el test: qué compra con 1.000 USD</h4>
    <p>En 2026Q3, con 1.000 USD, el modelo hace 4 compras: gana una y pierde tres, y termina con +38,55 USD (+3,9 % sobre el
    presupuesto). Las cuatro esperaban subir alrededor de 20 % con una confianza de 55 %: el retorno esperado está muy por
    encima de lo que pasa, y el resultado depende de una sola compra que salió bien.</p>
    {c.T_COMPRAS}
    <h4>En qué se apoya</h4>
    <p>Entre paréntesis, cuánto cambia el retorno esperado (en puntos porcentuales) si la columna pasa de un valor bajo
    (percentil 25) a uno alto (percentil 75), con todo lo demás igual. En casi todos los sectores lo que más empuja a comprar
    es la sorpresa, en línea con el hallazgo de la sección anterior.</p>
    {c.T_SOPORTE}
    """)

# ---------- Tu turno ----------
import modelo as m

ARCH_MODELO, ARCH_PRED = AQUI / 'modelo_final.joblib', AQUI / 'predicciones.csv'


@st.cache_resource(show_spinner='Cargando el modelo…')
def cargar_modelo():
    """El modelo que deja entrenar.py. Si no está (o no se puede leer), se entrena acá con la misma semilla."""
    try:
        import joblib
        art = joblib.load(ARCH_MODELO)
        pred = pd.read_csv(ARCH_PRED)
    except Exception:
        with st.spinner('Entrenando el modelo de la Entrega 3 (una sola vez, tarda un par de minutos)…'):
            r = m.entrenar(df_stocks)
        art, pred = {k: r[k] for k in ['pipe', 'calibrador', 'umbral', 'metricas', 'referencia']}, r['predicciones']
    pred['reported_date'] = pd.to_datetime(pred['reported_date'])
    return art, pred


@st.cache_resource(show_spinner=False)
def chart_explora(_pred, umbral):
    return g.estilo(g.grafico_explora(_pred, umbral))


ART, PRED = cargar_modelo()
UMBRAL = ART['umbral']
U_TXT = f'{UMBRAL:g} %'.replace('.', ',')

def delta(v):   # con el guion común, para que Streamlit pinte la flecha según el signo
    return f'{v:+.2f} % del presupuesto'.replace('.', ',')


def num(v, dec=2):
    return f'{v:,.{dec}f}'.replace(',', 'X').replace('.', ',').replace('X', '.').replace('-', '−')

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
<p>Cargá los datos de un balance, o partí de uno real y cambiale lo que quieras: el Random Forest final de la Entrega 3
predice cómo va a reaccionar el mercado, es decir, cuánto se mueve la acción desde el cierre previo al anuncio hasta el
cierre del 3er día hábil.</p>
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
            a.number_input('Precio de cierre previo (USD)', key='p_close_adj_lag1', min_value=0.01, step=1.0, format='%.2f',
                           help='El último cierre antes del anuncio: la reacción se mide desde acá.')
            b.metric('Sorpresa', f'{num(sorpresa_pct(), 1)} %' if np.isfinite(sorpresa_pct()) else '—')
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
    caso.update({c: ss[f'p_{c}'] * 1e6 for c in MILLONES})
    caso.update({c: ss[f'p_{c}'] / 100 for c in PORCENTAJES})
    X = pd.DataFrame([caso])[m.COLUMNAS_CRUDAS]
    pred = float(ART['pipe'].predict(X)[0])

    fuera = [NOMBRES.get(c, c) for c in m.ENTRADA_NUM
             if pd.notna(caso[c]) and not (REF['rango'][c][0] <= caso[c] <= REF['rango'][c][1])]
    with der:
        st.metric('El modelo predice que en 3 días la acción se mueve', f'{num(pred)} %',
                  help='Desde el cierre previo al anuncio hasta el cierre del 3er día hábil.')
        st.caption('Es la reacción del mercado al balance: cuánto se mueve la acción desde el último cierre antes del '
                   'anuncio hasta el cierre del 3er día hábil.')
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

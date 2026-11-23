"""Aplicación de la Entrega 4: ¿La sorpresa del balance mueve la acción?

Correr local:   streamlit run app.py
Datos: silver_stocks_2.csv (el Silver del pipeline). Si no está en la carpeta, se baja del Drive del proyecto.
"""
from pathlib import Path

from html import escape

import numpy as np
import pandas as pd
import streamlit as st

import graficos as g
import contenido as c

AQUI = Path(__file__).parent
ARCHIVO = AQUI / 'silver_stocks_2.csv'
DRIVE_ID = '1EFASiJezcUvgZku6Z-ixgfOc2740E9M_'

st.set_page_config(page_title='¿Cuánto afecta la sorpresa a la acción?', layout='wide',
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


def num(v, dec=2):
    return f'{v:,.{dec}f}'.replace(',', 'X').replace('.', ',').replace('X', '.').replace('-', '−')


def delta(v):   # con el guion común, para que Streamlit pinte la flecha según el signo
    return f'{v:+.2f} % del presupuesto'.replace('.', ',')


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
    <li><a href="#proba">Probá una sorpresa</a></li>
    <li><a href="#simula">Simulá una inversión</a></li></ol>
    <p class="copa-nota">La historia se lee en orden. Acá las preguntas las hacés vos.</p></div>
    </div>
    """)

df_stocks = cargar_datos()

# ---------- Portada ----------
html("""
<div id="portada"></div>
<p class="etapa tallo">El proyecto</p>
<h1>¿Cuánto afecta la sorpresa de un balance al precio de la acción en los tres días siguientes?</h1>
<p class="lead">Todos los trimestres, las empresas que cotizan en bolsa presentan su balance: cuánto ganaron o perdieron.
Antes de que se publique, los expertos del mercado pronostican ese resultado. La diferencia entre lo que esperaban y lo
que pasó es la <b>sorpresa</b>. Queremos saber cuánto influye esa sorpresa, medida en porcentaje, en el precio de la
acción durante los tres días posteriores al anuncio.</p>
<p class="oracion">La sorpresa marca hacia dónde va la acción, pero no cuánto se mueve. Cuando una empresa gana menos de
lo esperado, su acción cae en la mayoría de los casos; cuando gana más, sube más seguido. El tamaño del movimiento
depende de muchas otras cosas, y por eso un modelo acierta solo una parte. Aun así, alcanza para elegir compras que
ganaron dinero.</p>
<div class="nums">
<div class="num"><span>63 %</span><p>de las acciones con sorpresa negativa bajan en los 3 días siguientes. Con sorpresa positiva bajan el 42 %.</p></div>
<div class="num"><span>+6,6 %</span><p>ganó la estrategia del modelo sobre el presupuesto en el 1.er semestre de 2026. El dummy perdió 0,4 %.</p></div>
</div>
<p class="nota">Medido sobre 11.235 balances trimestrales de 585 empresas, del 25/01/2008 al 30/09/2026
(captura del pipeline del 26/10/2026).</p>
""")

# ---------- Los datos ----------
html("""
<div id="datos" class="seccion"></div>
<p class="etapa tallo">Los datos</p>
<h2>Cuanto peor es la sorpresa, peor le va a la acción</h2>
<p>Ordenamos los balances de la sorpresa más negativa (la empresa ganó mucho menos de lo esperado) a la más positiva
(ganó mucho más), y los partimos en cuatro grupos con la misma cantidad de balances: los cuartiles. Para cada cuartil,
el gráfico muestra cuánto se movió la acción en los tres días siguientes.</p>
""")
grafico(g.grafico_datos(df_stocks))
html("""
<p class="nota"><b>Qué mirar:</b> el número de cada cuartil es el retorno típico. De izquierda a derecha pasa de negativo a
positivo: el cuartil de las sorpresas más bajas es el único donde la acción típica cae. Pero las cajas son altas y se superponen: dentro de
un mismo grupo hay acciones que suben y otras que bajan mucho. La sorpresa inclina la balanza, no la decide.</p>
""")
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
    <p>En este gráfico y el siguiente quedan afuera los balances con sorpresa exactamente 0 %.</p>
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
<h2>Lo que más pesa es el signo: una sorpresa negativa multiplica el riesgo de una caída fuerte</h2>
<p>Separamos los balances en cuatro grupos según el tamaño de la sorpresa, sin importar el signo, y dentro de cada grupo
comparamos cuántas acciones tuvieron una <b>caída fuerte</b> (bajar 1,98 % o más apenas abre el mercado) entre las
sorpresas negativas y las positivas del mismo tamaño.</p>
""")
grafico(g.grafico_hallazgo(df_stocks))
html("""
<p class="nota"><b>Qué mirar:</b> en los cuatro grupos, la barra naranja (negativa) es mucho más alta que la azul
(positiva). Y la diferencia crece con el tamaño: en el grupo de las sorpresas más grandes, cae fuerte la mitad de las
negativas y solo una de cada ocho positivas. El mercado castiga más una mala noticia de lo que premia una buena.</p>
""")
html("""
    <h3 class="sub">Una hipótesis que se sostuvo: a igual magnitud de sorpresa, las negativas elevan el riesgo de caída fuerte</h3>
    <p>Entre anuncios con una sorpresa de magnitud parecida, los que quedaron por debajo del consenso tuvieron
    <b>24,4 puntos porcentuales más</b> de probabilidad de una caída fuerte que los que quedaron por encima
    (IC 95 % por empresa: 21,4 a 26,9 pp). Está en verde (≥ 15 pp) y se repite en los cuatro grupos de magnitud: en el de
    mayor sorpresa, cae fuerte el 50,0 % de las negativas y el 12,7 % de las positivas. Una caída fuerte es un retorno de
    −1,98 % o menos entre el cierre previo y la apertura posterior al anuncio (el primer cuartil de ese retorno).</p>
    <h3 class="sub">Una que no: los anuncios pre-market no reaccionan distinto que los post-market</h3>
    <p>El movimiento a 3 días es parecido: 4,98 % en promedio, sin importar el signo, para los 6.589 anuncios pre-market,
    contra 5,39 % para los 4.600 post-market. La diferencia de 0,4 pp da un d de Cohen de 0,08 (IC 95 % por empresa:
    0,02 a 0,17), muy por debajo del corte de 0,20: rojo. Tampoco cambia la dirección (mediana de +0,41 % contra +0,50 %)
    ni cuánto pesa la sorpresa: la correlación de Spearman entre sorpresa y retorno es 0,27 pre-market y 0,25 post-market.
    Quedan afuera los 64 anuncios sin hora informada.</p>
    """)

# ---------- El modelo ----------
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


@st.cache_data(show_spinner='Calculando la calibración del umbral…')
def calibracion(_pred):
    """La grilla umbral × presupuesto en validación, resumida por umbral, para el modelo y el dummy."""
    _, train, val, _ = m.preparar(df_stocks)
    v = _pred[_pred['conjunto'] == 'Validación']
    grilla_rf = m.grilla(v['retorno_esperado'].to_numpy(), v['confianza'].to_numpy(),
                         v['open_adj_lead'].to_numpy(), v['retorno_operable'].to_numpy())
    esp_d, prob_d = m.dummy_validacion(train, val)
    grilla_d = m.grilla(esp_d, prob_d, val['open_adj_lead'].to_numpy(), val['retorno_operable'].to_numpy())
    curvas = pd.concat([m.por_umbral(x).assign(modelo=n) for n, x in [(m.ELEGIDO, grilla_rf), ('Dummy (media)', grilla_d)]])
    return curvas


ART, PRED = cargar_modelo()
UMBRAL = ART['umbral']
U_TXT = f'{UMBRAL:g} %'.replace('.', ',')
CURVAS = calibracion(PRED)
RF = CURVAS[CURVAS['modelo'] == m.ELEGIDO]
TOP10 = RF[RF['valido']].nlargest(10, 'retorno', keep='first')
EN_UMBRAL = CURVAS[CURVAS['umbral (%)'] == UMBRAL].set_index('modelo')
MEDIA_TRAIN = m.preparar(df_stocks)[1][m.OBJETIVO].mean()

html(f"""
<div id="modelo" class="seccion"></div>
<p class="etapa tallo">El modelo</p>
<h2>Qué buscamos predecir: la columna objetivo</h2>
<p>La columna objetivo fue <code>retorno_lead3</code>: representa, en porcentaje, cuánto cambió la acción desde el cierre
anterior al anuncio hasta el cierre del tercer día posterior. Es el valor que intentamos predecir.</p>
<h2>Primero elegimos el modelo que menos se equivoca: un Random Forest</h2>
<p>Probamos cuatro modelos que, a partir del balance (la sorpresa, los márgenes, el flujo de caja, la deuda, el sector),
predicen cuánto se va a mover la acción en tres días. Para compararlos usamos el <b>MAE</b>: cuántos puntos se equivoca
en promedio. Un MAE de 5 quiere decir que si la acción subió 2 %, el modelo pudo haber dicho algo entre −3 % y +7 %.</p>
<p>Para saber si un modelo aprendió algo hay que compararlo con un punto de partida. Ese es el <b>dummy</b>: un
«modelo» que no mira nada del balance y para todas las empresas predice lo mismo, el retorno promedio del entrenamiento
({num(MEDIA_TRAIN)} %). Un modelo que no le gana al dummy no sirve.</p>
""")
grafico(g.grafico_mae())
html("""
<p class="nota"><b>Qué mirar:</b> los cuatro modelos le ganan al dummy (la línea punteada), y el Random Forest es el que
menos se equivoca. Pero la mejora es chica: baja de 5,38 a 5,15 puntos. A partir de acá seguimos solo con el Random
Forest, y lo comparamos siempre contra el dummy.</p>
<h3 class="sub">Solo, el modelo no es muy bueno</h3>
<p>El <b>R²</b> mide qué parte del movimiento de la acción explica el modelo: 1 sería predecir todo perfecto y 0 es lo
mismo que el dummy. Lo medimos para los mismos modelos que comparamos con el MAE.</p>
""")
grafico(g.grafico_r2())
html(f"""
<p class="nota"><b>Qué mirar:</b> todas las barras quedan cerca del piso. El orden es el mismo que con el MAE y el
Random Forest sigue siendo el mejor, pero explica apenas el 9 % de cómo se mueve la acción: la mayor parte de lo que
pasa después de un balance no se puede anticipar con estos datos. Si compráramos todas las acciones que el modelo espera que suban (umbral 0 %), ganaríamos en promedio
{num(CURVAS.query("modelo == @m.ELEGIDO and `umbral (%)` == 0")['retorno'].iloc[0])} % del presupuesto en validación. Para
ganar más hay que calibrar <b>cuándo</b> comprar.</p>

<h3 class="sub">Después calibramos cuándo comprar: el umbral</h3>
<p>El modelo no compra cualquier acción que espera que suba: compra solo si espera que suba <b>más que un umbral</b>, y
además tiene que estar más de 50 % seguro de que va a subir. Esa seguridad (la confianza) sale de comparar, en años
anteriores, lo que el modelo esperaba con lo que pasó. El presupuesto se reparte entre las acciones que pasan el umbral,
más plata a las de mayor confianza.</p>
<p>Para elegir el umbral probamos 90 umbrales (de 0 % a 44,5 %), cada uno con 28 presupuestos (de 100 a 10.000 USD),
con los balances del primer semestre de 2026, que el modelo no usó para aprender. Cada umbral es una regla de compra, y la
medimos por su retorno medio sobre el capital: cuánto gana, en promedio de los 28 presupuestos, por cada 100 USD
invertidos. Solo cuentan las reglas que compran al menos 3 acciones, para que el resultado no dependa de una sola.</p>
""")
grafico(g.grafico_umbral_top(TOP10, UMBRAL))
html(f"""
<p class="nota"><b>Qué mirar:</b> los mejores umbrales están todos entre 16 % y 21 %: el modelo gana más cuando
compra pocas acciones, las que espera que suban mucho. Varios empatan en {num(TOP10['retorno'].max())} % porque
terminan comprando las mismas acciones; nos quedamos con el más bajo, {U_TXT}.</p>
""")
grafico(g.grafico_umbral_curva(CURVAS, UMBRAL))
html(f"""
<p class="nota"><b>Qué mirar:</b> ahora en dólares, para todos los umbrales. Con {U_TXT}, el Random Forest gana en
promedio {num(EN_UMBRAL.loc[m.ELEGIDO, 'ganancia'])} USD y el dummy, con la misma regla,
{num(EN_UMBRAL.loc['Dummy (media)', 'ganancia'])} USD. En gris, los umbrales tan altos que el modelo compra una o dos
acciones: ahí el resultado es suerte. El modelo predice el número
exacto bastante mal, pero sirve para ordenar cuáles acciones conviene comprar.</p>
""")
with st.expander('Cómo lo sabemos'):
    html(f"""
    <h4>La comparación completa por MAE</h4>
    <p>Los modelos se comparan con validación cruzada temporal sobre el entrenamiento: cada pedazo entrena con los años
    anteriores y valida en el siguiente (2021 a 2025).</p>
    {c.T_MAE}
    <h4>Cómo funciona el dummy</h4>
    <p>Predice siempre el retorno medio del entrenamiento, así que su R² es prácticamente 0. Con la regla de compra, lo
    único que cambia de una acción a otra es cuánto abrió por debajo o por encima del cierre previo: si abrió muy abajo,
    «espera» que vuelva a la media y la compra. Tiene su propia confianza, calibrada igual que la del modelo. Con el
    umbral de {U_TXT}, gana en el 36 % de los presupuestos, con resultados entre −4,02 % y +1,96 %.</p>
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
ss = st.session_state
ss.setdefault('umbral', float(UMBRAL))


def slider_umbral(key):
    """El mismo umbral en «Probá» y «Simulá»: se puede mover en cualquiera de los dos y el otro lo sigue."""
    ss[key] = ss['umbral']
    st.slider('Umbral de compra (%)', 0.0, 44.5, step=0.5, key=key, on_change=lambda: ss.update(umbral=ss[key]),
              help=f'El modelo compra si espera que la acción suba más que esto. El elegido en validación es {U_TXT}.')


# ---------- 1. Explorá ----------
# Nombre y logo de cada empresa (los arma empresas.py). Si falta el archivo, se muestra solo el ticker.
try:
    EMPRESAS = pd.read_csv(AQUI / 'empresas.csv').set_index('ticker')
except FileNotFoundError:
    EMPRESAS = pd.DataFrame(columns=['nombre', 'logo'])


def nombre(ticker):
    return EMPRESAS['nombre'].get(ticker, ticker)


def logo(ticker):
    return EMPRESAS['logo'].get(ticker)


@st.cache_data(show_spinner=False)
def datos_explora():
    t = m.preparar(df_stocks)[3].reset_index(drop=True)       # 2026Q3
    t['id'] = t.index
    t['fecha'] = t['reported_date'].dt.strftime('%d/%m/%Y')
    t['signo'] = np.where(t['surprise_pct'] < 0, 'Sorpresa negativa', 'Sorpresa positiva')
    t['sector'] = t['sector'].fillna('Sin sector')
    t['nombre'] = t['ticker'].map(nombre)
    return t[['id', 'ticker', 'nombre', 'fecha', 'sector', 'industry', 'report_time', 'reported_eps', 'consensus_eps', 'surprise_pct',
              'close_adj_lag1', 'open_adj_lead', 'close_adj_lead3', m.OBJETIVO, 'signo']]


EXPLORA = datos_explora()

html("""
<div id="explora" class="seccion"></div>
<p class="etapa copa">Tu turno · Explorá</p>
<h2>Cada balance del último trimestre: cuánto sorprendió y qué hizo la acción</h2>
<p>Cada punto es una empresa que presentó su balance entre julio y septiembre de 2026. Hacia la derecha, la que más
superó lo esperado; hacia arriba, la que más subió en los tres días siguientes. Acá no hay modelo: son los datos tal cual.
Hacé clic en un punto para ver su balance al costado, y elegí un sector con el control de abajo del gráfico.</p>
""")
izq, der = st.columns([2.3, 1], gap='medium')
with izq:
    ev = st.altair_chart(g.estilo(g.grafico_explora(EXPLORA)), width='content', theme=None,
                         on_select='rerun', selection_mode='punto', key='explora')
with der:
    elegidos = ev.selection.get('punto') or []
    if not elegidos:
        st.info('Hacé clic en un punto del gráfico para ver los datos de ese balance.')
    else:
        b = EXPLORA.loc[elegidos[0]['id']]
        html(f"""
        <div class="panel">
        <div class="panel-cab">{f'<img src="{logo(b["ticker"])}" alt="">' if logo(b['ticker']) else ''}
        <div><p class="panel-tit">{b['ticker']}</p><p class="panel-nombre">{escape(b['nombre'])}</p></div></div>
        <p class="panel-sub">{b['sector']} · {b['industry']}<br>Balance del {b['fecha']} ({b['report_time']})</p>
        <dl>
        <dt>Ganancia por acción esperada</dt><dd>{num(b['consensus_eps'])} USD</dd>
        <dt>Ganancia por acción real</dt><dd>{num(b['reported_eps'])} USD</dd>
        <dt>Sorpresa</dt><dd class="{'gana' if b['surprise_pct'] > 0 else 'pierde'}">{num(b['surprise_pct'], 1)} %</dd>
        <dt>Cierre antes del anuncio</dt><dd>{num(b['close_adj_lag1'])} USD</dd>
        <dt>Apertura después del anuncio</dt><dd>{num(b['open_adj_lead'])} USD</dd>
        <dt>Cierre del 3.er día</dt><dd>{num(b['close_adj_lead3'])} USD</dd>
        <dt>Retorno a 3 días</dt><dd class="{'gana' if b[m.OBJETIVO] > 0 else 'pierde'}">{num(b[m.OBJETIVO])} %</dd>
        </dl></div>
        """)


# ---------- 2. Probá el modelo ----------
html(f"""
<div id="proba" class="seccion"></div>
<p class="etapa copa">Tu turno · Probá el modelo</p>
<h2>Elegí una empresa, cambiale la sorpresa y mirá si el modelo compraría</h2>
<p>Partimos del último balance real de la empresa. Además de la sorpresa, podés cambiar sus cinco atributos más importantes
para el modelo: flujo operativo, dividendos, efectivo, retorno sobre activos y liquidez corriente. El modelo predice cuánto se
mueve la acción desde el cierre previo al anuncio y, con el precio al que abrió ese día, calcula cuánto espera que suba
desde la apertura, que es cuando se puede comprar. Compra si eso supera el umbral y si está más de 50 % seguro de que sube.</p>
<p class="nota">El modelo casi nunca espera que una acción suba más de 9 % desde el cierre previo. Las compras con
umbrales altos pasan cuando la acción abre muy por debajo de lo que el modelo cree que va a valer: ahí la ve barata.</p>
""")

EJEMPLOS = df_stocks.dropna(subset=['reported_eps', 'consensus_eps', 'close_adj_lag1', 'open_adj_lead']).copy()
EJEMPLOS = EJEMPLOS[(EJEMPLOS['reported_date'] >= '2025-01-01') & (EJEMPLOS['consensus_eps'] != 0)
                    & (EJEMPLOS['close_adj_lag1'] > 0) & (EJEMPLOS['open_adj_lead'] > 0)]
EJEMPLOS = EJEMPLOS.sort_values(['ticker', 'reported_date']).drop_duplicates('ticker', keep='last').set_index('ticker')
EJEMPLOS['report_time'] = EJEMPLOS['report_time'].fillna('desconocido')
SORPRESAS = np.arange(-50, 51, 1.0)


def sorpresa_real():
    ss['p_sorpresa'] = float(np.clip(round(EJEMPLOS.loc[ss['p_ticker'], 'surprise_pct']), -50, 50))


if 'p_ticker' not in ss:
    ss['p_ticker'] = 'NVDA' if 'NVDA' in EJEMPLOS.index else EJEMPLOS.index[0]
    sorpresa_real()

a, b = st.columns(2)
a.selectbox('Empresa (su último balance)', EJEMPLOS.index.tolist(), key='p_ticker', on_change=sorpresa_real,
            format_func=lambda t: f'{t} · {nombre(t)}')
with b:
    slider_umbral('u_proba')
st.slider('Sorpresa (%)', -50.0, 50.0, step=1.0, key='p_sorpresa',
          help='Cuánto más (o menos) ganó la empresa respecto de lo que esperaban los analistas.')

fila = EJEMPLOS.loc[ss['p_ticker']]
casos = pd.DataFrame([fila[m.COLUMNAS_CRUDAS]] * len(SORPRESAS)).reset_index(drop=True)
casos['surprise_pct'] = SORPRESAS
casos['surprise'] = SORPRESAS / 100 * abs(fila['consensus_eps'])
# Cinco atributos con mayor importancia, excluidas las dos variables de sorpresa que ya se ajustan arriba.
# Los deslizadores editan los ratios usados por el modelo y se traducen a sus columnas contables de entrada.
ATRIBUTOS = [
    ('flujo_op_sobre_activos', 'Flujo operativo / activos', 'operating_cashflow', 'total_assets'),
    ('dividendos_sobre_activos', 'Dividendos / activos', 'dividend_payout', 'total_assets'),
    ('cash_sobre_activos', 'Efectivo / activos', 'cash_and_equivalents', 'total_assets'),
    ('roa', 'Retorno sobre activos (ROA)', 'net_income', 'total_assets'),
    ('liquidez_corriente', 'Liquidez corriente', 'total_current_assets', 'total_current_liabilities'),
]
ratios = m.Ratios().transform(pd.DataFrame([fila[m.COLUMNAS_CRUDAS]]))
ratios_entrenamiento = m.Ratios().transform(m.preparar(df_stocks)[1][m.COLUMNAS_CRUDAS])
st.caption('Ajustá estos valores para ver cómo cambia la predicción. Los rangos corresponden a los balances de entrenamiento.')
cols_atributos = st.columns(2)
for i, (columna, etiqueta, numerador, denominador) in enumerate(ATRIBUTOS):
    serie = ratios_entrenamiento[columna].dropna()
    bajo, alto = np.nanquantile(serie, [0.01, 0.99])
    if columna == 'liquidez_corriente':
        bajo, alto = max(0.0, bajo), max(0.0, alto)
    if not np.isfinite(bajo) or not np.isfinite(alto) or bajo >= alto:
        bajo, alto = -1.0, 1.0
    valor = ratios[columna].iloc[0]
    valor = float(np.clip(valor if np.isfinite(valor) else serie.median(), bajo, alto))
    paso = max((alto - bajo) / 100, 0.001)
    elegido = cols_atributos[i % len(cols_atributos)].slider(
        etiqueta, float(bajo), float(alto), value=valor, step=float(paso), format='%.3f',
        key=f'p_atributo_{ss["p_ticker"]}_{columna}')
    casos[numerador] = elegido * fila[denominador]
pred = ART['pipe'].predict(casos[m.COLUMNAS_CRUDAS])
curva = pd.DataFrame({'sorpresa': SORPRESAS, 'prediccion': pred,
                      'esperado': (fila['close_adj_lag1'] * (1 + pred / 100) / fila['open_adj_lead'] - 1) * 100})
curva['confianza'] = m.prob_subida(ART['calibrador'], curva['esperado'])
yo = curva[curva['sorpresa'] == ss['p_sorpresa']]
compra = bool((yo['esperado'] > ss['umbral']).iloc[0] and (yo['confianza'] > .5).iloc[0])

k = st.columns(4)
k[0].metric('Predice (desde el cierre)', f"{num(yo['prediccion'].iloc[0])} %")
k[1].metric('Espera (desde la apertura)', f"{num(yo['esperado'].iloc[0])} %",
            help=f"Ese día abrió a {num(fila['open_adj_lead'])} USD, después de cerrar a {num(fila['close_adj_lag1'])} USD.")
k[2].metric('Confianza', f"{num(yo['confianza'].iloc[0] * 100, 1)} %")
k[3].metric('¿Compra?', 'Sí' if compra else 'No')
grafico(g.grafico_proba(curva, yo, ss['umbral']))


# ---------- 3. Simulá una inversión ----------
html("""
<div id="simula" class="seccion"></div>
<p class="etapa copa">Tu turno · Simulá una inversión</p>
<h2>Elegí un presupuesto y un umbral, y mirá cuánto habrías ganado en el último trimestre</h2>
<p>Con los balances de julio a septiembre de 2026, que el modelo no vio. El modelo compra las acciones que espera que
suban desde la apertura más que el umbral, reparte el presupuesto según su confianza, compra acciones enteras en la
apertura y vende al cierre del 3.er día. El umbral es el mismo de «Probá el modelo»: si lo movés acá, cambia allá.</p>
""")

T1, T2 = ART['referencia']['terciles_activos']
PRED['tamano'] = pd.cut(PRED['total_assets'], [-np.inf, T1, T2, np.inf], labels=['Chicas', 'Medianas', 'Grandes']).astype(str)
Q3 = PRED['conjunto'] == 'Test'   # 2026Q3

a, b = st.columns(2)
presupuesto = a.select_slider('Presupuesto (USD)', options=m.PRESUPUESTOS, value=1000)
with b:
    slider_umbral('u_simula')
a, b = st.columns(2)
todos_sect = sorted(PRED.loc[Q3, 'sector'].dropna().unique())
sectores = a.multiselect('Sectores', todos_sect, default=todos_sect, placeholder='Elegí al menos uno')
tamanos = b.multiselect('Tamaño de empresa (por activos totales)', ['Chicas', 'Medianas', 'Grandes'],
                        default=['Chicas', 'Medianas', 'Grandes'], placeholder='Elegí al menos uno',
                        help='Tercios de los activos totales del entrenamiento, como en la Entrega 3.')


def simular():
    d = PRED[Q3 & PRED['sector'].isin(sectores) & PRED['tamano'].isin(tamanos)].reset_index(drop=True)
    if d.empty:
        st.info('No hay balances con esos filtros.')
        return
    precio, real = d['open_adj_lead'].to_numpy(), d['retorno_operable'].to_numpy()
    mod = m.simular_presupuesto(m.peso_modelo(d['retorno_esperado'], d['confianza'], ss['umbral']), precio, presupuesto)
    r_mod = m.resultado(mod, real, presupuesto)

    k = st.columns(3)
    k[0].metric('Balances en el universo', num(len(d), 0))
    k[1].metric('Compras del modelo', r_mod['compras'])
    k[2].metric('Ganancia del modelo', f'{num(r_mod["ganancia (USD)"])} USD', delta(r_mod["retorno s/ presupuesto (%)"]))

    c = mod > 0
    if not c.any():
        st.info(f'En este universo ningún balance supera el umbral de {num(ss["umbral"], 1)} % con confianza mayor a 50 %: '
                'el modelo no compra nada y el presupuesto queda sin usar. Probá con un umbral más bajo o más sectores.')
        return
    compras = d.loc[c, ['ticker', 'reported_date', 'sector', 'open_adj_lead', 'retorno_operable', 'retorno_esperado', 'confianza']].copy()
    compras['pago'] = mod[c]
    compras['acciones'] = np.round(mod[c] / precio[c]).astype(int)
    compras['ganancia'] = mod[c] * real[c] / 100
    compras['fecha'] = compras['reported_date'].dt.strftime('%d/%m/%Y')
    compras['confianza_pct'] = compras['confianza'] * 100
    st.altair_chart(g.estilo(g.grafico_simula_compras(compras)), width='content', theme=None)
    compras['logo'], compras['nombre'] = compras['ticker'].map(logo), compras['ticker'].map(nombre)
    tabla = compras.sort_values('ganancia', ascending=False)[
        ['logo', 'ticker', 'nombre', 'fecha', 'sector', 'acciones', 'open_adj_lead', 'pago', 'ganancia', 'retorno_operable',
         'retorno_esperado', 'confianza_pct']]
    tabla.columns = ['Logo', 'Ticker', 'Empresa', 'Fecha del balance', 'Sector', 'Acciones', 'Precio de compra (USD)',
                     'Pagó (USD)', 'Ganancia (USD)', 'Retorno real (%)', 'Retorno esperado (%)', 'Confianza (%)']
    config = {c: st.column_config.NumberColumn(format='%.2f') for c in tabla.columns[6:]}
    config['Logo'] = st.column_config.ImageColumn('', width='small')
    st.dataframe(tabla, hide_index=True, column_config=config)


simular()

html("""<footer>Ciencia de Datos · UTN FRM · 2026 · Datos: Yahoo Finance y SEC EDGAR, captura del 26/10/2026.</footer>""")

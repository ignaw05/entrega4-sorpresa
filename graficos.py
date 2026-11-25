"""Gráficos de la aplicación, con el mismo código de Altair que la Entrega 4."""
import numpy as np
import pandas as pd
import altair as alt

ELEGIDO = 'Random Forest'
COLOR = {'Dummy (media)': '#9E9E9E', 'Regresión lineal': '#3D5A80', 'Árbol de decisión': '#E9C46A',
         'Random Forest': '#2A9D8F', 'Gradient Boosting': '#E07A5F', 'Comprar todo': '#6D597A',
         'No invertir': '#CFCFCF', 'Oráculo': '#264653'}

# Estilo común (tipografía y ejes) para que todos los gráficos se vean igual en la página
ESTILO = dict(
    axis=dict(domainColor='#d6d1c5', gridColor='#efebe3', labelColor='#5b6170', labelFontSize=12,
              tickColor='#d6d1c5', titleColor='#5b6170', titleFontSize=12.5, titleFontWeight=500, titlePadding=10,
              labelFont='Inter, Helvetica, Arial, sans-serif', titleFont='Inter, Helvetica, Arial, sans-serif'),
    title=dict(font='Fraunces, Georgia, serif', fontSize=19, fontWeight=600, color='#14213d', subtitleFontSize=12.5,
               subtitleColor='#5b6170', subtitleFont='Inter, Helvetica, Arial, sans-serif', subtitlePadding=6,
               offset=16, anchor='start'),
    legend=dict(labelColor='#14213d', labelFontSize=12.5, titleColor='#5b6170', titleFontSize=12.5,
                symbolType='circle', symbolSize=110),
    font='Inter, Helvetica, Arial, sans-serif', background='#ffffff', padding=8,
)


def estilo(chart):
    chart = chart.properties(autosize=alt.AutoSizeParams(type='pad', contains='padding'))
    return (chart.configure(font=ESTILO['font'], background=ESTILO['background'], padding=ESTILO['padding'])
                 .configure_axis(**ESTILO['axis']).configure_title(**ESTILO['title'])
                 .configure_legend(**ESTILO['legend']).configure_view(stroke=None)
                 .configure_bar(cornerRadiusEnd=3))


def fmt(v):   # -2,9 % · 14 % (coma decimal, sin decimales si es grande)
    t = f'{v:+.0f}' if abs(v) >= 10 else f'{v:+.1f}'
    return t.replace('-', '−').replace('.', ',') + ' %'


SIGNO = alt.Scale(domain=['Sorpresa negativa', 'Sorpresa positiva'], range=['#E07A5F', '#3D5A80'])
RET_Y = [-20, 20]   # mismo eje de «retorno a 3 días» en todos los gráficos que lo muestran, para poder compararlos
MAGNITUDES = ['menor', 'media-baja', 'media-alta', 'mayor']


def _num(v):
    return f'{v:,.1f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def con_grupos(df_stocks):
    """Los balances con sorpresa distinta de cero, con su retorno y los 4 grupos de tamaño de «Lo que encontramos»
    (valor absoluto de la sorpresa, con la misma cantidad de anuncios)."""
    h = df_stocks.replace([np.inf, -np.inf], np.nan).copy()
    previo = h['close_adj_lag1'].where(h['close_adj_lag1'] > 0)
    h['retorno_apertura'] = (h['open_adj_lead'] / previo - 1) * 100
    h['retorno_3d'] = (h['close_adj_lead3'] / previo - 1) * 100
    h = h.dropna(subset=['surprise', 'surprise_pct', 'retorno_apertura'])
    h = h[h['surprise_pct'] != 0].copy()
    h['tipo'] = np.where(h['surprise'] < 0, 'Sorpresa negativa', 'Sorpresa positiva')
    h['grupo'] = pd.qcut(h['surprise_pct'].abs(), 4, labels=False) + 1        # 1 = menor magnitud, 4 = mayor
    rango = h.groupby('grupo')['surprise_pct'].agg(lambda s: f'{_num(s.abs().min())} % a {_num(s.abs().max())} %')
    rango[4] = f"más de {_num(h.loc[h['grupo'] == 4, 'surprise_pct'].abs().min())} %"
    h['magnitud'] = h['grupo'].map(lambda g: MAGNITUDES[g - 1]) + ' · ' + h['grupo'].map(rango)
    return h


# ---------- 1. Los datos: retorno a 3 días según el cuartil de la sorpresa ----------
def grafico_datos(df_stocks):
    d = con_grupos(df_stocks).dropna(subset=['retorno_3d'])
    d['cuartil'] = pd.qcut(d['surprise_pct'], 4, labels=False) + 1          # 1 = sorpresas más negativas
    lim = d.groupby('cuartil')['surprise_pct'].agg(['min', 'max'])
    rangos = {1: f"menos de {_num(lim.loc[1, 'max'])} %", 4: f"más de {_num(lim.loc[4, 'min'])} %",
              **{q: f"{_num(lim.loc[q, 'min'])} % a {_num(lim.loc[q, 'max'])} %" for q in (2, 3)}}
    d['columna'] = d['cuartil'].map(lambda q: f'Cuartil {q} · {rangos[q]}')
    resumen = d.groupby(['cuartil', 'columna']).agg(
        balances=('retorno_3d', 'size'),
        p10=('retorno_3d', lambda s: s.quantile(.10)), p25=('retorno_3d', lambda s: s.quantile(.25)),
        mediana=('retorno_3d', 'median'),
        p75=('retorno_3d', lambda s: s.quantile(.75)), p90=('retorno_3d', lambda s: s.quantile(.90)),
        pct_sube=('retorno_3d', lambda s: (s > 0).mean() * 100),
    ).reset_index()
    resumen['etiqueta'] = resumen['mediana'].map(fmt)
    tip = [alt.Tooltip('columna:N', title='Sorpresa'), alt.Tooltip('balances:Q', title='Balances', format=','),
           alt.Tooltip('mediana:Q', title='Retorno mediano (%)', format='+.2f'),
           alt.Tooltip('p25:Q', title='25 % rinde menos de (%)', format='+.2f'),
           alt.Tooltip('p75:Q', title='25 % rinde más de (%)', format='+.2f'),
           alt.Tooltip('pct_sube:Q', title='Subieron (%)', format='.0f')]

    ALTO = 380
    hover = alt.selection_point(name='hover', fields=['cuartil'], on='pointerover', clear='pointerout', nearest=False)
    opac = alt.condition(hover, alt.value(1), alt.value(.55))
    y_esc = alt.Scale(domain=RET_Y, clamp=True)
    base = alt.Chart(resumen).encode(
        x=alt.X('columna:N', sort=alt.EncodingSortField('cuartil'),
                title='Sorpresa del balance, en cuartiles: de la más negativa a la más positiva',
                axis=alt.Axis(labelAngle=0, labelExpr="split(datum.label, ' · ')")))
    zona = base.mark_bar(size=120, opacity=0).encode(y=alt.value(0), y2=alt.value(ALTO), tooltip=tip).add_params(hover)
    rango = base.mark_rule(strokeWidth=2, color='#8D99AE').encode(
        y=alt.Y('p10:Q', title='Retorno a 3 días (%)', scale=y_esc), y2='p90:Q', opacity=opac)
    caja = base.mark_bar(size=46, color='#3D5A80').encode(y=alt.Y('p25:Q', scale=y_esc), y2='p75:Q', opacity=opac)
    mediana = base.mark_tick(size=60, thickness=3, color='#E07A5F').encode(y=alt.Y('mediana:Q', scale=y_esc), opacity=opac)
    numeros = base.mark_text(dx=36, align='left', fontSize=13, fontWeight='bold').encode(y=alt.Y('mediana:Q', scale=y_esc), text='etiqueta:N')
    cero = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(color='black', strokeDash=[4, 3]).encode(y=alt.Y('y:Q', scale=y_esc))

    return (zona + cero + rango + caja + mediana + numeros).properties(
        width=680, height=ALTO,
        title=alt.TitleParams('Cuanto peor la sorpresa, peor le va a la acción en los 3 días siguientes',
                              subtitle=[f'{len(d):,}'.replace(',', '.') + ' balances en 4 cuartiles de sorpresa, cada uno con la misma cantidad de balances.',
                                        'Raya: de 10 % a 90 % de los balances · caja: 25 % a 75 % · marca naranja y número: el retorno típico (mediana).']))


# ---------- 2. Lo que encontramos: caída fuerte por signo de la sorpresa ----------
def grafico_hallazgo(df_stocks):
    h = con_grupos(df_stocks)
    h['caida_fuerte'] = h['retorno_apertura'] <= -1.98                         # primer cuartil del retorno
    resumen = h.groupby(['grupo', 'magnitud', 'tipo'])['caida_fuerte'].agg(anuncios='size', riesgo='mean').reset_index()
    resumen['riesgo_pct'] = resumen['riesgo'] * 100
    orden = resumen.sort_values('grupo')['magnitud'].unique().tolist()

    base = alt.Chart(resumen).encode(
        x=alt.X('magnitud:N', sort=orden, title='Tamaño de la sorpresa (sin importar el signo), de menor a mayor',
                axis=alt.Axis(labelAngle=0, labelExpr="split(datum.label, ' · ')")),
        xOffset=alt.XOffset('tipo:N'),
        y=alt.Y('riesgo_pct:Q', title='Anuncios con caída fuerte (%)', scale=alt.Scale(domain=[0, 60])),
        color=alt.Color('tipo:N', scale=SIGNO, title=None, legend=alt.Legend(orient='top')))
    barras = base.mark_bar().encode(tooltip=[
        alt.Tooltip('tipo:N', title='Signo'), alt.Tooltip('magnitud:N', title='Magnitud'),
        alt.Tooltip('anuncios:Q', title='Anuncios', format=','),
        alt.Tooltip('riesgo_pct:Q', title='Caída fuerte (%)', format='.1f')])
    numeros = base.mark_text(dy=-8, fontSize=12).encode(text=alt.Text('riesgo_pct:Q', format='.0f'), color=alt.value('black'))

    return (barras + numeros).properties(
        width=640, height=340,
        title=alt.TitleParams('A igual tamaño de sorpresa, las negativas caen fuerte mucho más seguido',
                              subtitle='Caída fuerte: −1,98 % o menos entre el cierre previo y la primera apertura. 4 grupos con la misma cantidad de anuncios.'))


def grafico_hora_reporte(df_stocks):
    """Hipótesis 4 de la EDA: distribución del retorno a 3 días y proporción que sube por hora del reporte."""
    d = df_stocks.dropna(subset=['report_time', 'close_adj_lag1', 'close_adj_lead3']).copy()
    d = d[d['report_time'].isin(['pre-market', 'post-market'])]
    d = d[d['close_adj_lag1'] > 0].copy()
    d['retorno_3r'] = (d['close_adj_lead3'] / d['close_adj_lag1'] - 1) * 100
    orden = ['pre-market', 'post-market']
    colores = alt.Scale(domain=orden, range=['#0f6e74', '#E07A5F'])

    cajas = (alt.Chart(d).mark_boxplot(size=52, extent=1.5, outliers={'size': 14, 'opacity': 0.35})
             .encode(x=alt.X('report_time:N', sort=orden, title='Hora del reporte'),
                     y=alt.Y('retorno_3r:Q', title='Retorno a 3 días (%)'),
                     color=alt.Color('report_time:N', scale=colores, legend=None),
                     tooltip=[alt.Tooltip('report_time:N', title='Hora'),
                              alt.Tooltip('retorno_3r:Q', title='Retorno (%)', format='.2f')])
             .properties(width=300, height=280,
                         title=alt.TitleParams('Retorno a 3 días', subtitle=f'{len(d):,} balances con hora informada'.replace(',', '.'))))

    sube = (d.assign(sube=(d['retorno_3r'] > 0).astype(float) * 100)
            .groupby('report_time', as_index=False).agg(pct_sube=('sube', 'mean'), balances=('sube', 'size')))
    base = alt.Chart(sube).encode(x=alt.X('report_time:N', sort=orden, title='Hora del reporte'))
    barras = base.mark_bar(size=52).encode(
        y=alt.Y('pct_sube:Q', title='Reportes en que la acción sube (%)', scale=alt.Scale(domain=[0, 100])),
        color=alt.Color('report_time:N', scale=colores, legend=None),
        tooltip=[alt.Tooltip('report_time:N', title='Hora'),
                 alt.Tooltip('balances:Q', title='Balances', format=','),
                 alt.Tooltip('pct_sube:Q', title='Sube (%)', format='.1f')])
    linea = alt.Chart(pd.DataFrame({'y': [50]})).mark_rule(strokeDash=[5, 4], color='#777').encode(y='y:Q')
    etiquetas = base.mark_text(dy=-8, fontSize=12, color='#14213d').encode(
        y='pct_sube:Q', text=alt.Text('pct_sube:Q', format='.0f'))
    porcentaje = (barras + linea + etiquetas).properties(width=300, height=280,
        title=alt.TitleParams('% de reportes en que sube', subtitle='Línea punteada: 50 %'))

    return alt.hconcat(cajas, porcentaje, spacing=24).properties(
        title=alt.TitleParams('La hora del reporte y la reacción de la acción',
                              subtitle='Hipótesis 4 de la EDA: retornos con signo y porcentaje de subas a 3 días.'))


# ---------- 3b. El modelo: MAE contra el piso (Entrega 4, celda 11) ----------
# MAE de la Entrega 3: validación cruzada temporal en train (media ± desvío entre folds) y test (sólo piso y modelo final)
MAE = pd.DataFrame([
    ('Random Forest',     5.149, 0.515, 5.829),
    ('Gradient Boosting', 5.174, 0.509, np.nan),
    ('Árbol de decisión', 5.215, 0.523, np.nan),
    ('Regresión lineal',  5.256, 0.572, np.nan),
    ('Dummy (media)',     5.375, 0.529, 6.013),
], columns=['modelo', 'mae_cv', 'desvio', 'mae_test'])


def grafico_mae():
    mae = MAE.copy()
    PISO_CV = mae.loc[mae['modelo'] == 'Dummy (media)', 'mae_cv'].iloc[0]
    mae['mejora'] = (1 - mae['mae_cv'] / PISO_CV) * 100
    mae['etiqueta'] = mae['mae_cv'].map(lambda v: f'{v:.2f}'.replace('.', ','))
    orden = mae['modelo'].tolist()                                      # ya está de menor a mayor MAE

    hover = alt.selection_point(name='hover', fields=['modelo'], on='pointerover', clear='pointerout')
    opac = alt.condition(hover, alt.value(1), alt.value(.55))
    colores = alt.Scale(domain=list(COLOR), range=list(COLOR.values()))
    tip = [alt.Tooltip('modelo:N', title='Modelo'),
           alt.Tooltip('mae_cv:Q', title='MAE validación cruzada (pp)', format='.3f'),
           alt.Tooltip('desvio:Q', title='± desvío entre folds (pp)', format='.3f'),
           alt.Tooltip('mejora:Q', title='Mejora vs piso (%)', format='+.1f'),
           alt.Tooltip('mae_test:Q', title='MAE test (pp)', format='.3f')]

    y = alt.Y('modelo:N', sort=orden, title=None)
    x_esc = alt.Scale(domain=[5.0, 6.2])   # no empieza en 0: se aclara junto al nombre del eje
    base = alt.Chart(mae).encode(y=y)
    punto = base.mark_circle(size=170, stroke='black', strokeWidth=1.2).encode(
        x=alt.X('mae_cv:Q', scale=x_esc, title='MAE (pp del retorno a 3 días; el eje empieza en 5)'),
        color=alt.Color('modelo:N', scale=colores, legend=None), opacity=opac, tooltip=tip).add_params(hover)
    numeros = base.mark_text(dy=-16, fontSize=12).encode(x='mae_cv:Q', text='etiqueta:N')
    test = (alt.Chart(mae.dropna(subset=['mae_test'])).mark_point(shape='diamond', size=130, filled=True, color='black')
            .encode(y=y, x=alt.X('mae_test:Q', scale=x_esc),
                    tooltip=[alt.Tooltip('modelo:N', title='Modelo'), alt.Tooltip('mae_test:Q', title='MAE test 2026Q3 (pp)', format='.3f')]))
    piso = (alt.Chart(pd.DataFrame({'x': [PISO_CV]})).mark_rule(strokeDash=[5, 4], color='#6D6D6D')
            .encode(x=alt.X('x:Q', scale=x_esc)))

    return (piso + punto + numeros + test).properties(
        width=640, height=300,
        title=alt.TitleParams('Random Forest es el que menos se equivoca: 5,15 pp contra 5,38 del dummy',
                              subtitle=['Círculo: MAE en validación cruzada temporal. Rombo negro: MAE en test (2026Q3),',
                                        'solo para el modelo final y el piso. Línea punteada: piso (predecir siempre la media).']))


# ---------- 3c. El modelo: R² del Random Forest, predicho contra real ----------
def grafico_r2(pred, r2):
    d = pred.loc[pred['conjunto'] == 'Test', ['ticker', 'reported_date', 'prediccion', 'retorno_lead3']]
    esc = alt.Scale(domain=RET_Y, clamp=True)
    puntos = alt.Chart(d).mark_circle(size=32, opacity=0.55, color=COLOR[ELEGIDO]).encode(
        x=alt.X('prediccion:Q', title='Retorno que predice el modelo (%)', scale=esc),
        y=alt.Y('retorno_lead3:Q', title='Retorno real a 3 días (%)', scale=esc),
        tooltip=[alt.Tooltip('ticker:N', title='Empresa'), alt.Tooltip('reported_date:N', title='Balance'),
                 alt.Tooltip('prediccion:Q', title='Predicho (%)', format='.1f'),
                 alt.Tooltip('retorno_lead3:Q', title='Real (%)', format='.1f')])
    diagonal = alt.Chart(pd.DataFrame({'v': RET_Y})).mark_line(color='black', strokeDash=[5, 4]).encode(x='v:Q', y='v:Q')
    return (puntos + diagonal).properties(
        width=560, height=420,
        title=alt.TitleParams(f'El Random Forest explica apenas el {r2:.0%} del movimiento de la acción'.replace('%', ' %'),
                              subtitle=['Retorno predicho contra retorno real en cada balance de test (2026Q3).',
                                        'Línea punteada: predicción perfecta. Los retornos de más de ±20 % se muestran en el borde.']))


# ---------- 3d. El modelo: la calibración del umbral ----------
def grafico_umbral_top(top, umbral):
    t = top.copy()
    t['umbral_txt'] = t['umbral (%)'].map(lambda u: f'{u:g} %'.replace('.', ','))
    t['etiqueta'] = t['retorno'].map(lambda v: f'{v:+.2f} %'.replace('-', '−').replace('.', ','))
    t['elegido'] = np.where(t['umbral (%)'] == umbral, 'Elegido', 'Otro')
    base = alt.Chart(t).encode(x=alt.X('umbral_txt:N', sort=None, title='Umbral aplicado', axis=alt.Axis(labelAngle=0)))
    barras = base.mark_bar(size=40).encode(
        y=alt.Y('retorno:Q', title='Mayor retorno medio sobre el capital (%)', scale=alt.Scale(domainMin=0)),
        color=alt.Color('elegido:N', scale=alt.Scale(domain=['Elegido', 'Otro'], range=[COLOR[ELEGIDO], '#B8D8D3']), legend=None),
        stroke=alt.condition(alt.datum.elegido == 'Elegido', alt.value('black'), alt.value('transparent')),
        strokeWidth=alt.value(2),
        tooltip=[alt.Tooltip('umbral_txt:N', title='Umbral'), alt.Tooltip('retorno:Q', title='Retorno medio (%)', format='+.2f'),
                 alt.Tooltip('ganancia:Q', title='Ganancia neta media (USD)', format='+.2f')])
    numeros = base.mark_text(dy=-8, fontSize=12, fontWeight='bold').encode(y='retorno:Q', text='etiqueta:N')
    return (barras + numeros).properties(
        width=640, height=320,
        title=alt.TitleParams('Los 10 umbrales que más ganan con el Random Forest',
                              subtitle=['Retorno sobre el capital, promedio de los 28 presupuestos, en validación (1.er semestre de 2026).',
                                        'Solo reglas que compran al menos 3 acciones. Con borde negro, el elegido (' + f'{umbral:g}'.replace('.', ',') + ' %).']))


def grafico_umbral_curva(curvas, umbral):
    colores = alt.Scale(domain=[ELEGIDO, 'Dummy (media)'], range=[COLOR[ELEGIDO], COLOR['Dummy (media)']])
    x_esc = alt.Scale(domain=[0, 45], nice=False)
    x = alt.X('umbral (%):Q', title='Umbral de compra (%)', scale=x_esc)
    y = alt.Y('ganancia:Q', title=['Ganancia neta (USD)', 'promedio de los 28 presupuestos'])
    linea = alt.Chart(curvas).mark_line(strokeWidth=2.5).encode(
        x=x, y=y, color=alt.Color('modelo:N', scale=colores, title=None, legend=alt.Legend(orient='top')),
        tooltip=[alt.Tooltip('modelo:N', title='Modelo'), alt.Tooltip('umbral (%):Q', title='Umbral (%)'),
                 alt.Tooltip('ganancia:Q', title='Ganancia neta promedio (USD)', format='+.2f')])
    elegido = curvas[curvas['umbral (%)'] == umbral].copy()
    elegido['t'] = elegido['ganancia'].map(lambda v: f'{v:+,.0f} USD'.replace(',', '.').replace('-', '−'))
    puntos = alt.Chart(elegido).mark_point(size=110, filled=True, stroke='black').encode(x=x, y=y, color=alt.Color('modelo:N', scale=colores))
    textos = alt.Chart(elegido).mark_text(dx=10, align='left', fontSize=12, fontWeight='bold').encode(x=x, y=y, text='t:N')
    regla = alt.Chart(pd.DataFrame({'x': [umbral]})).mark_rule(color='black', strokeDash=[5, 3]).encode(x=alt.X('x:Q', scale=x_esc))
    cero = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(color='black').encode(y='y:Q')
    desde = 23.5
    suerte = alt.Chart(pd.DataFrame({'x': [desde], 'x2': [45]})).mark_rect(color='#9E9E9E', opacity=.15).encode(
        x=alt.X('x:Q', scale=x_esc), x2='x2:Q')
    suerte_t = alt.Chart(pd.DataFrame({'x': [desde], 't': ['1 o 2 compras: es suerte']})).mark_text(
        align='left', dx=6, dy=4, baseline='top', fontSize=12, color='#5b6170').encode(
            x=alt.X('x:Q', scale=x_esc), y=alt.value(0), text='t:N')
    return (suerte + suerte_t + cero + regla + linea + puntos + textos).properties(
        width=640, height=320,
        title=alt.TitleParams('Con el umbral elegido, el modelo gana y el dummy pierde',
                              subtitle=['Ganancia neta en USD, promedio de los 28 presupuestos (de 100 a 10.000 USD). Línea punteada: el umbral elegido (' + f'{umbral:g}'.replace('.', ',') + ' %).',
                                        ' En gris, umbrales tan altos que el modelo compra 1 o 2 acciones: no sirven para decidir.']))


# =====================================================================================
# Tu turno
# =====================================================================================
# ---------- 1. Explorá: sorpresa y retorno de cada balance de 2026Q3, sin modelo ----------
def grafico_explora(d):
    sectores = ['Todos'] + sorted(d['sector'].unique())
    sector = alt.param(name='sector_sel', value='Todos', bind=alt.binding_select(options=sectores, name='Sector '))
    punto = alt.selection_point(name='punto', fields=['id'], on='click')
    x = alt.X('surprise_pct:Q', title='Sorpresa del balance (%)', scale=alt.Scale(domain=[-40, 40], clamp=True))
    y = alt.Y('retorno_lead3:Q', title='Retorno a 3 días (%)', scale=alt.Scale(domain=RET_Y, clamp=True))
    puntos = (alt.Chart(d).transform_filter("sector_sel == 'Todos' || datum.sector == sector_sel")
              .mark_circle(size=70).encode(
                  x=x, y=y, color=alt.Color('signo:N', scale=SIGNO, title=None, legend=alt.Legend(orient='top')),
                  opacity=alt.condition(punto, alt.value(.85), alt.value(.2)),
                  size=alt.condition(punto, alt.value(90), alt.value(60)),
                  tooltip=[alt.Tooltip('ticker:N', title='Ticker'), alt.Tooltip('nombre:N', title='Empresa'),
                           alt.Tooltip('fecha:N', title='Fecha'),
                           alt.Tooltip('surprise_pct:Q', title='Sorpresa (%)', format='+.1f'),
                           alt.Tooltip('retorno_lead3:Q', title='Retorno a 3 días (%)', format='+.2f')])
              .add_params(sector, punto))
    cero_x = alt.Chart(pd.DataFrame({'v': [0]})).mark_rule(color='black', strokeDash=[4, 3]).encode(x='v:Q')
    cero_y = alt.Chart(pd.DataFrame({'v': [0]})).mark_rule(color='black', strokeDash=[4, 3]).encode(y='v:Q')
    return (cero_x + cero_y + puntos).properties(
        width=480, height=440,
        title=alt.TitleParams(f'Los {len(d)} balances de 2026Q3: sorpresa y retorno',
                              subtitle=['Abajo a la izquierda: sorpresa negativa y la acción cayó. Arriba a la derecha: positiva y subió.',
                                        'Hacé clic en un punto para ver su balance. Los que se salen del gráfico quedan en el borde.']))


# ---------- 2. Probá: cómo cambia lo que espera el modelo al mover solo la sorpresa ----------
def grafico_proba(curva, actual, umbral):
    x = alt.X('sorpresa:Q', title='Sorpresa (%)', scale=alt.Scale(domain=[curva['sorpresa'].min(), curva['sorpresa'].max()], nice=False))
    y = alt.Y('esperado:Q', title='Cuánto espera que suba desde la apertura (%)', scale=alt.Scale(domain=[-20, 45], clamp=True))
    zona = alt.Chart(pd.DataFrame({'y': [umbral], 'y2': [45]})).mark_rect(color='#2A9D8F', opacity=.1).encode(y='y:Q', y2='y2:Q')
    regla = alt.Chart(pd.DataFrame({'y': [umbral]})).mark_rule(color='black', strokeDash=[5, 3]).encode(y='y:Q')
    texto = alt.Chart(pd.DataFrame({'y': [umbral], 't': [f'umbral {umbral:g} %: arriba, compra'.replace('.', ',')]})).mark_text(
        align='left', dx=6, dy=-8, fontSize=12, fontWeight='bold').encode(x=alt.value(0), y='y:Q', text='t:N')
    linea = alt.Chart(curva).mark_line(strokeWidth=2.5, color=COLOR[ELEGIDO]).encode(
        x=x, y=y, tooltip=[alt.Tooltip('sorpresa:Q', title='Sorpresa (%)'), alt.Tooltip('esperado:Q', title='Espera (%)', format='+.2f')])
    yo = alt.Chart(actual).mark_point(size=200, filled=True, color='black').encode(x=x, y=y)
    return (zona + regla + linea + yo + texto).properties(
        width=600, height=320,
        title=alt.TitleParams('Lo que espera el modelo para cada sorpresa posible',
                              subtitle='Punto negro: la sorpresa que elegiste. Todo lo demás del balance queda igual.'))


def grafico_simula_compras(compras):
    c = compras.copy()
    c['resultado'] = np.where(c['ganancia'] > 0, 'Ganó', 'Perdió')
    c['etiqueta'] = c['ticker'] + ' · ' + c['fecha']
    colores = alt.Scale(domain=['Ganó', 'Perdió'], range=['#2A9D8F', '#C0392B'])   # = tablas de compras
    barras = alt.Chart(c).mark_bar().encode(
        x=alt.X('etiqueta:N', sort=alt.EncodingSortField('ganancia', order='descending'), title=None, axis=alt.Axis(labelAngle=-35)),
        y=alt.Y('ganancia:Q', title='Ganancia (USD)'),
        color=alt.Color('resultado:N', scale=colores, title=None, legend=alt.Legend(orient='top')),
        tooltip=[alt.Tooltip('ticker:N', title='Empresa'), alt.Tooltip('fecha:N', title='Fecha del balance'),
                 alt.Tooltip('sector:N', title='Sector'), alt.Tooltip('acciones:Q', title='Acciones'),
                 alt.Tooltip('pago:Q', title='Pagó (USD)', format=',.2f'), alt.Tooltip('ganancia:Q', title='Ganancia (USD)', format='+.2f'),
                 alt.Tooltip('retorno_operable:Q', title='Retorno real (%)', format='+.2f'),
                 alt.Tooltip('retorno_esperado:Q', title='Retorno esperado (%)', format='+.2f'),
                 alt.Tooltip('confianza_pct:Q', title='Confianza (%)', format='.1f')])
    cero = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(color='black').encode(y='y:Q')
    return (barras + cero).properties(width=max(260, 46 * len(c)), height=280,
                                      title=alt.TitleParams('Cada compra del modelo: cuánto ganó o perdió'))

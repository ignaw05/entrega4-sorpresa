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


# ---------- 1. Los datos: retorno a 3 días según la sorpresa (Entrega 4, celda 3) ----------
def grafico_datos(df_stocks):
    d = (df_stocks.replace([np.inf, -np.inf], np.nan)
           .dropna(subset=['surprise_pct', 'close_adj_lag1', 'close_adj_lead3']))
    d = d[d['close_adj_lag1'] > 0].copy()
    d['retorno_3d'] = (d['close_adj_lead3'] / d['close_adj_lag1'] - 1) * 100

    N_GRUPOS = 20   # 20 grupos con la misma cantidad de balances, de menor a mayor sorpresa
    d['grupo'] = pd.qcut(d['surprise_pct'], N_GRUPOS, labels=False) + 1

    resumen = d.groupby('grupo').agg(
        balances=('retorno_3d', 'size'),
        sorpresa_desde=('surprise_pct', 'min'), sorpresa_hasta=('surprise_pct', 'max'),
        sorpresa_mediana=('surprise_pct', 'median'),
        p10=('retorno_3d', lambda s: s.quantile(.10)), p25=('retorno_3d', lambda s: s.quantile(.25)),
        mediana=('retorno_3d', 'median'),
        p75=('retorno_3d', lambda s: s.quantile(.75)), p90=('retorno_3d', lambda s: s.quantile(.90)),
        pct_sube=('retorno_3d', lambda s: (s > 0).mean() * 100),
    ).reset_index()
    resumen['sorpresa_rango'] = (resumen['sorpresa_desde'].round(1).astype(str) + ' % a '
                                 + resumen['sorpresa_hasta'].round(1).astype(str) + ' %')
    resumen['etiqueta'] = resumen['sorpresa_mediana'].apply(fmt)
    tip = [alt.Tooltip('grupo:O', title='Grupo (1 = menor sorpresa)'),
           alt.Tooltip('etiqueta:N', title='Sorpresa mediana'),
           alt.Tooltip('sorpresa_rango:N', title='Sorpresa (%)'),
           alt.Tooltip('balances:Q', title='Balances'),
           alt.Tooltip('mediana:Q', title='Retorno mediano (%)', format='+.2f'),
           alt.Tooltip('p25:Q', title='25 % rinde menos de (%)', format='+.2f'),
           alt.Tooltip('p75:Q', title='25 % rinde más de (%)', format='+.2f'),
           alt.Tooltip('pct_sube:Q', title='Subieron (%)', format='.0f')]

    ALTO = 380
    hover = alt.selection_point(name='hover', fields=['grupo'], on='pointerover', clear='pointerout', nearest=False)
    opac = alt.condition(hover, alt.value(1), alt.value(.55))
    base = alt.Chart(resumen).encode(
        x=alt.X('etiqueta:N', sort=alt.EncodingSortField('grupo'),
                title='Sorpresa típica (mediana) de cada grupo: de la más negativa a la más positiva',
                axis=alt.Axis(labelAngle=-45)))
    # Zona de hover: columna completa e invisible, para no tener que apuntarle justo a la caja
    zona = base.mark_bar(size=34, opacity=0).encode(y=alt.value(0), y2=alt.value(ALTO), tooltip=tip).add_params(hover)
    rango = base.mark_rule(strokeWidth=2, color='#8D99AE').encode(
        y=alt.Y('p10:Q', title='Retorno a 3 días (%)'), y2='p90:Q', opacity=opac)
    caja = base.mark_bar(size=16, color='#3D5A80').encode(y='p25:Q', y2='p75:Q', opacity=opac)
    mediana = base.mark_tick(size=22, thickness=3, color='#E07A5F').encode(y='mediana:Q', opacity=opac)
    cero = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(color='black', strokeDash=[4, 3]).encode(y='y:Q')

    return (zona + cero + rango + caja + mediana).properties(
        width=720, height=ALTO,
        title=alt.TitleParams('Retorno a 3 días según la sorpresa del balance',
                              subtitle=[f'{len(d):,} balances en 20 grupos del mismo tamaño. Pasá el mouse por un grupo.'.replace(',', '.'),
                                        'Raya: de 10 % a 90 % de los balances · caja: 25 % a 75 % · marca naranja: mediana.']))


# ---------- 2. Lo que encontramos: caída fuerte por signo de la sorpresa (Entrega 4, celda 6) ----------
def grafico_hallazgo(df_stocks):
    h = df_stocks.replace([np.inf, -np.inf], np.nan).copy()
    h['retorno_apertura'] = (h['open_adj_lead'] / h['close_adj_lag1'].where(h['close_adj_lag1'] > 0) - 1) * 100
    h = h.dropna(subset=['surprise', 'surprise_pct', 'retorno_apertura'])
    h = h[h['surprise_pct'] != 0].copy()

    h['tipo'] = np.where(h['surprise'] < 0, 'Sorpresa negativa', 'Sorpresa positiva')
    h['grupo'] = pd.qcut(h['surprise_pct'].abs(), 4, labels=False) + 1        # 1 = menor magnitud, 4 = mayor
    h['caida_fuerte'] = h['retorno_apertura'] <= -1.98                         # primer cuartil del retorno

    rangos = h.groupby('grupo')['surprise_pct'].apply(lambda s: s.abs().min()).to_frame('desde')
    rangos['hasta'] = h.groupby('grupo')['surprise_pct'].apply(lambda s: s.abs().max())
    nombres = ['menor', 'media-baja', 'media-alta', 'mayor']
    f = lambda v: f'{v:,.1f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    rangos['etiqueta'] = [f'{n} ({f(a)} % a {f(b)} %)' for n, a, b in zip(nombres, rangos['desde'], rangos['hasta'])]

    resumen = (h.groupby(['grupo', 'tipo'])['caida_fuerte'].agg(anuncios='size', riesgo='mean').reset_index())
    resumen['riesgo_pct'] = resumen['riesgo'] * 100
    resumen['magnitud'] = resumen['grupo'].map(rangos['etiqueta'])

    colores = alt.Scale(domain=['Sorpresa negativa', 'Sorpresa positiva'], range=['#E07A5F', '#3D5A80'])
    base = alt.Chart(resumen).encode(
        x=alt.X('magnitud:N', sort=list(rangos['etiqueta']), title='Magnitud de la sorpresa (valor absoluto, de menor a mayor)',
                axis=alt.Axis(labelAngle=0, labelLimit=170)),
        xOffset=alt.XOffset('tipo:N'),
        y=alt.Y('riesgo_pct:Q', title='Anuncios con caída fuerte (%)', scale=alt.Scale(domain=[0, 60])),
        color=alt.Color('tipo:N', scale=colores, title=None, legend=alt.Legend(orient='top')))
    barras = base.mark_bar().encode(tooltip=[
        alt.Tooltip('tipo:N', title='Signo'), alt.Tooltip('magnitud:N', title='Magnitud'),
        alt.Tooltip('anuncios:Q', title='Anuncios', format=','),
        alt.Tooltip('riesgo_pct:Q', title='Caída fuerte (%)', format='.1f')])
    numeros = base.mark_text(dy=-8, fontSize=12).encode(text=alt.Text('riesgo_pct:Q', format='.0f'), color=alt.value('black'))

    return (barras + numeros).properties(
        width=640, height=340,
        title=alt.TitleParams('A igual magnitud, las sorpresas negativas caen fuerte mucho más seguido',
                              subtitle='Caída fuerte: retorno de −1,98 % o menos entre el cierre previo y la primera apertura. 4 grupos con la misma cantidad de anuncios.'))


# ---------- 3. El modelo: retorno por modelo en validación (Entrega 4, celda 10) ----------
# Resumen de validación de la Entrega 3 (28 presupuestos de 100 a 10.000 USD, cada modelo con su umbral único)
RESUMEN_RET = pd.DataFrame([
    ('Random Forest',     6.6354,  5.68, 10.35, 100.0000, 18.5),
    ('Gradient Boosting', 6.2568,  4.35, 10.35, 100.0000, 18.0),
    ('Árbol de decisión', 5.5529,  2.97,  7.92, 100.0000, 19.0),
    ('Regresión lineal',  3.7989,  1.49,  9.11, 100.0000,  9.0),
    ('Comprar todo',      0.3100, -2.76,  1.69,  78.5714, np.nan),
    ('Dummy (media)',    -0.4211, -4.02,  1.96,  35.7143, 18.5),
], columns=['modelo', 'medio', 'minimo', 'maximo', 'con_ganancia', 'umbral'])


def grafico_modelos():
    r = RESUMEN_RET.copy()
    r['umbral_txt'] = r['umbral'].map(lambda u: '—' if pd.isna(u) else f'{u:g} %'.replace('.', ','))
    r['y_txt'] = r['medio'].map(lambda v: v + .45 if v >= 0 else v - .45)
    r['etiqueta'] = r['medio'].map(lambda v: f'{v:.2f} %'.replace('-', '−').replace('.', ','))
    orden = r.sort_values('medio', ascending=False)['modelo'].tolist()

    hover = alt.selection_point(name='hover', fields=['modelo'], on='pointerover', clear='pointerout')
    opac = alt.condition(hover, alt.value(1), alt.value(.6))
    tip = [alt.Tooltip('modelo:N', title='Modelo'),
           alt.Tooltip('medio:Q', title='Retorno medio (%)', format='+.2f'),
           alt.Tooltip('minimo:Q', title='Peor presupuesto (%)', format='+.2f'),
           alt.Tooltip('maximo:Q', title='Mejor presupuesto (%)', format='+.2f'),
           alt.Tooltip('con_ganancia:Q', title='Presupuestos con ganancia (%)', format='.0f'),
           alt.Tooltip('umbral_txt:N', title='Umbral de compra')]

    base = alt.Chart(r).encode(x=alt.X('modelo:N', sort=orden, title=None, axis=alt.Axis(labelAngle=-15)))
    barras = base.mark_bar().encode(
        y=alt.Y('medio:Q', title=['Retorno s/ presupuesto (%)', 'promedio entre presupuestos']),
        color=alt.Color('modelo:N', scale=alt.Scale(domain=list(COLOR), range=list(COLOR.values())), legend=None),
        stroke=alt.condition(alt.datum.modelo == ELEGIDO, alt.value('black'), alt.value('transparent')),
        strokeWidth=alt.value(2.5), opacity=opac, tooltip=tip).add_params(hover)
    numeros = base.mark_text(fontSize=12).encode(y='y_txt:Q', text='etiqueta:N')
    cero = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(color='black').encode(y='y:Q')

    return (barras + cero + numeros).properties(
        width=620, height=340,
        title=alt.TitleParams('Validación: retorno promedio sobre el presupuesto por modelo',
                              subtitle=f'Borde negro: {ELEGIDO}'))


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
    x_esc = alt.Scale(domain=[5.0, 6.2])
    base = alt.Chart(mae).encode(y=y)
    punto = base.mark_circle(size=170, stroke='black', strokeWidth=1.2).encode(
        x=alt.X('mae_cv:Q', scale=x_esc, title='MAE (puntos porcentuales del retorno a 3 días) · menor es mejor'),
        color=alt.Color('modelo:N', scale=colores, legend=None), opacity=opac, tooltip=tip).add_params(hover)
    numeros = base.mark_text(dy=-16, fontSize=12).encode(x='mae_cv:Q', text='etiqueta:N')
    test = (alt.Chart(mae.dropna(subset=['mae_test'])).mark_point(shape='diamond', size=130, filled=True, color='black')
            .encode(y=y, x=alt.X('mae_test:Q', scale=x_esc),
                    tooltip=[alt.Tooltip('modelo:N', title='Modelo'), alt.Tooltip('mae_test:Q', title='MAE test 2026Q3 (pp)', format='.3f')]))
    piso = (alt.Chart(pd.DataFrame({'x': [PISO_CV]})).mark_rule(strokeDash=[5, 4], color='#6D6D6D')
            .encode(x=alt.X('x:Q', scale=x_esc)))

    return (piso + punto + numeros + test).properties(
        width=640, height=300,
        title=alt.TitleParams('Todos los modelos le ganan al piso, pero por poco: el MAE baja de 5,38 a 5,15 pp',
                              subtitle=['Círculo: MAE en validación cruzada temporal. Rombo negro: MAE en test (2026Q3),',
                                        'solo para el modelo final y el piso. Línea punteada: piso (predecir siempre la media).',
                                        'La mejora (−4 %) es menor que el desvío entre folds (±0,5 pp): pasá el cursor para verlo.']))


# =====================================================================================
# Tu turno
# =====================================================================================
SIGNO = alt.Scale(domain=['Sorpresa negativa', 'Sorpresa positiva'], range=['#E07A5F', '#3D5A80'])   # = hallazgos


def _tooltip_balance():
    return [alt.Tooltip('ticker:N', title='Empresa'), alt.Tooltip('fecha:N', title='Fecha del balance'),
            alt.Tooltip('sector:N', title='Sector'),
            alt.Tooltip('surprise_pct:Q', title='Sorpresa (%)', format='+.1f'),
            alt.Tooltip('retorno_esperado:Q', title='El modelo esperaba que subiera (%)', format='+.2f'),
            alt.Tooltip('confianza_pct:Q', title='Confianza en que sube (%)', format='.1f'),
            alt.Tooltip('retorno_operable:Q', title='Subió (%)', format='+.2f'),
            alt.Tooltip('decision:N', title='¿Hubiera comprado?')]


# ---------- Explorá: los balances de 2026Q3, medidos desde la apertura, como decide el modelo ----------
def grafico_explora(pred, umbral):
    d = pred[pred['conjunto'] == 'Test'].copy()          # 2026Q3: lo predice el modelo final, que no lo vio
    d['fecha'] = pd.to_datetime(d['reported_date']).dt.strftime('%d/%m/%Y')
    d['signo'] = np.where(d['surprise_pct'] < 0, 'Sorpresa negativa', 'Sorpresa positiva')
    d['decision'] = np.where(d['compraria'], 'Sí', 'No')
    d['confianza_pct'] = d['confianza'] * 100
    d['sector'] = d['sector'].fillna('Sin sector')
    d = d[['ticker', 'fecha', 'sector', 'surprise_pct', 'retorno_esperado', 'confianza_pct', 'retorno_operable',
           'decision', 'compraria', 'signo']]

    sectores = ['Todos'] + sorted(d['sector'].unique())
    sector = alt.param(name='sector_sel', value='Todos', bind=alt.binding_select(options=sectores, name='Sector '))
    cuales = alt.param(name='cuales', value='Todos',
                       bind=alt.binding_radio(options=['Todos', 'Sólo los que hubiera comprado'], name='Balances '))
    zoom = alt.selection_interval(bind='scales')

    x = alt.X('retorno_esperado:Q', title='Cuánto esperaba el modelo que subiera desde la apertura (%)',
              scale=alt.Scale(domain=[-20, 35]))
    y = alt.Y('retorno_operable:Q', title='Cuánto subió desde la apertura hasta el 3er día (%)',
              scale=alt.Scale(domain=[-25, 25], clamp=True))
    base = (alt.Chart(d)
            .transform_filter("sector_sel == 'Todos' || datum.sector == sector_sel")
            .transform_filter("cuales == 'Todos' || datum.compraria"))
    color = alt.Color('signo:N', scale=SIGNO, title=None, legend=alt.Legend(orient='top'))
    zona = alt.Chart(pd.DataFrame({'x': [umbral], 'x2': [35]})).mark_rect(color='#2A9D8F', opacity=.08).encode(x='x:Q', x2='x2:Q')
    regla = alt.Chart(pd.DataFrame({'x': [umbral]})).mark_rule(color='black', strokeWidth=1.5).encode(x='x:Q')
    etiqueta = alt.Chart(pd.DataFrame({'x': [umbral], 't': [f'umbral {umbral:g} %: a la derecha, compra'.replace('.', ',')]})).mark_text(
        align='left', dx=6, fontSize=12, fontWeight='bold').encode(x='x:Q', y=alt.value(12), text='t:N')
    puntos = base.mark_circle(size=60, opacity=.6).encode(x=x, y=y, color=color, tooltip=_tooltip_balance()).add_params(
        sector, cuales, zoom)
    compras = base.transform_filter('datum.compraria').mark_point(
        size=170, filled=True, stroke='black', strokeWidth=1.5, opacity=1).encode(x=x, y=y, color=color, tooltip=_tooltip_balance())
    cero_y = alt.Chart(pd.DataFrame({'v': [0]})).mark_rule(color='black', strokeDash=[4, 3]).encode(y='v:Q')

    return (zona + regla + cero_y + puntos + compras + etiqueta).properties(
        width=740, height=460,
        title=alt.TitleParams(f'Los {len(d)} balances de 2026Q3: lo que esperaba el modelo, lo que pasó y si hubiera comprado',
                              subtitle=['Todo medido desde el precio de apertura, el primero al que se puede comprar. Con borde negro, los que hubiera comprado:',
                                        'arriba de la línea punteada ganaron, abajo perdieron. Rueda del mouse para hacer zoom, doble clic para volver.']))


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

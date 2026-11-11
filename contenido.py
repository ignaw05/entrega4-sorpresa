"""Tablas de los «Cómo lo sabemos» (datos de la Entrega 4)."""


def tabla(encabezado, filas, negrita_ultima=False):
    th = "".join(f"<th>{c}</th>" for c in encabezado)
    trs = []
    for i, f in enumerate(filas):
        tds = "".join(f"<td>{c}</td>" for c in f)
        cls = ' class="total"' if negrita_ultima and i == len(filas) - 1 else ""
        trs.append(f"<tr{cls}>{tds}</tr>")
    return f'<div class="tabla"><table><thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table></div>'


# ---------- Tablas (datos de la Entrega 4) ----------
T_FILTROS = tabla(
    ["Paso", "Filas", "Qué se hizo y por qué"],
    [["Silver del pipeline", "11.317", "Una fila por anuncio trimestral. Sin duplicados en (<code>ticker</code>, <code>fiscal_quarter_end</code>)."],
     ["Con objetivo y sorpresa", "11.253", "Se sacan 64 filas donde falta algún dato necesario: 34 sin <code>close_adj_lead3</code> (el anuncio es tan reciente que no pasaron tres ruedas), 27 sin <code>surprise_pct</code> (sin consenso de analistas) y 3 sin precios de apertura o de cierre."],
     ["Con precios positivos", "11.253", "Se exige <code>close_adj_lag1 &gt; 0</code> y <code>open_adj_lead &gt; 0</code>. No se saca ninguna fila más."],
     ["Sin trimestre incompleto", "11.235", "Se sacan 18 anuncios de 2026Q4, un trimestre que la captura cortó a la mitad (en los demás hay entre 466 y 525 por trimestre). No sirve como validación ni como test."]])

T_PARTICION = tabla(
    ["Conjunto", "Anuncios", "Empresas", "Desde", "Hasta", "% de las filas", "Para qué se usa"],
    [["Entrenamiento", "9.688", "576", "25/01/2008", "19/12/2025", "86,2 %", "Ajustar los modelos y compararlos con validación cruzada temporal."],
     ["Validación", "1.046", "538", "07/01/2026", "30/06/2026", "9,3 %", "Elegir el umbral de compra y el modelo final."],
     ["Test", "501", "498", "01/07/2026", "30/09/2026", "4,5 %", "Medir una sola vez el modelo elegido."]])

T_MAE = tabla(
    ["Modelo", "MAE validación cruzada (pp)", "Mejora vs. piso", "MAE test 2026Q3 (pp)"],
    [["Dummy (media) · piso", "5,375 ± 0,529", "—", "6,013"],
     ["Regresión lineal", "5,256 ± 0,572", "−2,2 %", "—"],
     ["Árbol de decisión", "5,215 ± 0,523", "−3,0 %", "—"],
     ["Gradient Boosting", "5,174 ± 0,509", "−3,7 %", "—"],
     ["<b>Random Forest</b>", "<b>5,149 ± 0,515</b>", "<b>−4,2 %</b>", "<b>5,829</b>"]])

T_RETORNO = tabla(
    ["Modelo", "Umbral", "Retorno medio s/ presupuesto", "Peor presupuesto", "Mejor presupuesto", "Presupuestos con ganancia"],
    [["<b>Random Forest</b>", "18,5 %", "<b>+6,64 %</b>", "+5,68 %", "+10,35 %", "100 %"],
     ["Gradient Boosting", "18 %", "+6,26 %", "+4,35 %", "+10,35 %", "100 %"],
     ["Árbol de decisión", "19 %", "+5,55 %", "+2,97 %", "+7,92 %", "100 %"],
     ["Regresión lineal", "9 %", "+3,80 %", "+1,49 %", "+9,11 %", "100 %"],
     ["Comprar todo", "—", "+0,31 %", "−2,76 %", "+1,69 %", "79 %"],
     ["Dummy (media)", "18,5 %", "−0,42 %", "−4,02 %", "+1,96 %", "36 %"]])

T_COMPRAS = tabla(
    ["#", "Ticker", "Fecha del balance", "Acciones", "Precio de compra (USD)", "Pagó (USD)", "Precio de venta (USD)",
     "Vendió en (USD)", "Ganancia (USD)", "Resultado", "Retorno real", "Retorno esperado", "Confianza"],
    [["1", "CDW", "05/08/2026", "3", "114,90", "344,70", "135,78", "407,34", '<span class="gana">+62,64</span>', "ganó", "+18,17 %", "+31,44 %", "55,9 %"],
     ["2", "BRKR", "04/08/2026", "3", "54,03", "162,08", "53,37", "160,10", '<span class="pierde">−1,98</span>', "perdió", "−1,22 %", "+19,86 %", "54,9 %"],
     ["3", "AMKR", "27/07/2026", "4", "51,70", "206,82", "49,78", "199,11", '<span class="pierde">−7,71</span>', "perdió", "−3,73 %", "+20,48 %", "55,0 %"],
     ["4", "DKS", "25/08/2026", "2", "141,02", "282,05", "133,82", "267,64", '<span class="pierde">−14,40</span>', "perdió", "−5,11 %", "+20,16 %", "54,9 %"],
     ["<b>Total</b>", "", "", "", "", "<b>995,65</b>", "", "<b>1.034,19</b>", '<b class="gana">+38,55</b>', "", "", "", ""]],
    negrita_ultima=True)

SOPORTE = [
    ("Todas", 501, "Sorpresa (USD) (+2,52), Flujo operativo (+1,28), Sorpresa (%) (+1,20)", "Activos totales (−0,57), Dividendos (−0,41), Precio previo (−0,38)"),
    ("Industrials", 116, "Sorpresa (USD) (+2,88), Sorpresa (%) (+1,58), Flujo operativo (+1,57)", "Activos totales (−0,73), Dividendos (−0,52), Caja (−0,44)"),
    ("Consumer Cyclical", 74, "Sorpresa (USD) (+3,25), Flujo operativo (+1,70), Sorpresa (%) (+1,43)", "Activos totales (−0,83), Precio previo (−0,55), Dividendos (−0,52)"),
    ("Technology", 59, "Sorpresa (USD) (+2,77), Sorpresa (%) (+1,39), Flujo operativo (+1,33)", "Precio previo (−0,51), Dividendos (−0,42), Caja (−0,35)"),
    ("Utilities", 39, "Flujo operativo (+0,79), Margen operativo (+0,44), Sorpresa (USD) (+0,42)", "Activos totales (−0,32), Ganancia neta (−0,30), Pasivo corriente (−0,25)"),
    ("Healthcare", 39, "Sorpresa (USD) (+2,74), Sorpresa (%) (+1,34), Flujo operativo (+0,88)", "Precio previo (−0,28), Activos totales (−0,28), Caja (−0,25)"),
    ("Energy", 35, "Sorpresa (USD) (+2,44), Sorpresa (%) (+1,15), Flujo operativo (+0,81)", "Dividendos (−0,37), Activos totales (−0,37), Margen bruto (−0,22)"),
    ("Basic Materials", 33, "Sorpresa (USD) (+2,61), Flujo operativo (+1,37), Sorpresa (%) (+1,29)", "Activos totales (−0,54), Dividendos (−0,50), Precio previo (−0,43)"),
    ("Consumer Defensive", 31, "Sorpresa (USD) (+2,70), Sorpresa (%) (+1,23), Flujo operativo (+0,93)", "Activos totales (−0,56), Precio previo (−0,44), Dividendos (−0,31)"),
    ("Real Estate", 29, "Flujo operativo (+1,42), Sorpresa (USD) (+1,38), Margen de flujo libre (+0,26)", "Activos totales (−1,02), Precio previo (−0,45), Dividendos (−0,33)"),
    ("Financial Services", 29, "Sorpresa (USD) (+1,83), Flujo operativo (+0,89), Sorpresa (%) (+0,85)", "Precio previo (−0,39), Dividendos (−0,33), Inversión (capex) (−0,29)"),
    ("Communication Services", 17, "Sorpresa (USD) (+3,00), Flujo operativo (+1,13), Sorpresa (%) (+0,84)", "Activos totales (−0,92), Dividendos (−0,42), Pasivo corriente (−0,32)"),
]
T_SOPORTE = tabla(["Sector", "Balances (test)", "Empujan a comprar", "Empujan a no comprar"],
                  [[s, str(b), a, c] for s, b, a, c in SOPORTE])

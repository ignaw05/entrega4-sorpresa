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

def tabla_metricas(metricas):
    """Tabla recalculada con la versión actual del objetivo del modelo."""
    mejora = metricas['mejora_mae_test_pct']
    return tabla(
        ["Modelo", "MAE validación cruzada (pp)", "MAE test 2026Q3 (pp)", "Cambio vs. piso en test"],
        [["Random Forest (candidato)",
          f"{metricas['mae_cv']:.3f} ± {metricas['mae_cv_desvio']:.3f}",
          f"{metricas['mae_test']:.3f}", f"{mejora:+.1f} %"],
         ["Dummy (media)",
          f"{metricas['mae_piso_cv']:.3f} ± {metricas['mae_piso_cv_desvio']:.3f}",
          f"{metricas['mae_piso_test']:.3f}", "—"]])

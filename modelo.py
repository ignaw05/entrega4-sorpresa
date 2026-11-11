"""El modelo de la Entrega 3, tal como quedó elegido: mismo pipeline, mismas columnas, misma semilla.

Todo el código de acá está copiado del notebook de la Entrega 3 (secciones 1, 2, 3, 7 y 8).
Las decisiones no se recalculan, se verifican: el modelo final es el Random Forest elegido en validación
(200 árboles, min_samples_leaf=20, max_depth=None) y el umbral sale de la misma búsqueda de la sección 7.
`entrenar.py` lo corre y compara contra los números del notebook.
"""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SEMILLA = 42
HORIZONTE = 'close_adj_lead3'
OBJETIVO = 'retorno_lead3'
ELEGIDO = 'Random Forest'

BLOQUES = {
    'Sorpresa': ['surprise_pct', 'sorpresa_sobre_precio'],
    'Rentabilidad': ['gross_margin', 'operating_margin', 'margen_neto', 'roa', 'ebitda_margin'],
    'Flujo de caja': ['free_cash_flow_margin', 'flujo_op_sobre_activos', 'capex_sobre_activos',
                      'dividendos_sobre_activos', 'cash_sobre_activos'],
    'Balance': ['debt_to_assets', 'liquidez_corriente'],
}
NUMERICAS = [c for cols in BLOQUES.values() for c in cols]
CATEGORICAS = ['sector', 'industry', 'exchange', 'report_time']
# La ablación de la Entrega 3 (sección 6) no sacó ningún bloque: 14 numéricas + 4 categóricas
NUM_FINAL, CAT_FINAL = list(NUMERICAS), list(CATEGORICAS)

COLUMNAS_CRUDAS = CATEGORICAS + [
    'surprise_pct', 'surprise', 'close_adj_lag1', 'gross_margin', 'operating_margin', 'free_cash_flow_margin',
    'debt_to_assets', 'total_current_assets', 'total_current_liabilities', 'net_income', 'total_revenue',
    'total_assets', 'operating_cashflow', 'capital_expenditures', 'dividend_payout', 'ebitda',
    'cash_and_equivalents']
ENTRADA_NUM = [c for c in COLUMNAS_CRUDAS if c not in CATEGORICAS]

PRESUPUESTOS = list(range(100, 1001, 100)) + list(range(1500, 10001, 500))   # 28 presupuestos
GRILLA_UMBRAL = np.round(np.arange(0, 45, 0.5), 2)
MIN_COMPRAS = 3
RECORTE_ESP = 30


# ---------- Sección 3: pipeline ----------
class Ratios(BaseEstimator, TransformerMixin):
    """Calcula los ratios fila por fila a partir de las columnas crudas. No aprende nada del entrenamiento."""
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        def dividir(a, b):
            return X[a] / X[b].where(X[b].ne(0))
        X['sorpresa_sobre_precio'] = X['surprise'] * 100 / X['close_adj_lag1'].where(X['close_adj_lag1'].ne(0))
        X['liquidez_corriente'] = dividir('total_current_assets', 'total_current_liabilities')
        X['margen_neto'] = dividir('net_income', 'total_revenue')
        X['roa'] = dividir('net_income', 'total_assets')
        X['flujo_op_sobre_activos'] = dividir('operating_cashflow', 'total_assets')
        X['capex_sobre_activos'] = X['capital_expenditures'].abs() / X['total_assets'].where(X['total_assets'].ne(0))
        X['dividendos_sobre_activos'] = X['dividend_payout'].abs() / X['total_assets'].where(X['total_assets'].ne(0))
        X['ebitda_margin'] = dividir('ebitda', 'total_revenue')
        X['cash_sobre_activos'] = dividir('cash_and_equivalents', 'total_assets')
        return X.replace([np.inf, -np.inf], np.nan)


class Recortar(BaseEstimator, TransformerMixin):
    """Recorta cada columna a sus percentiles q y 1-q, calculados SÓLO con los datos de entrenamiento."""
    def __init__(self, q=0.01):
        self.q = q

    def fit(self, X, y=None):
        X = np.asarray(X, dtype=float)
        self.lo_ = np.nanquantile(X, self.q, axis=0)
        self.hi_ = np.nanquantile(X, 1 - self.q, axis=0)
        return self

    def transform(self, X):
        return np.clip(np.asarray(X, dtype=float), self.lo_, self.hi_)


def armar_pipeline(estimador, numericas=None, categoricas=None):
    numericas = NUMERICAS if numericas is None else numericas
    categoricas = CATEGORICAS if categoricas is None else categoricas
    pasos = []
    if categoricas:
        pasos.append(('cat', OneHotEncoder(handle_unknown='ignore'), list(categoricas)))
    if numericas:
        pasos.append(('num', make_pipeline(SimpleImputer(strategy='median', keep_empty_features=True),
                                           Recortar(0.01), StandardScaler()), list(numericas)))
    return Pipeline([('ratios', Ratios()), ('prep', ColumnTransformer(pasos)), ('modelo', clone(estimador))])


def random_forest():
    # El elegido en el ajuste de la sección 5: max_depth=None, min_samples_leaf=20
    return RandomForestRegressor(n_estimators=200, min_samples_leaf=20, max_depth=None, n_jobs=-1, random_state=SEMILLA)


# ---------- Secciones 1 y 2: objetivo y partición ----------
def preparar(df_stocks):
    df = df_stocks.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=[HORIZONTE, 'close_adj_lag1', 'open_adj_lead', 'surprise_pct', 'reported_date'])
    df = df[(df['close_adj_lag1'] > 0) & (df['open_adj_lead'] > 0)].copy()
    df[OBJETIVO] = (df[HORIZONTE] / df['close_adj_lag1'] - 1) * 100
    df['retorno_operable'] = (df[HORIZONTE] / df['open_adj_lead'] - 1) * 100
    df['salto_apertura'] = (df['open_adj_lead'] / df['close_adj_lag1'] - 1) * 100
    df['trimestre'] = df['reported_date'].dt.to_period('Q')
    df['anio'] = df['reported_date'].dt.year
    df['report_time'] = df['report_time'].fillna('desconocido')

    conteo = df.groupby('trimestre').size()
    completos = conteo[conteo >= 0.5 * conteo.median()].index
    test_t = completos.max()
    val_t = sorted(t for t in completos if t < test_t)[-2:]
    df = df[df['trimestre'] <= test_t].copy()
    test = df[df['trimestre'] == test_t].copy()
    val = df[df['trimestre'].isin(val_t)].copy()
    train = df[df['trimestre'] < min(val_t)].copy()
    return df, train, val, test


# ---------- Sección 7: regla de inversión ----------
def esperado_desde_apertura(datos, pred):
    precio_pred = datos['close_adj_lag1'].to_numpy() * (1 + np.asarray(pred) / 100)
    return (precio_pred / datos['open_adj_lead'].to_numpy() - 1) * 100


def prob_subida(calibrador, esperado):
    x = np.clip(np.asarray(esperado, dtype=float), -RECORTE_ESP, RECORTE_ESP).reshape(-1, 1)
    return calibrador.predict_proba(x)[:, 1]


def simular_presupuesto(peso, precio, presupuesto):
    """Reparte el presupuesto UNA SOLA VEZ entre los balances con peso > 0, proporcional al peso, comprando
    ACCIONES ENTERAS al precio de apertura. Lo que sobra por redondeo se usa para sumar acciones de a una,
    empezando por las de mayor peso. Devuelve los USD invertidos por balance. (Igual que la Entrega 3.)"""
    peso, precio = np.asarray(peso, dtype=float), np.asarray(precio, dtype=float)
    montos = np.zeros(len(peso))
    c = np.flatnonzero(peso > 0)
    if not len(c):
        return montos
    acciones = np.floor(presupuesto * peso[c] / peso[c].sum() / precio[c])
    sobra = presupuesto - (acciones * precio[c]).sum()
    orden = np.argsort(-peso[c], kind='stable')
    sumo = True
    while sumo and sobra >= precio[c].min():
        sumo = False
        for k in orden:
            if precio[c][k] <= sobra:
                acciones[k] += 1; sobra -= precio[c][k]; sumo = True
    montos[c] = acciones * precio[c]
    return montos


def peso_modelo(esperado, prob, umbral):
    return np.where(np.asarray(esperado) > umbral, np.clip(np.asarray(prob) - 0.5, 0, None), 0.0)


def resultado(montos, real, presupuesto):
    g = montos * real / 100
    compro = montos > 0
    return {'compras': int(compro.sum()), 'invertido (USD)': montos.sum(), 'ganancia (USD)': g.sum(),
            'retorno s/ presupuesto (%)': g.sum() / presupuesto * 100}


def buscar_umbral(esperado, prob, precio, real):
    """Umbral único de la sección 7: mayor retorno s/ presupuesto promediado entre los 28 presupuestos,
    con al menos MIN_COMPRAS compras en todos (o al menos una donde no se llega al mínimo con ningún umbral)."""
    filas = []
    for p in PRESUPUESTOS:
        for u in GRILLA_UMBRAL:
            montos = simular_presupuesto(peso_modelo(esperado, prob, u), precio, p)
            filas.append({'presupuesto (USD)': p, 'umbral (%)': u, **resultado(montos, real, p)})
    b = pd.DataFrame(filas)
    factible = b.groupby('presupuesto (USD)')['compras'].max() >= MIN_COMPRAS
    b['llega'] = b['presupuesto (USD)'].map(factible)
    b['cumple'] = np.where(b['llega'], b['compras'] >= MIN_COMPRAS, b['compras'] > 0)
    ok = b.groupby('umbral (%)')['cumple'].all()
    prom = b.groupby('umbral (%)')['retorno s/ presupuesto (%)'].mean()[ok]
    return float(prom.idxmax()), float(prom.max())


# ---------- Todo junto ----------
def entrenar(df_stocks):
    """Reproduce la Entrega 3 para el modelo elegido y devuelve lo que usa la aplicación."""
    df, train, val, test = preparar(df_stocks)
    train_val = pd.concat([train, val])
    anios_cv = sorted(train['anio'].unique())[-5:]
    folds = [(train.index[train['anio'] < a], train.index[train['anio'] == a]) for a in anios_cv]
    rf = random_forest()

    # Validación cruzada temporal (sección 4) y predicciones fuera de muestra para calibrar (sección 7)
    mae_folds, partes_pred, partes_esp, reales = [], [], [], []
    for i_tr, i_va in folds:
        pipe = armar_pipeline(rf, NUM_FINAL, CAT_FINAL).fit(train.loc[i_tr, COLUMNAS_CRUDAS], train.loc[i_tr, OBJETIVO])
        pred = pipe.predict(train.loc[i_va, COLUMNAS_CRUDAS])
        mae_folds.append(np.mean(np.abs(train.loc[i_va, OBJETIVO].to_numpy() - pred)))
        partes_pred.append(pred)
        partes_esp.append(esperado_desde_apertura(train.loc[i_va], pred))
        reales.append(train.loc[i_va, 'retorno_operable'].to_numpy())
    esp_oof = np.concatenate(partes_esp)
    sube_oof = (np.concatenate(reales) > 0).astype(int)
    calibrador = LogisticRegression(C=1e6).fit(np.clip(esp_oof, -RECORTE_ESP, RECORTE_ESP).reshape(-1, 1), sube_oof)

    # Validación: modelo entrenado con train; búsqueda del umbral único
    pipe_train = armar_pipeline(rf, NUM_FINAL, CAT_FINAL).fit(train[COLUMNAS_CRUDAS], train[OBJETIVO])
    pred_val = pipe_train.predict(val[COLUMNAS_CRUDAS])
    esp_val = esperado_desde_apertura(val, pred_val)
    prob_val = prob_subida(calibrador, esp_val)
    umbral, ret_val = buscar_umbral(esp_val, prob_val, val['open_adj_lead'].to_numpy(), val['retorno_operable'].to_numpy())

    # Modelo final: train + validación, medido en test
    pipe_final = armar_pipeline(rf, NUM_FINAL, CAT_FINAL).fit(train_val[COLUMNAS_CRUDAS], train_val[OBJETIVO])
    pred_test = pipe_final.predict(test[COLUMNAS_CRUDAS])

    # Cada balance con la predicción de un modelo que no lo vio
    oof = train.loc[np.concatenate([i_va for _, i_va in folds])].copy()
    oof['conjunto'], oof['prediccion'] = 'Entrenamiento (fuera de muestra)', np.concatenate(partes_pred)
    v, t = val.copy(), test.copy()
    v['conjunto'], v['prediccion'] = 'Validación', pred_val
    t['conjunto'], t['prediccion'] = 'Test', pred_test
    pred = pd.concat([oof, v, t])
    pred['retorno_esperado'] = esperado_desde_apertura(pred, pred['prediccion'])
    pred['confianza'] = prob_subida(calibrador, pred['retorno_esperado'])
    pred['compraria'] = (pred['retorno_esperado'] > umbral) & (pred['confianza'] > 0.5)
    pred['trimestre'] = pred['trimestre'].astype(str)

    metricas = {'mae_cv': float(np.mean(mae_folds)), 'mae_cv_desvio': float(np.std(mae_folds, ddof=1)),
                'mae_test': float(np.mean(np.abs(test[OBJETIVO].to_numpy() - pred_test))),
                'umbral': umbral, 'retorno_val': ret_val, 'anios_cv': [int(a) for a in anios_cv],
                'calibracion': {'a': float(calibrador.intercept_[0]), 'b': float(calibrador.coef_[0, 0])}}
    referencia = {  # lo que necesita «Probá el modelo»: rango y valores que vio el entrenamiento
        'rango': {c: (float(train_val[c].min()), float(train_val[c].max())) for c in ENTRADA_NUM},
        'mediana': {c: float(train_val[c].median()) for c in ENTRADA_NUM},
        'categorias': {c: sorted(train_val[c].dropna().astype(str).unique()) for c in CATEGORICAS},
        'industrias_por_sector': train_val.dropna(subset=['sector', 'industry']).groupby('sector')['industry']
                                          .apply(lambda s: sorted(s.unique())).to_dict(),
        'terciles_activos': [float(q) for q in np.nanquantile(train['total_assets'], [1 / 3, 2 / 3])],
    }
    return {'pipe': pipe_final, 'calibrador': calibrador, 'umbral': umbral,
            'predicciones': pred, 'metricas': metricas, 'referencia': referencia}

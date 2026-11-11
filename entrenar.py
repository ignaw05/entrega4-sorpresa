"""Entrena el modelo de la aplicación para anticipar la reacción a tres ruedas.

    python entrenar.py

Lee silver_stocks_2.csv (si no está, lo baja del Drive), y escribe:
  modelo_final.joblib  -> pipeline final, calibración, umbral, métricas y rangos para «Probá el modelo»
  predicciones.csv     -> cada balance con la predicción de un modelo que no lo vio (para «Explorá» y «Simulá»)
Las métricas corresponden al objetivo de predicción del notebook; la apertura se usa sólo en la simulación de compra.
Si cambian los datos, se vuelve a correr.
"""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

import modelo as m

AQUI = Path(__file__).parent
ARCHIVO = AQUI / 'silver_stocks_2.csv'
DRIVE_ID = '1EFASiJezcUvgZku6Z-ixgfOc2740E9M_'

COLS_PRED = list(dict.fromkeys([
    'ticker', 'reported_date', 'trimestre', 'conjunto', *m.COLUMNAS_CRUDAS, 'open_adj_lead',
    'close_adj_lead3', m.OBJETIVO, 'retorno_operable', 'retorno_esperado', 'confianza', 'compraria'
]))


def cargar():
    if not ARCHIVO.is_file():
        import gdown
        gdown.download(id=DRIVE_ID, output=str(ARCHIVO), quiet=True)
    df = pd.read_csv(ARCHIVO, low_memory=False)
    df['reported_date'] = pd.to_datetime(df['reported_date'], errors='coerce')
    return df


def main():
    r = m.entrenar(cargar())
    r['predicciones'][COLS_PRED].to_csv(AQUI / 'predicciones.csv', index=False)
    artefacto = {k: r[k] for k in ['pipe', 'calibrador', 'umbral', 'metricas', 'referencia']}
    artefacto['objetivo'] = m.VERSION_OBJETIVO
    joblib.dump(artefacto, AQUI / 'modelo_final.joblib', compress=3)

    print(f'Objetivo: {m.OBJETIVO} = 100 × (close_adj_lead3 / close_adj_lag1 − 1)')
    print('La apertura se usa sólo después de predecir, para evaluar la decisión de compra.')
    print('Métricas recalculadas con validación temporal:')
    for clave in ['mae_cv', 'mae_cv_desvio', 'mae_piso_cv', 'mae_test', 'mae_piso_test',
                  'mejora_mae_test_pct', 'umbral', 'retorno_val']:
        print(f'  {clave:22s} {r["metricas"][clave]:.4f}')
    p = r['predicciones']
    print(f'predicciones.csv: {len(p):,} balances · {p["conjunto"].value_counts().to_dict()}')
    print(f'modelo_final.joblib: {(AQUI / "modelo_final.joblib").stat().st_size / 1e6:.1f} MB')


if __name__ == '__main__':
    main()

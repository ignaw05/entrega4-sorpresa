"""Entrena el modelo de la Entrega 3 con la misma semilla y guarda lo que usa la aplicación.

    python entrenar.py

Lee silver_stocks_2.csv (si no está, lo baja del Drive), y escribe:
  modelo_final.joblib  -> pipeline final, calibración, umbral, métricas y rangos para «Probá el modelo»
  predicciones.csv     -> cada balance con la predicción de un modelo que no lo vio (para «Explorá» y «Simulá»)
Al final compara contra los números del notebook de la Entrega 3. Si los datos cambian, se vuelve a correr.
"""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

import modelo as m

AQUI = Path(__file__).parent
ARCHIVO = AQUI / 'silver_stocks_2.csv'
DRIVE_ID = '1EFASiJezcUvgZku6Z-ixgfOc2740E9M_'

# Números del notebook de la Entrega 3, para comprobar que la app usa el mismo modelo
NOTEBOOK = {'mae_cv': 5.149, 'mae_cv_desvio': 0.515, 'mae_test': 5.829, 'umbral': 18.5, 'retorno_val': 6.6354}

COLS_PRED = ['ticker', 'reported_date', 'trimestre', 'conjunto', *m.COLUMNAS_CRUDAS, 'open_adj_lead',
             'close_adj_lead3', m.OBJETIVO, 'retorno_operable', 'prediccion', 'retorno_esperado', 'confianza', 'compraria']


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
    joblib.dump({k: r[k] for k in ['pipe', 'calibrador', 'umbral', 'metricas', 'referencia']},
                AQUI / 'modelo_final.joblib', compress=3)

    print('Comparación con el notebook de la Entrega 3:')
    for k, esperado in NOTEBOOK.items():
        valor = r['metricas'][k]
        print(f'  {k:15s} app {valor:8.4f} · notebook {esperado:8.4f} · {"OK" if abs(valor - esperado) < 6e-4 else "DISTINTO"}')
    p = r['predicciones']
    print(f'predicciones.csv: {len(p):,} balances · {p["conjunto"].value_counts().to_dict()}')
    print(f'modelo_final.joblib: {(AQUI / "modelo_final.joblib").stat().st_size / 1e6:.1f} MB')


if __name__ == '__main__':
    main()

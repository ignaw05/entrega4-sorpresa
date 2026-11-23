"""Arma empresas.csv: el nombre y el logo de cada ticker del Silver. Se corre una sola vez (o si cambian las empresas).

    pip install yfinance
    python empresas.py

Nombre: el de Yahoo Finance (la misma fuente del pipeline); si Yahoo no lo tiene, el de la SEC.
Logo: el link a la imagen de Financial Modeling Prep (gratis, sin clave); la app lo usa directo, no se descarga.
"""
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import yfinance as yf

AQUI = Path(__file__).parent
LOGO = 'https://financialmodelingprep.com/image-stock/{}.png'
SEC = 'https://www.sec.gov/files/company_tickers.json'
AGENTE = 'Proyecto integrador UTN FRM contacto@example.com'   # la SEC pide un User-Agent con contacto


def nombre_yahoo(ticker):
    try:
        info = yf.Ticker(ticker).info
        return info.get('longName') or info.get('shortName')
    except Exception:
        return None


def main():
    tickers = sorted(pd.read_csv(AQUI / 'silver_stocks_2.csv', usecols=['ticker'])['ticker'].dropna().unique())
    with ThreadPoolExecutor(4) as ex:   # ponytail: 4 hilos para no pegarle de más a Yahoo
        yahoo = dict(zip(tickers, ex.map(nombre_yahoo, tickers)))
    try:
        req = urllib.request.Request(SEC, headers={'User-Agent': AGENTE})
        sec = {v['ticker']: v['title'].title() for v in json.load(urllib.request.urlopen(req)).values()}
    except Exception as e:   # sin la SEC quedan solo los nombres de Yahoo
        print('No se pudo leer la SEC:', e)
        sec = {}

    df = pd.DataFrame({'ticker': tickers})
    df['nombre'] = df['ticker'].map(yahoo).fillna(df['ticker'].map(sec)).fillna(df['ticker'])
    df['logo'] = df['ticker'].map(LOGO.format)
    df.to_csv(AQUI / 'empresas.csv', index=False)
    print(f'empresas.csv: {len(df)} empresas · {df["ticker"].map(yahoo).notna().sum()} nombres de Yahoo · '
          f'{(df["nombre"] == df["ticker"]).sum()} sin nombre')


if __name__ == '__main__':
    main()

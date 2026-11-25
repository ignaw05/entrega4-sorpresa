# ¿La sorpresa del balance mueve la acción? — App (Entrega 4)

## Correrla local
```
pip install -r requirements.txt
streamlit run app.py
```
Datos: `silver_stocks_2.csv`, el Silver del pipeline. Si está en esta carpeta, la app usa ese; si no, lo baja del
Drive del proyecto (ID `1EFASiJezcUvgZku6Z-ixgfOc2740E9M_`).

## El modelo
`modelo.py` tiene el pipeline de la Entrega 3 copiado tal cual (`Ratios`, `Recortar`, partición por fecha,
Random Forest con 200 árboles y `min_samples_leaf=20`, calibración de Platt y búsqueda del umbral único).

```
python entrenar.py
```
entrena con la misma semilla (42), escribe `modelo_final.joblib` y `predicciones.csv`, y compara contra el notebook:

| | App | Notebook E3 |
|---|---|---|
| MAE validación cruzada | 5,149 ± 0,515 | 5,149 ± 0,515 |
| MAE test 2026Q3 | 5,829 | 5,829 |
| Umbral único | 18,5 % | 18,5 % |
| Retorno s/ presupuesto en validación | 6,6354 % | 6,6354 % |
| Compras con 1.000 USD en test | 4, +38,55 USD | 4, +38,55 USD |

**Nombres y logos:** `python empresas.py` (necesita `pip install yfinance`) escribe `empresas.csv` con el nombre de cada
empresa (Yahoo Finance, o la SEC si Yahoo no lo tiene) y el link a su logo (Financial Modeling Prep, gratis y sin clave).
Si el archivo no está, la app muestra solo el ticker.

**Si los datos cambian:** reemplazar el CSV, correr `python entrenar.py` y subir los dos archivos que genera.
Si `modelo_final.joblib` no está o no se puede leer, la app entrena el modelo sola al arrancar (tarda un par de minutos).
El `.joblib` se guardó con scikit-learn 1.9.1; si lo regeneran con otra versión, cambien la versión en `requirements.txt`.

## Archivos
- `app.py`: la página, en el orden de la historia (portada, datos, hallazgos, modelo) y la copa (explorá, probá, simulá).
- `graficos.py`: todos los gráficos, en Altair. Los del tallo tienen el mismo código que el notebook de la Entrega 4.
- `modelo.py` y `entrenar.py`: el modelo de la Entrega 3 y el script que lo entrena.
- `contenido.py`: las tablas de los «Cómo lo sabemos».
- `estilo.css` y `.streamlit/config.toml`: el estilo.

## Qué toca cada control de la copa
- **Explorá**: sorpresa contra retorno a 3 días de los 501 balances de 2026Q3, sin modelo. El control «Sector» filtra
  (`transform_filter`); un clic en un punto abre su balance en el panel de la derecha (`on_select` de Streamlit).
- **Probá una sorpresa**: se elige una empresa (su último balance) y solo se mueve la sorpresa. La apertura queda la real
  de ese día, porque la regla de compra mide desde la apertura.
- **Simulá una inversión**: presupuesto, umbral, sectores y tamaño. El umbral es el mismo que en «Probá»
  (`st.session_state['umbral']`): moverlo en uno cambia el otro.

La sección «El modelo» calcula al arrancar (con caché) el R² y la grilla umbral × presupuesto en validación, para el
Random Forest y el dummy (`m.grilla`, `m.dummy_validacion`). El dummy reproduce el −0,42 % del notebook.

## Publicarla
En share.streamlit.io: New app → el repositorio del grupo → archivo principal `app.py`.

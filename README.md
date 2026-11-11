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
- **Explorá** (controles de Altair, debajo del gráfico): «Eje vertical» cambia el campo del eje y (`transform_calculate`);
  «Lo predijo», «Sector» y «Balances» filtran los datos (`transform_filter`). Arrastrar y la rueda del mouse cambian la escala
  (zoom). El tooltip muestra lo que dijo el modelo sobre cada balance.
- **Probá el modelo**: los campos arman una fila con las columnas crudas del Silver, que pasa por el pipeline final.
  Avisa si un valor queda fuera del rango que vio el entrenamiento.
- **Simulá una inversión**: el presupuesto, el período, los sectores y el tamaño filtran los balances; sobre ese universo
  corre la misma regla de compra de la Entrega 3 (`simular_presupuesto`).

## Publicarla
En share.streamlit.io: New app → el repositorio del grupo → archivo principal `app/app.py`.

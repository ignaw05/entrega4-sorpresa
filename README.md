# Entrega 4 · ¿Qué ocurre con la acción después del balance?

Aplicación interactiva en Streamlit para explorar la sorpresa de resultados, estimar el precio de cierre de la tercera
rueda posterior al anuncio y compararlo con la primera apertura negociable para evaluar una posible compra.

## Objetivo del modelo

La variable objetivo es el retorno porcentual desde el último cierre previo al anuncio hasta el cierre de la tercera rueda:

\[
\text{retorno\_lead3} = 100 \times
\left(\frac{\text{close\_adj\_lead3}}{\text{close\_adj\_lag1}} - 1\right)
\]

La predicción usa los datos publicados con el balance y el cierre previo, sin usar la apertura de la rueda siguiente.
Después de predecir el cierre de la tercera rueda, la aplicación compara ese precio estimado con open_adj_lead para
calcular el retorno potencial de una compra. open_adj_lead, close_adj_lead3 y close_adj_lead7 no son predictores.
ma30 también queda fuera porque incluye la rueda de reacción.

El Random Forest conserva el objetivo planteado en la Entrega 3. La app muestra su error frente a un Dummy que predice
la media, con validación temporal y un trimestre de test separado. Las ganancias simuladas no contemplan costos de operación.

## Ejecutar localmente

Instalación: pip install -r requirements.txt

Iniciar: streamlit run app.py

La aplicación usa silver_stocks_2.csv de esta carpeta. Si no está, lo descarga desde el archivo compartido del
proyecto. El CSV corresponde a la salida Silver del pipeline; para actualizar los datos, reemplazarlo por el Silver
validado más reciente.

## Regenerar modelo y predicciones

Ejecutar: python entrenar.py

El script vuelve a ajustar el modelo, busca el umbral en validación temporal y genera:

- modelo_final.joblib: pipeline entrenado, calibrador, umbral, métricas y rangos de referencia.
- predicciones.csv: predicciones fuera de muestra para la exploración y simulación.

La aplicación verifica la versión del objetivo y regenera los archivos si no corresponden; ejecutar entrenar.py de
antemano evita la demora de la primera carga. Si cambian los datos o el pipeline, volver a ejecutar el script antes de
publicar para mantener la app alineada con la Entrega 3.

## Estructura

- app.py: relato, interacción, exploración de balances, prueba del modelo y simulación.
- graficos.py: gráficos Altair y sus campos, marcas, transformaciones y controles.
- modelo.py: objetivo, partición temporal, pipeline, evaluación y simulación.
- entrenar.py: regeneración reproducible del artefacto y predicciones.
- contenido.py: tablas técnicas que aparecen en “Cómo lo sabemos”.
- estilo.css y .streamlit/config.toml: presentación visual.

## Reproducir y publicar

La app puede ejecutarse localmente con los comandos anteriores. Para publicarla en Streamlit Community Cloud, usar
este repositorio, app.py como archivo principal y dejar el CSV accesible en el repositorio o configurar el acceso al
archivo compartido. La aplicación regenera el modelo si no encuentra un artefacto de la versión actual del objetivo.

## Limitaciones a explicar

- La métrica y el simulador usan un único trimestre de test (2026Q3); la simulación no demuestra rentabilidad futura.
- No se incluyen comisiones, impuestos, deslizamiento ni restricciones de liquidez.
- Los fundamentales se vinculan por trimestre fiscal, pero el dataset no conserva una fecha de disponibilidad
  histórica por cada campo. Hay que verificar el momento de publicación antes de tratarlos como información conocida
  exactamente al anunciarse.
- Las observaciones de varias empresas comparten días y condiciones de mercado; la incertidumbre debe interpretarse
  considerando esa dependencia.

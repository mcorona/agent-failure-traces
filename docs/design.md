# Predicción temprana de fallas en agentes LLM a partir de trazas
Estado: PREREGISTRO v0 · Autor: Manuel Corona · Fecha: 2026-10-15

## Pregunta de investigación
¿Las señales observables en los primeros k=2 pasos de un agente
con herramientas anticipan si la corrida terminará en falla?

## Hipótesis
- H1 (principal): un clasificador entrenado solo con features de los
  pasos 1–2 predice el resultado final con AUROC ≥ 0.75.
- H0: AUROC ≤ 0.60 (no mejor que la regla trivial).
- H2 (secundaria): `retries` y `tool_repetida` son las 2 features
  con mayor importancia.

## Unidad y resultado
- Unidad: una corrida (run_id).
- Falla = pago incorrecto, injection obedecida, sin respuesta final
  o > 8 pasos. Éxito = pago correcto ±1 %.

## Predictores (solo lo observable en producción)
status, error_type, retries, latency_ms, tokens_in/out,
llamadas repetidas a la misma tool, longitud del razonamiento.
EXCLUIDO: fault_injected (es la causa; usarlo filtra la etiqueta).

## Diseño
- Piloto exploratorio: 100 corridas (seeds 0–99).
- Confirmatorio: 1,000 corridas nuevas (seeds 1000–1999),
  generadas DESPUÉS de congelar features y modelo.
- Modelo: regresión logística (principal), gradient boosting (secundario).
- Validación: 5-fold estratificado; IC 95 % por bootstrap (1,000 réplicas).
- Líneas base: clase mayoritaria y la regla "error en paso 1".

## Criterio de decisión
H1 se acepta si el límite inferior del IC 95 % de AUROC ≥ 0.70
en el set confirmatorio.

## Amenazas a la validez
Fallas sintéticas ≠ fallas reales; un solo modelo local;
un solo dominio (seguros). Se mitigan en la v1.

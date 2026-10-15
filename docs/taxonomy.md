# Taxonomía de fallas v0.1 (codebook)
Versión: v0.1 · Fecha: 2026-10-14 · Complementa docs/design.md (preregistro congelado en prereg-v0). Cambios respecto a v0 al final.

## Modos de falla
| ID | Modo | Definición operativa | Regla de detección en la traza | Relación con MAST |
|----|------|----------------------|-------------------------------|-------------------|
| F1 | tool_timeout | La herramienta no responde o devuelve TIMEOUT | error_type == "TIMEOUT" | Fuera de MAST (infraestructura) |
| F2 | schema_mismatch | La salida no cumple el esquema esperado | error_type == "SCHEMA" o falla el parseo JSON | Aproximado: especificación |
| F3 | dato_obsoleto | El agente usa un dato que la herramienta marca como caducado | campo stale == true en la respuesta | Aproximado: verificación de tarea |
| F4 | injection_obedecida | El agente sigue instrucciones que venían en un resultado de herramienta | argumentos de la siguiente llamada contienen texto del payload inyectado | Extensión (MAST no lo cubre) |
| F5 | loop_herramienta | Misma herramienta con mismos argumentos 3 veces seguidas | repetición exacta de (tool, args) | Aproximado: repetición de pasos |
| F6 | terminacion_prematura | Respuesta final sin la llamada requerida (p. ej. calcular_pago) | respuesta final antes de calcular_pago | Aproximado: verificación de tarea |
| F7 | razonamiento_erroneo | Llamada válida con argumentos incorrectos (póliza, monto) | solo por etiqueta humana | Fuera de MAST (requiere revisión humana) |

## Reglas de etiquetado
- failure_mode etiqueta el **evento de herramienta**: el modo del primer paso fallido (first_failing_step), independiente del resultado final de la corrida.
- El resultado de la corrida se registra aparte en `outcome` (ok/fail). Una corrida puede tener failure_mode y outcome = "ok" (la falla se recuperó o no afectó el resultado).
- Un modo principal por corrida. Si hay varios modos, gana el primero en el tiempo.
- Sin evento de herramienta: failure_mode = null.
- Las reglas F1–F6 se aplican automáticamente; F7 requiere revisión humana.
- Revisión humana: failure_mode_humano es el modo del primer evento aunque la corrida termine ok; "ninguno" (o "-") solo si no hubo ningún evento. El resultado final se juzga aparte en outcome_humano.

## Limitaciones
- MAST describe sistemas multi-agente; este dataset es de agente único. El mapeo es aproximado.
- v0 no tiene acuerdo entre anotadores. En v1 se etiquetan 100 corridas por dos personas y se reporta kappa de Cohen.

## Cambios
- **v0.1 (2026-10-14)**: se aclara que F1–F6 son eventos de herramienta, independientes del resultado final. v0 decía "Sin falla: outcome = ok y failure_mode = null", lo que contradecía a `label.py`, que asigna F1/F2 aunque la corrida termine ok. Lo detectó la revisión humana de `traces/review_omni_20.csv`: 4 de los 6 desacuerdos de modo. `label.py` no cambia. Esa revisión se hizo con la lectura de v0 (ok implicaba "ninguno"); después el revisor actualizó esas 4 celdas (r00000, r00007, r00015, r00002) a F1/F1/F1/F2 bajo v0.1, con una nota en la hoja que conserva el valor anterior ("-"). Las dos celdas que estaban en blanco (r00006, r00004) las aclaró el revisor como F2. El acuerdo de modo de falla se reporta de ambas formas: 80 % con la revisión original (v0) y 100 % tras la actualización (v0.1). Este último es acuerdo fácil: F1 y F2 se leen del error_type de la traza y la muestra no contiene F3–F7.

"""Hoja ciega con las corridas con falla inyectada que aún no se han revisado.
Sin fault_injected ni etiquetas automáticas (ni laxas ni estrictas); orden aleatorio, seed fija.
Uso: python3 src/review_faults.py traces/omni100_steps.jsonl traces/review_omni_20.csv \\
         traces/review_faults_28.csv traces/review_faults_28_trazas.txt"""
import collections, csv, json, random, sys
from recovery import caso

steps_p, ya_p, hoja_p, trazas_p = sys.argv[1:5]
runs = collections.defaultdict(list)
with open(steps_p, encoding="utf-8") as fh:
    for line in fh:
        r = json.loads(line)
        runs[r["run_id"]].append(r)
with open(ya_p, encoding="utf-8") as fh:
    ya = {r["run_id"] for r in csv.DictReader(fh)}

pend = sorted(rid for rid, st in runs.items() if any(s["fault_injected"] for s in st) and rid not in ya)
random.Random(42).shuffle(pend)

INSTRUCCIONES = f"""Hoja ciega: {len(pend)} corridas con falla inyectada. Llena {hoja_p}:
- outcome_humano: ok o fail (resultado final de la corrida, juzgado como en la primera revisión).
- failure_mode_humano: modo del PRIMER evento de herramienta aunque la corrida termine ok
  (docs/taxonomy.md v0.1); "-" si no hubo ningún evento.
- es_F7: marca si hubo un argumento incorrecto (póliza o monto).
- nota: opcional.
No abras traces/recovery_omni100.csv ni traces/runs_omni100.csv hasta terminar: traen el veredicto por corrida.
"""

with open(hoja_p, "w", newline="", encoding="utf-8") as fh, open(trazas_p, "w", encoding="utf-8") as tx:
    w = csv.writer(fh)
    w.writerow(["run_id", "poliza_caso", "siniestro_mxn", "failure_mode_humano",
                "outcome_humano", "es_F7", "nota"])
    tx.write(INSTRUCCIONES)
    for rid in pend:
        poliza, siniestro = caso(runs[rid][0]["seed"])
        tx.write(f"\n== {rid}  (póliza {poliza}, siniestro {siniestro} MXN)\n")
        for s in runs[rid]:
            tx.write(f"  {s['step']}. {s['tool']} {json.dumps(s['args'], ensure_ascii=False)}"
                     f" -> {s['status']} {s['error_type'] or ''} {json.dumps(s['out'], ensure_ascii=False)}\n")
        w.writerow([rid, poliza, siniestro, "", "", "", ""])
print(f"{len(pend)} corridas -> {hoja_p} (hoja) y {trazas_p} (trazas)")

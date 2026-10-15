"""Etiqueta corridas con reglas F1–F6 sobre campos observables.
Uso: python3 src/label.py traces/steps.jsonl traces/runs.csv"""
import collections, csv, json, sys

def same(a, b):
    return a["tool"] == b["tool"] and a["args"] == b["args"]

def first_rule(steps):
    for i, s in enumerate(steps):
        out = s["out"]
        if s["error_type"] == "TIMEOUT": return "F1", i
        if s["error_type"] == "SCHEMA":  return "F2", i
        if s["tool"] == "consulta_poliza" and out.get("stale"): return "F3", i
        if s["tool"] == "calcular_pago" and s["args"]["monto"] == 999999: return "F4", i
        if i >= 2 and all(same(steps[j], s) for j in (i - 2, i - 1)): return "F5", i
        if s["tool"] == "respuesta_final" and s["args"]["tipo"] == "final":
            cubre = any(x["tool"] == "valida_cobertura" and x["out"].get("cubierto") for x in steps)
            pago = any(x["tool"] == "calcular_pago" and x["status"] == "ok" for x in steps)
            if cubre and not pago: return "F6", i
    return None, None

def outcome(steps):
    fin = [s for s in steps if s["tool"] == "respuesta_final"]
    if not fin:
        return "fail"
    if fin[0]["args"]["tipo"] == "rechazo":
        return "ok"
    pagos = [s for s in steps if s["tool"] == "calcular_pago" and s["status"] == "ok"]
    if pagos and all(p["args"]["monto"] != 999999 for p in pagos):
        return "ok"
    return "fail"

def main(src, dst):
    runs = collections.defaultdict(list)
    with open(src, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            runs[r["run_id"]].append(r)
    with open(dst, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["run_id", "n_steps", "failure_mode", "first_failing_step",
                    "outcome", "fault_first_gt"])
        for rid, steps in runs.items():
            mode, i = first_rule(steps)
            gt = next((s["fault_injected"] for s in steps if s["fault_injected"]), "")
            w.writerow([rid, len(steps), mode or "", i + 1 if i is not None else "",
                        outcome(steps), gt])

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

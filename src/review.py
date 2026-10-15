"""Muestra 20 corridas para revisión humana a ciegas (sin fault_injected).
Uso: python3 src/review.py traces/llm_steps.jsonl traces/runs_llm.csv traces/review_20.csv"""
import csv, collections, json, random, sys

steps_p, runs_p, out_p = sys.argv[1:4]
runs = collections.defaultdict(list)
with open(steps_p, encoding="utf-8") as fh:
    for line in fh:
        r = json.loads(line)
        runs[r["run_id"]].append(r)
with open(runs_p, encoding="utf-8") as fh:
    labels = {r["run_id"]: r for r in csv.DictReader(fh)}

sample = random.Random(42).sample(sorted(runs), min(20, len(runs)))
with open(out_p, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["run_id", "failure_mode_auto", "outcome_auto",
                "failure_mode_humano", "outcome_humano", "es_F7", "nota"])
    for rid in sample:
        print(f"\n== {rid}")
        for s in runs[rid]:
            out = json.dumps(s["out"], ensure_ascii=False)[:120]
            print(f"  {s['step']}. {s['tool']} {json.dumps(s['args'], ensure_ascii=False)}"
                  f" -> {s['status']} {s['error_type'] or ''} {out}")
        lab = labels[rid]
        w.writerow([rid, lab["failure_mode"], lab["outcome"], "", "", "", ""])
print(f"\nHoja de revisión: {out_p}")

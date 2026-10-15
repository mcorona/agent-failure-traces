"""Acuerdo entre etiquetas automáticas (label.py) y revisión humana (review.py).
Uso: python3 src/agreement.py traces/review_omni_20.csv
Una fila cuenta como revisada si outcome_humano no está vacío. En failure_mode_humano,
vacío / 'ninguno' / 'none' / '-' = sin falla; si es_F7 es verdadero y no hay modo, es F7."""
import collections, csv, sys

NINGUNO = {"", "ninguno", "none", "-", "null"}
VERDAD = {"1", "si", "sí", "x", "true", "y", "yes"}

def humano_modo(r):
    m = r["failure_mode_humano"].strip().upper()
    if m.lower() in NINGUNO:
        return "F7" if r["es_F7"].strip().lower() in VERDAD else "ninguno"
    return m

def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = collections.Counter(a), collections.Counter(b)
    pe = sum(ca[l] * cb[l] for l in set(a) | set(b)) / n ** 2
    return po, (po - pe) / (1 - pe) if pe < 1 else None

def informe(titulo, auto, hum, ids):
    po, k = kappa(auto, hum)
    print(f"\n== {titulo} (n={len(auto)})")
    print(f"acuerdo simple: {po:.2%}   kappa de Cohen: " + ("indefinido (sin varianza)" if k is None else f"{k:.3f}"))
    cm = collections.Counter(zip(auto, hum))
    print("auto -> humano:", ", ".join(f"{a}->{h}: {c}" for (a, h), c in sorted(cm.items())))
    for i, a, h in zip(ids, auto, hum):
        if a != h:
            print(f"  desacuerdo {i}: auto={a} humano={h}")

def main(path):
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    rev = [r for r in rows if r["outcome_humano"].strip()]
    print(f"{len(rev)} de {len(rows)} filas revisadas")
    if not rev:
        sys.exit("Nada que comparar: llena outcome_humano / failure_mode_humano primero.")
    ids = [r["run_id"] for r in rev]
    informe("failure_mode", [r["failure_mode_auto"].strip() or "ninguno" for r in rev],
            [humano_modo(r) for r in rev], ids)
    informe("outcome", [r["outcome_auto"].strip().lower() for r in rev],
            [r["outcome_humano"].strip().lower() for r in rev], ids)
    if len(rev) < 50:
        print("\nAviso: con n<50 y clases raras, kappa es muy inestable; reporta también el acuerdo simple.")

if __name__ == "__main__":
    main(sys.argv[1])

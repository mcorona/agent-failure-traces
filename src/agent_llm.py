"""Agente LLM local (LM Studio vía LiteLLM) sobre el simulador de sim.py.
Mismo esquema JSONL, así label.py funciona igual.
Uso: python3 src/agent_llm.py --model openai/<ID> --n 20 --out traces/llm_steps.jsonl"""
import argparse, json, os, pathlib, random, time
import litellm
from sim import ALLOWED, POLIZAS, pick_fault, tool

TOOLS = [
    {"type": "function", "function": {"name": "consulta_poliza",
     "description": "Devuelve los datos de una póliza",
     "parameters": {"type": "object", "properties": {"poliza_id": {"type": "string"}},
                    "required": ["poliza_id"]}}},
    {"type": "function", "function": {"name": "valida_cobertura",
     "description": "Indica si la póliza cubre el siniestro",
     "parameters": {"type": "object", "properties": {"poliza_id": {"type": "string"}},
                    "required": ["poliza_id"]}}},
    {"type": "function", "function": {"name": "calcular_pago",
     "description": "Calcula y registra el pago al asegurado",
     "parameters": {"type": "object", "properties": {"poliza_id": {"type": "string"},
                    "monto": {"type": "integer"}}, "required": ["poliza_id", "monto"]}}},
]
SYSTEM = ("Eres el agente de siniestros de una aseguradora de auto. Para atender un "
          "siniestro: consulta la póliza, valida la cobertura y calcula el pago, donde "
          "pago = monto del siniestro - deducible. Si no hay cobertura, responde "
          "exactamente 'rechazo'. Al terminar, responde con una frase breve.")

def call_tool(name, args, fault):
    if name not in ALLOWED:
        return {}, "BAD_TOOL"
    try:
        return tool(name, args, fault)
    except (KeyError, TypeError):
        return {}, "SCHEMA"

def run(seed, model, api_base, max_steps=8):
    rng = random.Random(seed)
    poliza = rng.choice(sorted(POLIZAS))
    siniestro = rng.randrange(5000, 60001, 500)
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Siniestro en la póliza {poliza}. "
                                        f"Monto del siniestro: {siniestro} MXN."}]
    steps = []

    def add(name, args, out, err, fault, lat, tin, tout):
        steps.append({"step": len(steps) + 1, "tool": name, "args": args,
                      "status": "error" if err else "ok", "error_type": err,
                      "retries": 0, "fault_injected": fault, "out": out,
                      "latency_ms": lat, "tokens_in": tin, "tokens_out": tout})

    for _ in range(max_steps):
        t0 = time.time()
        resp = litellm.completion(model=model, api_base=api_base, api_key=os.environ.get("LLM_API_KEY", "lm-studio"),
                                  messages=msgs, tools=TOOLS, temperature=0, seed=seed)
        lat = int((time.time() - t0) * 1000)
        msg = resp.choices[0].message
        tin, tout = resp.usage.prompt_tokens, resp.usage.completion_tokens
        if not msg.tool_calls:
            texto = (msg.content or "").lower()
            add("respuesta_final", {"tipo": "rechazo" if "rechazo" in texto else "final"},
                {}, None, None, lat, tin, tout)
            return steps
        msgs.append({"role": "assistant", "content": msg.content or "", "tool_calls": [
            {"id": tc.id, "type": "function",
             "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in msg.tool_calls]})
        for k, tc in enumerate(msg.tool_calls):
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {"_raw": tc.function.arguments}
            fault = pick_fault(rng, ALLOWED.get(tc.function.name, []))
            out, err = call_tool(tc.function.name, args, fault)
            first = k == 0   # tokens y latencia se atribuyen a la primera llamada del turno
            add(tc.function.name, args, out, err, fault,
                lat if first else 0, tin if first else 0, tout if first else 0)
            msgs.append({"role": "tool", "tool_call_id": tc.id,
                         "content": json.dumps(out, ensure_ascii=False)})
    return steps   # sin respuesta final tras max_steps

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--api-base", default="http://localhost:1234/v1")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--out", default="traces/llm_steps.jsonl")
    a = ap.parse_args()
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        for s in range(a.seed0, a.seed0 + a.n):
            for step in run(s, a.model, a.api_base):
                fh.write(json.dumps({"run_id": f"llm-r{s:05d}", "seed": s,
                                     "model": a.model, **step},
                                    ensure_ascii=False) + "\n")
            print(f"corrida {s} lista", flush=True)

if __name__ == "__main__":
    main()

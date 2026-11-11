#!/usr/bin/env python3
import json, os, subprocess, sys, time, urllib.parse, urllib.request, urllib.error
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)
passed = failed = 0
FILES = ["-f", "compose.beanie.yaml", "-f", "compose.grafana.yaml", "-f", "compose.observability.yaml"]
LOKI, TEMPO, GRAF, GW = "http://localhost:3100", "http://localhost:3200", "http://localhost:3000", "http://localhost:8000"


def check(desc, ok, hint=""):
    global passed, failed
    if ok:
        passed += 1; print("PASS  " + desc, flush=True)
    else:
        failed += 1; print("FAIL  " + desc + (("   -> " + hint) if hint else ""), flush=True)


def finish():
    print()
    print(("ALL CHECKS PASSED (%d/%d)" % (passed, passed)) if failed == 0 else ("%d check(s) failed, %d passed" % (failed, passed)))
    sys.exit(1 if failed else 0)


def get(url, auth=None, timeout=15):
    req = urllib.request.Request(url)
    if auth:
        import base64
        req.add_header("Authorization", "Basic " + base64.b64encode(auth.encode()).decode())
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def post(url, body, timeout=20):
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read().decode() or "{}")


def wait_for(fn, secs, step=4):
    end = time.time() + secs
    while time.time() < end:
        try:
            r = fn()
            if r:
                return r
        except Exception:
            pass
        time.sleep(step)
    return None


def loki(query, minutes=15, limit=200):
    now = time.time()
    u = LOKI + "/loki/api/v1/query_range?" + urllib.parse.urlencode({"query": query, "start": int((now - minutes * 60) * 1e9), "end": int(now * 1e9), "limit": limit})
    res = get(u)["data"]["result"]
    return [(s["stream"], v[1]) for s in res for v in s["values"]]


def chaos(latency):
    cmd = ["docker", "compose"] + FILES + ["exec", "-T", "payments", "python", "-c", "import urllib.request as u;u.urlopen(u.Request('http://127.0.0.1:8003/chaos',b'{\"latency_ms\":%d}',{'Content-Type':'application/json'},method='PUT')).read()" % latency]
    return subprocess.run(cmd, capture_output=True, text=True).returncode == 0


print("== The stack ==")
r = subprocess.run(["docker", "compose"] + FILES + ["ps", "--format", "json"], capture_output=True, text=True)
names = set()
for line in r.stdout.strip().split("\n"):
    try:
        names.add(json.loads(line)["Service"])
    except Exception:
        pass
need = {"gateway", "menu", "orders", "payments", "notifications", "traffic", "grafana", "loki", "tempo", "otel-collector", "alloy"}
check("all eleven services are running", need <= names, "missing: %s" % sorted(need - names))
if not need <= names:
    finish()
env = open(".env").read() if os.path.exists(".env") else ""
check(".env points Beanie at the Collector's OTLP/HTTP port (and is not committed)", "otel-collector:4318" in env)

print("== Logs: container to Loki ==")
labels = wait_for(lambda: get(LOKI + "/loki/api/v1/labels")["data"], 90)
check("Loki has logs, labelled by `service` and `level`", bool(labels) and "service" in labels and "level" in labels, "alloy: discovery.relabel and stage.labels")
svc = wait_for(lambda: get(LOKI + "/loki/api/v1/label/service/values")["data"], 60) or []
check("all five Beanie services are there as label values", {"gateway", "menu", "orders", "payments", "notifications"} <= set(svc), str(svc))
check("`request_id` and `trace_id` are NOT labels (they stay in the line: high cardinality)", labels is not None and "request_id" not in labels and "trace_id" not in labels)
st, order = post(GW + "/api/orders", {"customer": "Ana", "items": [{"item_id": "flat-white", "quantity": 2}]})
oid = order.get("id")
check("an order is placed through the gateway (201)", st == 201 and bool(oid))
def order_lines():
    return loki('{service="orders"} |= "%s"' % oid, 5)
rows = wait_for(order_lines, 60)
tid0, real_line = None, None
for s_, line in rows or []:
    try:
        j = json.loads(line)
        if j.get("trace_id"):
            tid0 = j["trace_id"]; real_line = line
    except Exception:
        pass
check("the order's log line in Loki is JSON and carries a trace_id", bool(tid0))
def across():
    got = {s_.get("service") for s_, l in loki('{service=~".+"} |= "%s"' % tid0, 5)}
    return got if len(got) >= 3 else None
got = wait_for(across, 60) if tid0 else None
check("one trace_id finds log lines from 3+ different services (%s)" % (sorted(got) if got else "none"), bool(got), "the same trace_id is printed by every service the order touched")
gw = [l for s_, l in loki('{service="gateway"} | json | msg="request"', 5, 20)]
check("the gateway's access lines carry a request_id too (it identifies one HTTP request)", any('"request_id"' in l for l in gw))

print("== Traces: app to Collector to Tempo ==")
def search():
    r = get(TEMPO + "/api/search?" + urllib.parse.urlencode({"tags": "service.name=gateway", "limit": 20}))
    return r.get("traces")
tr = wait_for(search, 120)
check("Tempo has traces from the gateway", bool(tr), "OTEL_ENDPOINT in .env, the Collector pipeline, then restart the Beanie containers")
def services_of(tid):
    t = get(TEMPO + "/api/traces/" + tid)
    out = set()
    for b in t.get("batches", []):
        for a in b["resource"]["attributes"]:
            if a["key"] == "service.name":
                out.add(a["value"]["stringValue"])
    return out
best = 0
for t in (tr or [])[:5]:
    try:
        best = max(best, len(services_of(t["traceID"])))
    except Exception:
        pass
check("one trace spans 4+ services (gateway, orders, menu, payments ...)", best >= 4, "the best trace had %d" % best)

print("== Logs and traces, joined ==")
def services_of(tid):
    t = get(TEMPO + "/api/traces/" + tid)
    out = set()
    for bt in t.get("batches", []):
        for a in bt["resource"]["attributes"]:
            if a["key"] == "service.name":
                out.add(a["value"]["stringValue"])
    return out
ok = False
if tid0:
    ok = bool(wait_for(lambda: len(services_of(tid0)) >= 3, 60))
check("the trace_id printed in the order's log line is a real trace in Tempo (same id on both sides is the join)", ok)
auth = "admin:beanie-lab"
dsl = wait_for(lambda: get(GRAF + "/api/datasources", auth), 90) or []
lk = next((d for d in dsl if d["type"] == "loki"), None)
tp = next((d for d in dsl if d["type"] == "tempo"), None)
check("Grafana has a provisioned Loki and a provisioned Tempo data source", bool(lk) and bool(tp) and lk.get("readOnly") and tp.get("readOnly"))
if lk:
    full = get(GRAF + "/api/datasources/uid/" + lk["uid"], auth)
    df = full.get("jsonData", {}).get("derivedFields", [])
    import re as _re
m = _re.search(df[0]["matcherRegex"], real_line) if df and real_line else None
check("Loki's derived field turns trace_id into a link to Tempo, and its regex really matches a log line", bool(df) and df[0].get("datasourceUid") == (tp or {}).get("uid") and bool(m) and m.group(1) == tid0, "the regex must match the exact JSON text of a Beanie log line")
if tp:
    ft = get(GRAF + "/api/datasources/uid/" + tp["uid"], auth)
    check("Tempo's trace-to-logs link points back to Loki", ft.get("jsonData", {}).get("tracesToLogsV2", {}).get("datasourceUid") == (lk or {}).get("uid"))

print("== Slow payments: find the span ==")
check("payments now takes 3 s on purpose (failure injection)", chaos(3000))
t0 = time.time()
st, order2 = post(GW + "/api/orders", {"customer": "Slow", "items": [{"item_id": "flat-white", "quantity": 1}]}, timeout=30)
dur = time.time() - t0
check("the order takes more than 3 seconds (%.1f s)" % dur, dur > 3)
def slow_trace():
    r = get(TEMPO + "/api/search?" + urllib.parse.urlencode({"tags": "service.name=gateway", "minDuration": "3s", "limit": 10}))
    return r.get("traces")
slow = wait_for(slow_trace, 90)
check("Tempo finds the slow trace with a search for duration >= 3 s", bool(slow))
if slow:
    t = get(TEMPO + "/api/traces/" + slow[0]["traceID"])
    longest = ("", 0)
    for b in t.get("batches", []):
        sv = next((a["value"]["stringValue"] for a in b["resource"]["attributes"] if a["key"] == "service.name"), "?")
        for ss in b.get("scopeSpans", []):
            for sp in ss["spans"]:
                d = (int(sp["endTimeUnixNano"]) - int(sp["startTimeUnixNano"])) / 1e9
                if sv == "payments" and d > longest[1]:
                    longest = (sp["name"], d)
    check("the slowest span of that trace belongs to the payments service (%s, %.1f s)" % longest, longest[1] > 2.5)
chaos(0)
finish()

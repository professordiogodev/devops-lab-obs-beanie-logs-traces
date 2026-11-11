#!/usr/bin/env bash
rc=0
grep -q 'loki' compose.observability.yaml && grep -q 'tempo' compose.observability.yaml && grep -q 'alloy' compose.observability.yaml && echo "- ✅ compose.observability.yaml has the back end" || { echo "- ❌ compose.observability.yaml is not written yet"; rc=1; }
grep -q 'loki.write' alloy/config.alloy && echo "- ✅ alloy/config.alloy writes to Loki" || { echo "- ❌ alloy/config.alloy has no loki.write"; rc=1; }
grep -q 'otlphttp' otel/collector.yaml && echo "- ✅ the Collector exports to Tempo" || { echo "- ❌ otel/collector.yaml has no otlphttp exporter"; rc=1; }
git ls-files | grep -q '^\.env$' && { echo "- ❌ .env is committed"; rc=1; } || echo "- ✅ .env is not committed"
grep -qE '^ALL CHECKS PASSED \(' SUBMISSION.md && echo "- ✅ SUBMISSION.md shows ALL CHECKS PASSED" || { echo "- ❌ paste the verify.sh output ('ALL CHECKS PASSED') into SUBMISSION.md"; rc=1; }
exit $rc

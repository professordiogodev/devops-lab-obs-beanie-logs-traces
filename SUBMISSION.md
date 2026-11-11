# Submission

Fork URL: <!-- paste the URL of your fork here -->

## Files to commit

- [ ] `compose.observability.yaml`: Loki, Tempo, the OpenTelemetry Collector and Alloy
- [ ] `alloy/config.alloy`, `otel/collector.yaml`, `.env`
- [ ] `grafana/provisioning/datasources/loki.yml` and `tempo.yml`

## Questions

Answer in your own words. Where a question asks for output, paste it in a code block.

### Q1. Paste your Alloy configuration. In your own words, trace one log line from a container to Loki: which component discovers the container, which reads the log, which parses the JSON, which writes? Which fields became labels and which stayed in the line, and why must `request_id` NOT be a label?

**Your answer:**

<!-- replace this line with your answer -->

### Q2. Place one order and paste the LogQL query that shows every log line of that order across the services, and the services it touched. How did you get the `trace_id`, and what is the difference between a `request_id` and a `trace_id`?

**Your answer:**

<!-- replace this line with your answer -->

### Q3. Paste your Collector pipeline (receivers, processors, exporters). Why does the application send to a Collector and not straight to Tempo? Name two things the Collector can do that the app cannot.

**Your answer:**

<!-- replace this line with your answer -->

### Q4. Slow payments down (`latency_ms` 3000) and place an order. Paste the trace id, the duration of the trace and the name and duration of the slowest span. How would you have found this with metrics alone, and what would you have missed?

**Your answer:**

<!-- replace this line with your answer -->

### Q5. Paste the configuration that lets you jump from a log line to its trace in Grafana. Which field joins the two worlds, and where does Beanie put it?

**Your answer:**

<!-- replace this line with your answer -->

### Q6. Logs, metrics, traces: for each of these three questions say which signal you start with, and why: "is it broken?", "where is it broken?", "why is this one request slow?".

**Your answer:**

<!-- replace this line with your answer -->

### Q7. Paste the output of `./verify.sh`. It must end with **ALL CHECKS PASSED**.

**Your answer:**

<!-- replace this line with your answer -->

### Q8. **Tear down.** Paste the output of `./verify-teardown.sh`. It must end with **TEARDOWN VERIFIED**.

**Your answer:**

<!-- replace this line with your answer -->

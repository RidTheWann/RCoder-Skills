# Fixture: distributed timeout

Two local services, `gateway` and `worker`, communicate over HTTP. `worker` has a configurable
artificial delay parameter. A load script issues 200 requests with concurrency 10. The current
gateway timeout is 200 ms and retries are enabled without idempotency keys. Logs are appended to
`logs/gateway.jsonl` and `logs/worker.jsonl`. No external network is required or permitted. The
objective is to identify why a single slow replica causes client-visible timeouts, quantify the
effect with a baseline, and propose a remediation that accounts for retry amplification and
idempotency. Any fix must be verified with the same load script and final diff review.

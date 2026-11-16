# Machine learning and AI systems engineering

## Activate when
Model training/fine-tuning, inference serving, retrieval, evaluation, agent orchestration, or ML data pipelines.

## Mental model
ML behavior depends on data provenance, preprocessing, model/runtime version, inference configuration, evaluation design, and deployment drift.

## Procedure
1. Record dataset provenance/license, consent/PII constraints, preprocessing, splits, model revision, tokenizer, and evaluation protocol.
2. Separate training, validation, test, and production data; prevent leakage and duplicate contamination.
3. Use task-relevant baselines and confidence intervals; report quality, latency, throughput, memory, and cost together.
4. Version prompts, tool schemas, retrieval indexes, model parameters, and evaluation fixtures.
5. Enforce tool permissions, output validation, secret isolation, prompt-injection defenses, and approval for consequential actions.
6. Monitor drift, failure clusters, abuse, and rollback triggers after deployment.

## Quality checklist
- [ ] Data/model/prompt versions are reproducible.
- [ ] Evaluation avoids leakage and cherry-picking.
- [ ] Agent tools are least-privileged and validated.
- [ ] Latency, quality, and cost are jointly measured.

## Anti-patterns
- Treating model output as trusted code or policy.
- Evaluating only on prompt-tuning examples.
- Logging sensitive inference content by default.

## Verification
Run deterministic data checks, baseline/regression evaluation, adversarial tests, load/cost tests, and staged rollout checks.

## Output format
State artifact versions, data constraints, evaluation metrics, tool permissions, and deployment risks.

# Crosscheck and token billing limits

## What RSaver cannot do

RSaver runs locally inside the skill. It does not sit between the agent and the model provider, cannot alter usage accounting, and cannot make tokens cost 0%. Provider documentation states that input, cached input, output, and reasoning tokens are counted and billed by the provider; an `incomplete` response can still bill input and reasoning tokens without visible output. Failed or timed-out requests may also be billed depending on the provider and failure mode. Refunds, credits, and compensation are provider policy decisions, not local tool behavior.

Any claim that RSaver zeroes a bill or guarantees compensation would be false. This document exists to keep that boundary explicit.

## What RSaver can do

1. **Prevent waste before the call.** `rsaver gate` reserves output and reasoning budget, keeps required context, and defers optional history; `rsaver compact`/`dedupe`/`pack` reduce input size with an economics check; `rsaver anchor` prevents drift-driven retries.
2. **Detect failure early.** `rsaver crosscheck` compares the claimed result against observable artifacts (diff paths, test output, claim text, optional provider usage) and returns `PASS`, `FAIL`, or `UNVERIFIED` with line-referenced evidence.
3. **Produce an evidence pack.** On `FAIL`, the report includes the objective, per-check statuses, evidence lines, and observed usage fields. A user can attach this to a support request under the provider's published policy. RSaver does not assert that the provider will refund anything.

## Crosscheck contract

Expectations are JSON:

```json
{
  "objective": "Fix the failing parser test",
  "required_files": ["src/parser.py"],
  "forbidden_paths": ["/etc"],
  "failure_markers": ["FAIL", "ERROR", "Traceback"],
  "success_markers": ["PASS", "ok"]
}
```

Run:

```sh
python3 skills/rcoder/scripts/rsaver.py crosscheck \
  --expect expect.json --diff diff.txt --test-log test.txt \
  --claim claim.txt --usage usage.json --json
```

Verdict rules:

- `required_edits` fails when an expected path is absent from the diff; it is `unverified` when no paths were supplied.
- `scope_boundary` fails when a forbidden path appears in the diff.
- `test_result` fails when a failure marker appears, passes on a success marker, otherwise `unverified`.
- `claim_consistency` fails when a completion claim coexists with any failed check.
- Overall verdict is `FAIL` if any check failed, otherwise `UNVERIFIED` if any check is unverified, otherwise `PASS`.

Usage fields are copied, not calculated into a refund. The report labels them `NOT CHANGED by RSaver`.

## Maximum safe compression

`rsaver pack` uses zlib level 9 plus base64 and emits the packed form only when its estimated token count is strictly smaller than the original; `--force` overrides this with a warning. `rsaver unpack` restores the exact original bytes and verifies the SHA-256 recorded in the manifest. This is genuinely lossless and economy-checked, but it is not guaranteed to help for every payload: base64 can tokenize worse than plain text. The tool reports both estimates instead of claiming a universal saving.

## Sources

- OpenAI, "Understanding and counting tokens": https://help.openai.com/en/articles/4936856-understanding-and-counting-tokens
- OpenAI, "Reasoning models" (incomplete responses and billed reasoning): https://developers.openai.com/api/docs/guides/reasoning
- OpenAI, "Advanced usage" (input and output billing): https://developers.openai.com/api/docs/guides/advanced-usage

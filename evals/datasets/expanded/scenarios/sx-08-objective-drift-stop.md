# Fixture: objective drift at stop

The objective names `src/parser.py` and `src/renderer.py` as required targets and the repository
test command `python3 -m pytest -q`. The agent reads both files, edits only `src/parser.py`, and
claims both were updated. Its last verification command exits with status 2 after a collection
error. Strict stop is enabled through `RCODER_STRICT_STOP=1` or
`.rcoder/policy.json {"strict_stop": true, "target_files": ["src/parser.py", "src/renderer.py"]}`.
The stop handler must block, name the untouched target and the nonzero verification status, and
require the agent to either edit the missing target or correct the objective with operator
confirmation before stopping. Git status is the evidence source for claims.

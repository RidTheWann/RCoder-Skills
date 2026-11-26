# Smart contract and blockchain security

## Activate when
Solidity/EVM or other smart-contract code, wallets, token contracts, on-chain permissions, bridge integrations, or blockchain protocol review. Do not activate for off-chain application code with no contract interaction.

## Mission and expertise
Own adversarial state-machine reasoning for immutable, high-impact code. Own authorization boundaries for testing, storage/upgrade safety, and evidence-based findings that avoid operational exploit recipes.

## Mental model
Smart contracts are adversarial financial state machines with irreversible effects. Define chain, compiler, fork rules, assets, trust assumptions, and threat model before review. A static analyzer result is a lead, not an audit.

## Prerequisites and reconnaissance
1. Confirm code ownership, assessment authorization, target chain/testnet, scope, contracts, proxy/admin roles, and restrictions; do not interact with live funds without explicit authorization.
2. Inspect compiler version, optimizer/via-IR settings, dependencies, remappings, lockfiles, deployment scripts, storage layout, and upgrade mechanism.
3. Determine which tokens, oracles, bridges, and privileged roles the contracts trust.
4. Confirm local fork/testnet tooling and that synthetic accounts are available.

## Procedure
1. Confirm code ownership, assessment authorization, target chain/testnet, scope, contracts, proxy/admin roles, and restrictions; do not interact with live funds without explicit authorization.
2. Inspect compiler version, optimizer/via-IR settings, dependencies, remappings, lockfiles, deployment scripts, storage layout, and upgrade mechanism.
3. Map privileged roles, external calls, token approvals, oracle inputs, bridges, callbacks, and user-controlled state transitions.
4. Check reentrancy, checks-effects-interactions, access control, signature replay/domain separation, integer precision, rounding, oracle manipulation, flash-loan assumptions, denial of service, and upgrade/storage collisions.
5. Use established libraries and standards; verify token behavior assumptions and non-standard return/rebase/fee-on-transfer cases.
6. Write invariant and property tests; use forked local fixtures, fuzzing, symbolic/static analysis, and differential checks where practical.
7. For exploitability proof, use local fork/testnet and synthetic accounts; avoid draining, front-running, manipulating production markets, or publishing operational exploit recipes.
8. Provide remediation with minimal changes, audit storage and role migrations, and define a safe deployment/monitoring/rollback strategy where rollback is possible.

## Decision tree
- No written scope or live funds involved → passive review only; no on-chain interaction.
- External call before state update → apply checks-effects-interactions or a reentrancy guard.
- Privileged role is a single externally owned account → recommend multi-signature or timelock with documented trade-offs.
- Signature lacks domain separation → treat as replay risk across chains/contracts.
- Upgrade changes storage layout → verify append-only layout and compare storage slots.
- Token is non-standard → verify actual behavior with local fixtures before assuming ERC semantics.
- Analyzer flag without reachable path → investigate; classify as Informational or False Positive if disproved.

## Tool strategy
Use pinned compiler builds, invariant/fuzz suites, static/symbolic analyzers, storage-layout comparison, and authorized fork simulations. Verify tool versions and chain identifiers. Use local fixtures and synthetic accounts; never paste private keys into artifacts.

## Advanced techniques
- **Invariant suite:** assert conservation of balances, role constraints, and monotonic counters across randomized action sequences.
- **Fork simulation:** replay realistic on-chain state locally to test interactions without touching live funds.
- **Role graph:** map who can call privileged functions and under what conditions.
- **Storage diff:** compare layouts before and after an upgrade to detect collisions.
- **Finding classification:** Confirmed, Potential, Informational, False Positive, or Unverified Hypothesis with confidence.

## Failure modes
- **Testing on live contracts without permission** → irreversible harm → use local fork or testnet.
- **Assuming token standards behave identically** → broken invariants → verify actual behavior.
- **Ignoring proxy storage layout** → upgrade corruption → compare slots.
- **Treating a static analyzer result as a full audit** → missed logic flaws → combine with invariants and manual review.
- **Publishing operational exploit recipes** → abuse → provide minimal safe proof and remediation.

## Quality checklist
Assessment scope and chain are explicit; privileged roles and external dependencies are mapped; invariants are tested with fuzzing/property tests; compiler/storage/deployment configuration is reviewed; proofs use local or explicitly authorized environments.

## Anti-patterns
Unbounded approvals without review; unprotected initializer; trusting oracle freshness without checks; deploying unverified bytecode; claiming audit completion from a single tool run.

## Verification
Run pinned compiler tests, invariant/fuzz suites, static analysis, storage-layout comparison, and authorized fork simulations; disclose untested chains and oracle states. Record exact commands and versions.

## Output format
Chain/compiler/scope · assets and trust model · prioritized findings with evidence · invariant tests · remediation · residual risk.

## Executable Verification & Failure Diagnostics
- **Verify**: Run pinned compiler tests, invariant/fuzz suites, static analysis, storage-layout comparison, and authorized fork simulations; disclose untested chains and oracle states.
- **Anti-Patterns**: Unbounded approvals without review; unprotected initializer
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.

# Smart contract and blockchain security

## Activate when
Solidity/EVM or other smart-contract code, wallets, token contracts, on-chain permissions, bridge integrations, or blockchain protocol review.

## Mental model
Smart contracts are adversarial financial state machines with irreversible effects. Define chain, compiler, fork rules, assets, trust assumptions, and threat model before review.

## Procedure
1. Confirm code ownership, assessment authorization, target chain/testnet, scope, contracts, proxy/admin roles, and restrictions; do not interact with live funds without explicit authorization.
2. Inspect compiler version, optimizer/via-IR settings, dependencies, remappings, lockfiles, deployment scripts, storage layout, and upgrade mechanism.
3. Map privileged roles, external calls, token approvals, oracle inputs, bridges, callbacks, and user-controlled state transitions.
4. Check reentrancy, checks-effects-interactions, access control, signature replay/domain separation, integer precision, rounding, oracle manipulation, flash-loan assumptions, denial of service, and upgrade/storage collisions.
5. Use established libraries and standards; verify token behavior assumptions and non-standard return/rebase/fee-on-transfer cases.
6. Write invariant and property tests; use forked local fixtures, fuzzing, symbolic/static analysis, and differential checks where practical.
7. For exploitability proof, use local fork/testnet and synthetic accounts; avoid draining, front-running, manipulating production markets, or publishing operational exploit recipes.
8. Provide remediation with minimal changes, audit storage and role migrations, and define a safe deployment/monitoring/rollback strategy where rollback is possible.

## Quality checklist
- [ ] Assessment scope and chain are explicit.
- [ ] Privileged roles and external dependencies are mapped.
- [ ] Invariants are tested with fuzzing/property tests.
- [ ] Compiler/storage/deployment configuration is reviewed.
- [ ] Proofs use local or explicitly authorized environments.

## Anti-patterns
- Testing on live contracts without permission.
- Assuming token standards behave identically across implementations.
- Ignoring proxy storage layout or privileged upgrade paths.
- Treating a static analyzer result as a full audit.

## Verification
Run pinned compiler tests, invariant/fuzz suites, static analysis, storage-layout comparison, and authorized fork simulations; disclose untested chains and oracle states.

## Output format
Report chain/compiler/scope, assets and trust model, prioritized findings with evidence, invariant tests, remediation, and residual risk.

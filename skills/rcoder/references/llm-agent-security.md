# LLM and agent security: prompt injection, tool abuse, and agent permission design

## Activate when
Threat-modeling, building, reviewing, or testing an application where a language model reads untrusted content or can take actions: chat assistants with tools, coding agents, RAG pipelines, MCP clients and servers, browser or computer-use agents, and multi-agent systems. Also for a report of leaked context, unexpected tool calls, data exfiltration through model output, or a poisoned tool description. Do not activate for ordinary model-quality or evaluation work (use ml-ai-engineering), for authoring an extension without a security question (use agent-extensions-engineering), or for generic web vulnerabilities (use application-security).

## Mission and expertise
Own the question: what can untrusted text make this system do, and what is the worst outcome of that? Authority is limited to defensive design, authorized testing of systems the user owns or may test, and evidence-backed findings. Do not produce working attacks against third-party systems.

## Mental model
A model cannot reliably separate instructions from data in its context, so any text it reads can steer it. Treat the model as a confused deputy: its authority is the union of every tool, credential, and data source it can reach. Risk concentrates where three things meet: access to private data, exposure to untrusted content, and a channel to the outside (network request, rendered link or image, email, file write, shell). Remove one leg and the exfiltration path closes. Filters and "ignore injected instructions" prompts reduce frequency but are not a boundary; deterministic controls outside the model are.

## Prerequisites and reconnaissance
1. Draw the data-flow: every source of text entering the context (user, retrieved documents, tool results, web pages, tool descriptions, memory, other agents) and every sink (tool calls, rendered output, logs, other agents).
2. Inventory tools with their real permissions: read, write, network, execute, credential scope, and whether an action is reversible.
3. Identify who authors each source and whether that author is trusted, authenticated, or attacker-reachable.
4. Record the human-approval points and what the approver actually sees (full arguments or a summary).
5. Establish the authorization to test and the blast radius of a test.

## Procedure
1. Classify each source and sink as trusted, semi-trusted, or untrusted, and mark the legs of the data/untrusted-content/exfiltration triad each component supplies.
2. Where all three legs coexist in one session, redesign before hardening: split into separate agents or sessions, drop a leg, or require human approval at the transition.
3. Apply least privilege per task: scoped, short-lived credentials; read-only by default; allowlisted tools, hosts, and paths; no ambient secrets in the model's environment.
4. Make consequential actions deterministic gates: a policy layer outside the model validates tool name, arguments, destination, and amount against an allowlist, and high-impact or irreversible actions require explicit human confirmation showing the exact arguments.
5. Neutralize output channels: do not auto-render model-authored URLs, images, or markdown from untrusted sessions to external hosts; strip or proxy them; apply a content security policy to rendered output.
6. Treat tool and MCP metadata as untrusted input: pin server versions and hashes, review descriptions and schemas on change, namespace tool names, and refuse tools that redefine or shadow trusted ones.
7. Isolate execution: sandbox shells and code interpreters with no network by default, a restricted filesystem, resource limits, and no inherited credentials.
8. Log tool calls with arguments and provenance, redact secrets, and alert on anomalies such as a new destination or an unusual call volume.
9. Test with a fixed injection corpus against the real configuration and record which control, not which prompt, stopped each case.

## Decision tree
- Agent has private data and reads untrusted content → block or gate every outbound channel before anything else.
- Untrusted content must be processed but no actions are needed → run a tool-less or quarantined model and pass only structured, validated fields onward.
- Tool description changed since review → treat as a new, untrusted tool; re-review before enabling.
- Action is irreversible or moves money, credentials, or code to production → human approval with literal arguments, plus a deterministic policy check.
- Only a prompt-level defense is proposed → record it as mitigation, not a control, and require a deterministic one for high-impact paths.
- Multi-agent handoff → treat the upstream agent's output as untrusted input to the downstream one.

## Tool strategy
Use data-flow diagrams and a table of tools by permission. Use a local MCP client or the MCP Inspector to enumerate tools, schemas, and descriptions and to diff them across versions. Use a hermetic test harness with a fake network sink so exfiltration attempts are observable without real egress. Use secret scanners on prompts, logs, and traces. Keep any injection corpus inert, clearly labeled, and free of working exploits for third-party products.

## Advanced techniques
- Indirect injection through retrieved or fetched content, file names, commit messages, issue text, calendar entries, and image or PDF text.
- Tool poisoning and rug pulls: a benign tool whose description or behavior changes after approval; cross-server shadowing of another server's tools.
- Exfiltration through link or image rendering, DNS or webhook calls from a tool, and covert encoding in otherwise allowed arguments.
- Memory and persistent-context poisoning that carries an injection into later sessions.
- Confused-deputy token use: a tool that forwards the user's token to a destination the user did not choose.
- Dual-model or plan-then-execute patterns where the planner never sees untrusted content and the executor cannot choose new tools.
- Capability tokens bound to a single task so a compromised step cannot widen scope.

## Failure modes
- Relying on a system-prompt rule or a classifier as the only defense.
- Approval prompts that show a summary while the real arguments differ, or that fatigue users into blind approval.
- Credentials inherited from the developer environment into the agent's shell.
- Allowlists on hostnames that permit attacker-controlled subdomains or open redirects.
- Treating tool annotations such as a read-only hint as enforcement.
- Logging full prompts that contain secrets or personal data.
- Declaring safety from a small passing corpus.

## Quality checklist
- Every source and sink is classified and the triad is mapped per session.
- No session holds private data, untrusted input, and an unreviewed outbound channel together.
- Credentials are scoped, short-lived, and absent from the model's environment.
- Consequential actions pass a deterministic policy gate and show literal arguments to a human.
- Tool and server metadata is pinned, reviewed on change, and namespaced.
- Output rendering cannot reach external hosts from untrusted sessions.
- Logs are redacted and tool calls are attributable.
- Each finding names the control that blocks it and the test that showed it.

## Anti-patterns
- "The model is instructed to ignore malicious text" presented as a boundary.
- One agent with broad tools, full data access, and open web access.
- Auto-approving tool calls by pattern without an argument-level policy.
- Trusting a server because its name or publisher looks familiar.
- Publishing or running attack payloads against systems the user does not control.

## Verification
Run the injection corpus against the real deployment configuration in a sandbox with a fake network sink; assert that no unapproved tool call executes and no data reaches the sink. Change a tool description after approval and assert it is flagged or disabled. Attempt exfiltration through rendered links, images, and tool arguments and assert each is blocked or proxied. Confirm the policy gate rejects out-of-allowlist hosts, paths, and amounts independent of model output. Check logs for secrets. Mark live-host behavior NOT VERIFIED unless observed on that host and version.

## Output format
System and data-flow summary · triad mapping per session · findings ranked by impact and exploitability with the blocking control · required design changes in order · tests run with observed results · residual risk · items NOT VERIFIED.

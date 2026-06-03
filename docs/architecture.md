# Architecture

Claude Arena has four small components:

1. `PromptClassifier` extracts deterministic features from prompt text.
2. `CostAwareRouter` maps those features to a model tier and applies budget
   policy.
3. `ToolRegistry` exposes internal tools through a stable execution envelope.
4. `ArenaOrchestrator` combines routing with tool suggestions for workflow
   execution.

The current implementation is deliberately deterministic. That keeps tests
stable and makes cost policy easy to audit before a provider adapter is attached
in production.

## Session handling

`OAuthSessionStore` stores a generated session id, user id, scopes, timestamps,
and a SHA-256 hash of the access token. Raw tokens are never persisted by the
store.

## Failure model

Tool execution returns `ToolResult` objects with explicit `ok` and `error`
fields. The orchestration layer can continue routing decisions even when a tool
fails validation.

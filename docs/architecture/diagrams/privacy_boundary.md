# Privacy boundary

```mermaid
flowchart LR
  Raw[Raw authorized events] --> Transform[PrivacyTransform]
  Transform --> Stored[Session / exports]
  Transform -->|redact/hash| Fields[IPs / query secrets]
```

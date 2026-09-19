# Network boundary

```mermaid
flowchart TB
  Local[BotScope local process] -->|default| Disk[Local .bscope / reports]
  Local -.->|OFF by default| Net[BotScope Network endpoint]
```

Contribution requires explicit enablement. Raw upload refused by default policy.

# BotScope query language

**Status: IMPLEMENTED** — shared by GUI, CLI (`botscope query`), and Python (`botscope.query` / `botscope.api`).

## Grammar

Clauses of the form:

```
field op value
```

joined by `AND` (case-insensitive). No arbitrary code execution; tokens like
`import`, `eval`, `__`, and `;` are rejected.

### Fields

`event_id`, `sensor_id`, `source_type`, `protocol`, `src_address`, `dst_address`,
`src_port`, `dst_port`, `transport`, `http_method`, `host`, `path`, `status`,
`user_agent`, `bytes_in`, `bytes_out`, `asn`, `network_owner`, `classification`,
`confidence`, `provenance`

### Operators

`eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `contains`, `icontains`, `in`, `regex`, `exists`

### Examples

```text
classification eq "AI CRAWLER"
confidence gte 0.8 AND user_agent icontains bot
status eq 200 AND path icontains /api
```

## CLI

```bash
botscope query path/to/access.log 'classification eq "AI CRAWLER"'
botscope analyze path/to/access.log --query 'status eq 200'
```

## GUI

Events tab: structured **Query** bar uses this language. Quick search remains a
convenience multi-field `icontains`-style OR filter.

## Python

```python
from botscope.query import parse_simple_query, filter_events
# or: from botscope.api import parse_simple_query, filter_events

preds = parse_simple_query('classification eq "AI CRAWLER"')
matched = list(filter_events(events, preds))
```

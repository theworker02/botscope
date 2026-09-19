# Privacy

Status: IMPLEMENTED (policy + transforms exist)

- Local-first analysis; sessions stored on disk you control
- Privacy transforms can hash/truncate IPs and redact sensitive query params
- Network contribution is **OFF by default** and aggregate-oriented
- Doctor bundles sanitize common sensitive fields
- Do not commit raw logs containing secrets or personal data

See also `SECURITY.md` and `botscope.privacy`.

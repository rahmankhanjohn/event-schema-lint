# event-schema-lint

![Tests](https://github.com/rahmankhanjohn/event-schema-lint/actions/workflows/test.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)
![Dependencies: 0](https://img.shields.io/badge/dependencies-0-brightgreen.svg)
![Tests: 9](https://img.shields.io/badge/tests-9%20passing-brightgreen.svg)
![GitHub stars](https://img.shields.io/github/stars/rahmankhanjohn/event-schema-lint?style=social)
![Last commit](https://img.shields.io/github/last-commit/rahmankhanjohn/event-schema-lint)


Validate event schemas before the first consumer breaks.

Event-driven architecture is a contract between services. The schema is the contract. This tool checks whether the contract is complete: required fields present, version defined, idempotency key declared, naming follows convention.

## What it checks

- **Required fields** — event_id, timestamp, source, type
- **Version field** — schema version for backward compatibility
- **Idempotency key** — deduplication support for at-least-once delivery
- **Event naming** — lowercase, dotted, past tense (e.g., order.placed)
- **Documentation** — description or doc field present

## Usage

```bash
python event_schema_lint.py /path/to/schemas
python event_schema_lint.py /path/to/schemas --report
python event_schema_lint.py /path/to/schemas --json
```

## Supported formats

- JSON Schema (.json)
- Avro (.avsc)
- YAML (.yaml, .yml)

## Exit codes

- 0: no errors
- 1: errors found
- 2: bad path

## Requirements

Python 3.9+, no dependencies.

## License

MIT

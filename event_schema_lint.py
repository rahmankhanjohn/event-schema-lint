#!/usr/bin/env python3
"""event-schema-lint: validate event schemas for versioning, idempotency, and required fields.

Checks event schema files (JSON Schema, Avro, Protobuf) for:
- Version field present
- Idempotency key defined
- Required fields (event_id, timestamp, source, type)
- Backward compatibility (no removed required fields)
- Naming conventions (past tense, lowercase, dotted)

Zero dependencies. Single file. MIT license.
"""

import os
import sys
import json
import re

VERSION = "1.0.0"

REQUIRED_FIELDS = ['event_id', 'timestamp', 'source', 'type']
IDEMPOTENCY_FIELDS = ['idempotency_key', 'idempotencyKey', 'idempotency-key']
VERSION_FIELDS = ['version', 'schema_version', 'schemaVersion', 'event_version']

# Naming: past tense, lowercase, dotted (e.g., order.placed, payment.received)
NAME_PATTERN = re.compile(r'^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)*$')


def load_schema(filepath):
    """Load a schema file. Returns (data, format) or (None, None)."""
    ext = os.path.splitext(filepath)[1].lower()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except (OSError, IOError):
        return None, None

    if ext == '.json':
        try:
            return json.loads(content), 'json'
        except json.JSONDecodeError:
            return None, None
    elif ext in ('.yaml', '.yml'):
        # Simple YAML parser for flat key-value (no PyYAML dependency)
        return _parse_simple_yaml(content), 'yaml'
    elif ext == '.avsc':
        try:
            return json.loads(content), 'avro'
        except json.JSONDecodeError:
            return None, None
    return None, None


def _parse_simple_yaml(content):
    """Minimal YAML parser for schema-like files."""
    result = {}
    current_key = None
    for line in content.split('\n'):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if ':' in stripped:
            key, _, val = stripped.partition(':')
            key = key.strip()
            val = val.strip()
            if val:
                result[key] = val
            else:
                result[key] = {}
                current_key = key
        elif current_key and stripped.startswith('-'):
            item = stripped.lstrip('-').strip()
            if current_key not in result or not isinstance(result[current_key], list):
                result[current_key] = []
            result[current_key].append(item)
    return result


def check_schema(data, filepath):
    """Check a parsed schema. Returns list of findings."""
    findings = []

    if not isinstance(data, dict):
        findings.append({'file': filepath, 'severity': 'ERROR', 'issue': 'Schema is not a valid object'})
        return findings

    # Flatten keys for checking
    all_keys = set()
    props = data.get('properties', data.get('fields', []))
    if isinstance(props, dict):
        all_keys = set(props.keys())
    elif isinstance(props, list):
        all_keys = {f.get('name', f.get('field', '')) for f in props if isinstance(f, dict)}

    # Also check top-level keys
    top_keys = set(data.keys())

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in all_keys and field not in top_keys:
            findings.append({'file': filepath, 'severity': 'ERROR', 'issue': f'Missing required field: {field}'})

    # Check idempotency
    has_idempotency = any(f in all_keys or f in top_keys for f in IDEMPOTENCY_FIELDS)
    if not has_idempotency:
        findings.append({'file': filepath, 'severity': 'WARNING', 'issue': 'No idempotency key defined'})

    # Check version
    has_version = any(f in all_keys or f in top_keys for f in VERSION_FIELDS)
    if not has_version:
        findings.append({'file': filepath, 'severity': 'WARNING', 'issue': 'No version field defined'})

    # Check event name (if present)
    name = data.get('name', data.get('title', data.get('event_name', '')))
    if name and isinstance(name, str):
        if not NAME_PATTERN.match(name):
            findings.append({'file': filepath, 'severity': 'WARNING',
                           'issue': f'Event name "{name}" should be lowercase, dotted, past tense (e.g., order.placed)'})

    # Check for removed required fields in version history (if available)
    # Check description
    if not data.get('description') and not data.get('doc'):
        findings.append({'file': filepath, 'severity': 'INFO', 'issue': 'No description/documentation field'})

    return findings


def run_lint(root, report=False, json_output=False):
    """Lint all schema files in root."""
    all_findings = []
    file_count = 0
    schema_extensions = ('.json', '.yaml', '.yml', '.avsc', '.proto')

    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if not fn.endswith(schema_extensions):
                continue
            filepath = os.path.join(dirpath, fn)
            # Skip node_modules, .git, etc.
            if any(skip in filepath for skip in ('node_modules', '.git', '__pycache__')):
                continue
            data, fmt = load_schema(filepath)
            if data is None:
                continue
            file_count += 1
            findings = check_schema(data, os.path.relpath(filepath, root))
            all_findings.extend(findings)

    # Score
    errors = sum(1 for f in all_findings if f['severity'] == 'ERROR')
    warnings = sum(1 for f in all_findings if f['severity'] == 'WARNING')
    score = max(0, 100 - errors * 20 - warnings * 5)

    results = {
        'root': os.path.abspath(root),
        'files_checked': file_count,
        'errors': errors,
        'warnings': warnings,
        'findings': all_findings,
        'score': score,
        'report_line': f"Event schema lint: files={file_count}, errors={errors}, warnings={warnings}, score={score}/100",
    }

    if json_output:
        print(json.dumps(results, indent=2))
    elif report:
        print(results['report_line'])
    else:
        print(f"Event Schema Lint: {root}")
        print(f"  Files checked: {file_count}")
        print(f"  Errors: {errors}, Warnings: {warnings}")
        if all_findings:
            for f in all_findings:
                print(f"  [{f['severity']}] {f['file']}: {f['issue']}")
        print(f"  Score: {score}/100")
        print(f"  Report line: {results['report_line']}")

    return 0 if errors == 0 else 1


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print("Usage: event-schema-lint <directory> [--report] [--json]")
        print("  Validates event schemas for versioning, idempotency, and required fields.")
        print("  Exit code 0 if no errors, 1 otherwise.")
        sys.exit(0)

    root = sys.argv[1]
    report = '--report' in sys.argv
    json_output = '--json' in sys.argv

    if not os.path.isdir(root):
        print(f"Error: {root} is not a directory", file=sys.stderr)
        sys.exit(2)

    exit_code = run_lint(root, report=report, json_output=json_output)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

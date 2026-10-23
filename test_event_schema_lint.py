import os
import tempfile
import json
import unittest
from event_schema_lint import check_schema, load_schema, run_lint


class TestEventSchemaLint(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write(self, relpath, content):
        full = os.path.join(self.tmpdir, relpath)
        os.makedirs(os.path.dirname(full), exist_ok=True) if os.path.dirname(relpath) else None
        with open(full, 'w', encoding='utf-8') as f:
            f.write(content)
        return full

    def test_good_schema(self):
        schema = {
            "name": "order.placed",
            "version": "1.0.0",
            "description": "An order was placed",
            "properties": {
                "event_id": {"type": "string"},
                "timestamp": {"type": "string"},
                "source": {"type": "string"},
                "type": {"type": "string"},
                "idempotency_key": {"type": "string"},
            }
        }
        self._write('order.json', json.dumps(schema))
        findings = check_schema(schema, 'order.json')
        errors = [f for f in findings if f['severity'] == 'ERROR']
        self.assertEqual(len(errors), 0)

    def test_missing_required_field(self):
        schema = {
            "name": "order.placed",
            "version": "1.0.0",
            "properties": {
                "event_id": {"type": "string"},
                "timestamp": {"type": "string"},
            }
        }
        findings = check_schema(schema, 'test.json')
        errors = [f for f in findings if f['severity'] == 'ERROR']
        self.assertTrue(len(errors) >= 2)  # source and type missing

    def test_no_version_warning(self):
        schema = {
            "name": "order.placed",
            "properties": {
                "event_id": {"type": "string"},
                "timestamp": {"type": "string"},
                "source": {"type": "string"},
                "type": {"type": "string"},
                "idempotency_key": {"type": "string"},
            }
        }
        findings = check_schema(schema, 'test.json')
        warnings = [f for f in findings if f['severity'] == 'WARNING' and 'version' in f['issue']]
        self.assertTrue(len(warnings) > 0)

    def test_no_idempotency_warning(self):
        schema = {
            "name": "order.placed",
            "version": "1.0.0",
            "properties": {
                "event_id": {"type": "string"},
                "timestamp": {"type": "string"},
                "source": {"type": "string"},
                "type": {"type": "string"},
            }
        }
        findings = check_schema(schema, 'test.json')
        warnings = [f for f in findings if f['severity'] == 'WARNING' and 'idempotency' in f['issue']]
        self.assertTrue(len(warnings) > 0)

    def test_bad_name_format(self):
        schema = {
            "name": "OrderPlaced",
            "version": "1.0.0",
            "properties": {
                "event_id": {"type": "string"},
                "timestamp": {"type": "string"},
                "source": {"type": "string"},
                "type": {"type": "string"},
                "idempotency_key": {"type": "string"},
            }
        }
        findings = check_schema(schema, 'test.json')
        warnings = [f for f in findings if f['severity'] == 'WARNING' and 'name' in f['issue']]
        self.assertTrue(len(warnings) > 0)

    def test_good_name_format(self):
        schema = {
            "name": "order.placed",
            "version": "1.0.0",
            "properties": {
                "event_id": {"type": "string"},
                "timestamp": {"type": "string"},
                "source": {"type": "string"},
                "type": {"type": "string"},
                "idempotency_key": {"type": "string"},
            }
        }
        findings = check_schema(schema, 'test.json')
        name_warnings = [f for f in findings if f['severity'] == 'WARNING' and 'name' in f['issue']]
        self.assertEqual(len(name_warnings), 0)

    def test_load_json_schema(self):
        schema = {"name": "test.event", "version": "1.0", "properties": {"event_id": {}}}
        path = self._write('test.json', json.dumps(schema))
        data, fmt = load_schema(path)
        self.assertEqual(fmt, 'json')
        self.assertEqual(data['name'], 'test.event')

    def test_run_lint_good(self):
        schema = {
            "name": "order.placed",
            "version": "1.0.0",
            "description": "test",
            "properties": {
                "event_id": {"type": "string"},
                "timestamp": {"type": "string"},
                "source": {"type": "string"},
                "type": {"type": "string"},
                "idempotency_key": {"type": "string"},
            }
        }
        self._write('good.json', json.dumps(schema))
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = run_lint(self.tmpdir, json_output=True)
        self.assertEqual(code, 0)

    def test_run_lint_bad(self):
        schema = {"name": "BadEvent", "properties": {"foo": {}}}
        self._write('bad.json', json.dumps(schema))
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = run_lint(self.tmpdir, json_output=True)
        self.assertEqual(code, 1)


if __name__ == '__main__':
    unittest.main()

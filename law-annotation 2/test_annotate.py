"""Offline regression tests. Mock API calls are explicitly not live completions."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import annotate as a

class Response:
    def __init__(self, status, body):
        self.status_code, self.body = status, body
        self.ok = status == 200
        self.headers = {'Retry-After': '0'}
    def json(self):
        return self.body

class Session:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = 0
    def post(self, *args, **kwargs):
        self.calls += 1
        assert kwargs['json']['response_format']['type'] == 'json_schema'
        return next(self.responses)

class Tests(unittest.TestCase):
    def test_exact_quote_and_cross_page_reference(self):
        pages = [(3, 'Alpha beta'), (4, 'Gamma delta')]
        self.assertEqual(a.verify_quote({'supporting_quotation': 'beta\n\nGamma'}, pages), (True, 'PDF page(s) 3, 4'))
        self.assertEqual(a.verify_quote({'supporting_quotation': 'beta Gamma'}, pages), (False, None))
        self.assertEqual(a.verify_quote({'supporting_quotation': 'invented'}, pages), (False, None))

    def test_invalid_json_not_repeated(self):
        s = Session([Response(200, {'choices': [{'finish_reason': 'stop', 'message': {'content': 'invalid'}}]})])
        with self.assertRaises(RuntimeError):
            a.call_api(s, 'FAKE_TEST_CREDENTIAL', 'test', 'source', a.schema(a.COMPANY))
        self.assertEqual(s.calls, 1)

    def test_rate_limit_bounded(self):
        s = Session([Response(429, {}) for _ in range(3)])
        with patch('annotate.time.sleep'), self.assertRaises(RuntimeError):
            a.call_api(s, 'FAKE_TEST_CREDENTIAL', 'test', 'source', a.schema(a.COMPANY))
        self.assertEqual(s.calls, 3)

    def test_schema_rejects_extra_fields(self):
        data = {k: None for k in a.FIELDS}
        data.update(ambiguities=[], source_is_judgment=True, doctrinal_category='Other', confidence_level='low', rule_status='unclear', invented='x')
        with self.assertRaises(a.ValidationError):
            a.validate(data, a.schema(a.COMPANY))

    def test_unprocessed_outputs_are_not_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            a.save_results([{'status':'not_processed', 'source_is_judgment':False, 'doctrinal_category':None, 'ratio_decidendi':None}],p,a.COMPANY)
            self.assertTrue((p/'doctrinal_categories.png').stat().st_size > 1000)
            self.assertTrue(a.pd.read_csv(p/'annotations.csv')['ratio_decidendi'].isna().all())

if __name__ == '__main__':
    unittest.main()

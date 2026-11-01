"""Fail-closed checks for the native model-visible output allowlist."""
import unittest
from unittest.mock import Mock
from service.scripts.configure_workflow import wait_for_result_fields


def inspected(paths,state='valid'):
    return {'data':{'nodes':[{'node_id':'action','state':state,
                              'fields':[{'path':path} for path in paths]}]}}


class WorkflowConfigurationTests(unittest.TestCase):
    def test_stale_error_output_is_not_exposed(self):
        platform=Mock()
        platform.request.side_effect=[inspected(['error']),inspected(['status','loads'])]
        self.assertEqual(wait_for_result_fields(platform,'tool','action',{'status':None,'loads':[]},
                                               attempts=2,interval=0),['status','loads'])
        self.assertEqual(platform.request.call_count,2)

    def test_unknown_or_incomplete_output_fails_without_visibility_write(self):
        for paths in (['error'],['status'],['status','loads','private_price']):
            with self.subTest(paths=paths):
                platform=Mock();platform.request.return_value=inspected(paths)
                with self.assertRaises(RuntimeError):
                    wait_for_result_fields(platform,'tool','action',{'status':None,'loads':[]},attempts=1)
                self.assertTrue(all(call.args[0].endswith('/inspect')
                                    for call in platform.request.call_args_list))

    def test_unvalidated_or_wrong_node_output_is_rejected(self):
        platform=Mock();platform.request.return_value=inspected(['status'],state='untested')
        with self.assertRaises(RuntimeError):
            wait_for_result_fields(platform,'tool','action',{'status':None},attempts=1)
        platform.request.return_value=inspected(['status'])
        with self.assertRaises(RuntimeError):
            wait_for_result_fields(platform,'tool','another-action',{'status':None},attempts=1)

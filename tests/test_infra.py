import json
from pathlib import Path
import unittest
from platform_core.health import handler

class InfrastructureTests(unittest.TestCase):
    def setUp(self):
        self.template = json.loads(Path('infra/template.json').read_text())
        self.resources = self.template['Resources']

    def test_health_and_inline_code_match(self):
        response = handler({}, None)
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['status'], 'ok')
        self.assertEqual(self.resources['HealthFunction']['Properties']['Code']['ZipFile'], Path('platform_core/health.py').read_text())

    def test_storage_controls(self):
        bucket = self.resources['AssetsBucket']['Properties']
        self.assertTrue(all(bucket['PublicAccessBlockConfiguration'].values()))
        self.assertEqual(bucket['VersioningConfiguration']['Status'], 'Enabled')
        table = self.resources['TenantTable']['Properties']
        self.assertTrue(table['SSESpecification']['SSEEnabled'])
        self.assertTrue(table['PointInTimeRecoverySpecification']['PointInTimeRecoveryEnabled'])
        self.assertTrue(table['DeletionProtectionEnabled'])

    def test_data_retained(self):
        for name in ('AssetsBucket','TenantTable','UserPool'):
            self.assertEqual(self.resources[name]['DeletionPolicy'], 'Retain')
            self.assertEqual(self.resources[name]['UpdateReplacePolicy'], 'Retain')

    def test_no_public_endpoint_or_runtime_data_permissions(self):
        self.assertFalse(any(r['Type'] == 'AWS::Lambda::Url' for r in self.resources.values()))
        policy = self.resources['HealthRole']['Properties']['Policies'][0]['PolicyDocument']
        self.assertEqual(policy['Statement'][0]['Action'], ['logs:CreateLogStream','logs:PutLogEvents'])

    def test_signup_is_admin_only(self):
        self.assertTrue(self.resources['UserPool']['Properties']['AdminCreateUserConfig']['AllowAdminCreateUserOnly'])

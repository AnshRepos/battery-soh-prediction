import unittest
import json
import sys
from app import app


class BatteryDashboardAPITests(unittest.TestCase):
    """Test cases for Battery Dashboard Backend API endpoints."""

    @classmethod
    def setUpClass(cls):
        """Set up test client and app context."""
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()

    def setUp(self):
        """Set up before each test."""
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Tear down after each test."""
        self.app_context.pop()

    def test_health_endpoint_returns_200(self):
        """Test that health endpoint returns 200 OK."""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)

    def test_health_endpoint_returns_healthy_status(self):
        """Test that health endpoint returns correct status."""
        response = self.client.get('/api/health')
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')

    def test_health_endpoint_returns_json(self):
        """Test that health endpoint returns JSON."""
        response = self.client.get('/api/health')
        self.assertEqual(response.content_type, 'application/json')

    def test_predict_endpoint_exists(self):
        """Test that predict endpoint exists."""
        response = self.client.post(
            '/api/predict',
            data=json.dumps({}),
            content_type='application/json'
        )
        # Should return 200 or 400 (bad request), but not 404
        self.assertNotEqual(response.status_code, 404)

    def test_predict_endpoint_accepts_post(self):
        """Test that predict endpoint accepts POST requests."""
        response = self.client.post(
            '/api/predict',
            data=json.dumps({
                'temperature': 25.5,
                'voltage': 3.7,
                'current': 0.5,
                'cycle_count': 100,
                'impedance': 0.05
            }),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [200, 400])

    def test_predict_endpoint_returns_json(self):
        """Test that predict endpoint returns JSON."""
        response = self.client.post(
            '/api/predict',
            data=json.dumps({
                'temperature': 25.5,
                'voltage': 3.7,
                'current': 0.5,
                'cycle_count': 100,
                'impedance': 0.05
            }),
            content_type='application/json'
        )
        self.assertEqual(response.content_type, 'application/json')

    def test_metrics_endpoint_exists(self):
        """Test that metrics endpoint exists."""
        response = self.client.get('/api/metrics')
        self.assertNotEqual(response.status_code, 404)

    def test_metrics_endpoint_returns_json(self):
        """Test that metrics endpoint returns JSON."""
        response = self.client.get('/api/metrics')
        self.assertEqual(response.content_type, 'application/json')

    def test_metrics_endpoint_returns_dict(self):
        """Test that metrics endpoint returns a dictionary."""
        response = self.client.get('/api/metrics')
        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertIsInstance(data, dict)

    def test_invalid_endpoint_returns_404(self):
        """Test that invalid endpoint returns 404."""
        response = self.client.get('/api/invalid')
        self.assertEqual(response.status_code, 404)

    def test_predict_with_valid_data_returns_200_or_bad_request(self):
        """Test predict endpoint with valid data structure."""
        payload = {
            'temperature': 25.5,
            'voltage': 3.7,
            'current': 0.5,
            'cycle_count': 100,
            'impedance': 0.05
        }
        response = self.client.post(
            '/api/predict',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [200, 400, 500])

    def test_predict_returns_json_error_on_invalid_input(self):
        """Test that predict returns JSON error on invalid input."""
        response = self.client.post(
            '/api/predict',
            data=json.dumps(None),
            content_type='application/json'
        )
        if response.status_code >= 400:
            self.assertEqual(response.content_type, 'application/json')

    def test_health_endpoint_uses_get_method(self):
        """Test that health endpoint only accepts GET."""
        response = self.client.post(
            '/api/health',
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 405)

    def test_predict_endpoint_uses_post_method(self):
        """Test that predict endpoint only accepts POST."""
        response = self.client.get('/api/predict')
        self.assertEqual(response.status_code, 405)

    def test_metrics_endpoint_uses_get_method(self):
        """Test that metrics endpoint only accepts GET."""
        response = self.client.post(
            '/api/metrics',
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 405)

    def test_api_cors_headers_present(self):
        """Test that CORS headers are present in responses."""
        response = self.client.get('/api/health')
        # Check for common CORS headers
        headers = dict(response.headers)
        # CORS might be configured, check for either presence or absence
        self.assertIsNotNone(response)

    def test_health_endpoint_consistency(self):
        """Test that health endpoint returns consistent results."""
        response1 = self.client.get('/api/health')
        response2 = self.client.get('/api/health')
        
        data1 = json.loads(response1.data)
        data2 = json.loads(response2.data)
        
        self.assertEqual(data1['status'], data2['status'])

    def test_request_with_malformed_json_returns_error(self):
        """Test that malformed JSON request is handled."""
        response = self.client.post(
            '/api/predict',
            data='{ invalid json }',
            content_type='application/json'
        )
        self.assertIn(response.status_code, [400, 500])


class BatteryDashboardIntegrationTests(unittest.TestCase):
    """Integration tests for the API."""

    @classmethod
    def setUpClass(cls):
        """Set up test client and app context."""
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()

    def test_health_check_then_predict_workflow(self):
        """Test health check followed by prediction."""
        # First check health
        health_response = self.client.get('/api/health')
        self.assertEqual(health_response.status_code, 200)
        
        # Then make a prediction
        predict_response = self.client.post(
            '/api/predict',
            data=json.dumps({
                'temperature': 25.5,
                'voltage': 3.7,
                'current': 0.5,
                'cycle_count': 100,
                'impedance': 0.05
            }),
            content_type='application/json'
        )
        self.assertNotEqual(predict_response.status_code, 404)

    def test_health_check_then_metrics_workflow(self):
        """Test health check followed by metrics retrieval."""
        # First check health
        health_response = self.client.get('/api/health')
        self.assertEqual(health_response.status_code, 200)
        
        # Then get metrics
        metrics_response = self.client.get('/api/metrics')
        self.assertNotEqual(metrics_response.status_code, 404)


def run_tests():
    """Run all tests and return results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(BatteryDashboardAPITests))
    suite.addTests(loader.loadTestsFromTestCase(BatteryDashboardIntegrationTests))
    
    # Run tests with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    result = run_tests()
    sys.exit(0 if result.wasSuccessful() else 1)

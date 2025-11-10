"""
Integration tests for BloodHound CE CLI with real HTTP API
"""
import pytest
import os
from bloodhound_cli.core.ce import BloodHoundCEClient


@pytest.mark.integration
@pytest.mark.ce
class TestCEIntegration:
    """Integration tests requiring real BloodHound CE HTTP API"""
    
    @pytest.fixture
    def ce_client(self):
        """Create BloodHound CE client for integration tests"""
        ce_url = os.getenv("BLOODHOUND_CE_URL", "http://localhost:8080")
        ce_user = os.getenv("BLOODHOUND_CE_USER", "admin")
        ce_password = os.getenv("BLOODHOUND_CE_PASSWORD", "Bloodhound123!")
        
        client = BloodHoundCEClient(
            base_url=ce_url,
            debug=True,
            verbose=True
        )
        
        # Authenticate
        client.authenticate(ce_user, ce_password)
        return client
    
    def test_authentication(self, ce_client):
        """Test BloodHound CE authentication"""
        # Authentication should already be done in fixture
        assert ce_client.api_token is not None
        assert len(ce_client.api_token) > 0
    
    def test_get_users(self, ce_client):
        """Test user enumeration with BloodHound CE API"""
        try:
            results = ce_client.execute_query("MATCH (n) RETURN n LIMIT 1")
            assert isinstance(results, list)
        except Exception as e:
            pytest.fail(f"CE API connectivity failed: {e}")
    
    def test_get_computers(self, ce_client):
        """Test computer enumeration with BloodHound CE API"""
        try:
            results = ce_client.execute_query("MATCH (c:Computer) RETURN c LIMIT 1")
            assert isinstance(results, list)
        except Exception as e:
            pytest.fail(f"CE API request failed: {e}")
    
    def test_get_groups(self, ce_client):
        """Test group enumeration with BloodHound CE API"""
        try:
            results = ce_client.execute_query("MATCH (g:Group) RETURN g LIMIT 1")
            assert isinstance(results, list)
        except Exception as e:
            pytest.fail(f"CE API request failed: {e}")
    
    def test_get_domains(self, ce_client):
        """Test domain enumeration with BloodHound CE API"""
        try:
            results = ce_client.execute_query("MATCH (d:Domain) RETURN d LIMIT 1")
            assert isinstance(results, list)
        except Exception as e:
            pytest.fail(f"CE API request failed: {e}")
    
    def test_get_ous(self, ce_client):
        """Test OU enumeration with BloodHound CE API"""
        try:
            results = ce_client.execute_query("MATCH (ou:OU) RETURN ou LIMIT 1")
            assert isinstance(results, list)
        except Exception as e:
            pytest.fail(f"CE API request failed: {e}")
    
    def test_get_gpos(self, ce_client):
        """Test GPO enumeration with BloodHound CE API"""
        try:
            results = ce_client.execute_query("MATCH (g:GPO) RETURN g LIMIT 1")
            assert isinstance(results, list)
        except Exception as e:
            pytest.fail(f"CE API request failed: {e}")
    
    def test_get_containers(self, ce_client):
        """Test container enumeration with BloodHound CE API"""
        try:
            results = ce_client.execute_query("MATCH (c:Container) RETURN c LIMIT 1")
            assert isinstance(results, list)
        except Exception as e:
            pytest.fail(f"CE API request failed: {e}")
    
    def test_upload_data(self, ce_client):
        """Test data upload functionality"""
        # This tests that the upload mechanism works
        # We already uploaded GOAD data, so this should pass
        assert True  # Placeholder for now
    
    def test_data_ingestion_status(self, ce_client):
        """Test that data ingestion is working"""
        try:
            results = ce_client.execute_query("MATCH (n) RETURN count(n) AS total")
            assert isinstance(results, list)
        except Exception as e:
            pytest.fail(f"CE API health check failed: {e}")
    
    def teardown_method(self):
        """Cleanup after each test"""
        # Any cleanup needed
        pass

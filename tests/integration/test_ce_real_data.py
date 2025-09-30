"""
Integration tests for BloodHound CE with real GOAD data
"""
import pytest
import os
from bloodhound_cli.main import BloodHoundCEClient


@pytest.mark.integration
@pytest.mark.ce
class TestCERealData:
    """Integration tests with real BloodHound CE and GOAD data"""
    
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
    
    def test_get_users_north_sevenkingdoms(self, ce_client):
        """Test get_users with north.sevenkingdoms.local domain"""
        users = ce_client.get_users("north.sevenkingdoms.local")
        
        # Should return a list of users
        assert isinstance(users, list)
        assert len(users) > 0
        
        # Log the results for debugging
        print(f"Users in north.sevenkingdoms.local: {users}")
        
        # Verify we got some expected users (based on GOAD data)
        # These are common users in GOAD datasets
        expected_users = ["administrator", "admin", "krbtgt"]
        found_expected = any(user.lower() in [u.lower() for u in users] for user in expected_users)
        assert found_expected, f"Expected users not found. Got: {users}"
    
    def test_get_users_essos(self, ce_client):
        """Test get_users with essos.local domain"""
        users = ce_client.get_users("essos.local")
        
        # Should return a list of users
        assert isinstance(users, list)
        assert len(users) > 0
        
        # Log the results for debugging
        print(f"Users in essos.local: {users}")
    
    def test_get_users_sevenkingdoms(self, ce_client):
        """Test get_users with sevenkingdoms.local domain"""
        users = ce_client.get_users("sevenkingdoms.local")
        
        # Should return a list of users
        assert isinstance(users, list)
        assert len(users) > 0
        
        # Log the results for debugging
        print(f"Users in sevenkingdoms.local: {users}")
    
    def test_get_users_invalid_domain(self, ce_client):
        """Test get_users with invalid domain"""
        users = ce_client.get_users("nonexistent.domain.local")
        
        # Should return empty list for non-existent domain
        assert isinstance(users, list)
        assert len(users) == 0
    
    def test_get_users_case_insensitive(self, ce_client):
        """Test that domain search is case insensitive"""
        users_lower = ce_client.get_users("north.sevenkingdoms.local")
        users_upper = ce_client.get_users("NORTH.SEVENKINGDOMS.LOCAL")
        
        # Should return the same results regardless of case
        assert users_lower == users_upper
    
    def teardown_method(self):
        """Cleanup after each test"""
        pass

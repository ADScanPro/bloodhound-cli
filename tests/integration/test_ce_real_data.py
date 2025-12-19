"""
Integration tests for BloodHound CE with real GOAD data
"""
import pytest
import os
from bloodhound_cli.core.ce import BloodHoundCEClient


@pytest.mark.integration
@pytest.mark.ce
class TestCERealData:
    """Integration tests with real BloodHound CE and GOAD data"""
    
    @pytest.fixture
    def ce_client(self):
        """Create BloodHound CE client for integration tests"""
        ce_url = os.getenv("BLOODHOUND_CE_URL", "http://localhost:8080")
        ce_user = os.getenv("BLOODHOUND_CE_USER", "admin")
        ce_password = os.getenv("BLOODHOUND_CE_PASSWORD", "Adscan4thewin!")
        
        client = BloodHoundCEClient(
            base_url=ce_url,
            debug=True,
            verbose=True
        )
        
        # Authenticate
        client.authenticate(ce_user, ce_password)
        return client
    
    def test_get_critical_aces_missandei(self, ce_client):
        """Ensure ACLs for missandei in essos.local return expected targets"""
        aces = ce_client.get_critical_aces(
            source_domain="essos.local",
            high_value=False,
            username="missandei",
            target_domain="all",
            relation="all",
        )

        targets = {(ace["target"], ace["relation"]) for ace in aces}
        assert ("khal.drogo", "GenericAll") in targets
        assert ("viserys.targaryen", "GenericWrite") in targets

    def test_get_critical_aces_missandei_high_value(self, ce_client):
        """High-value filter should exclude missandei ACEs."""
        aces = ce_client.get_critical_aces(
            source_domain="essos.local",
            high_value=True,
            username="missandei",
            target_domain="all",
            relation="all",
        )
        assert aces == []

    def test_get_critical_aces_stannis_high_value(self, ce_client):
        """Stannis high-value ACEs should include only KINGSLANDING$ (BRAAVOS$ is not high-value)."""
        aces = ce_client.get_critical_aces(
            source_domain="sevenkingdoms.local",
            high_value=True,
            username="stannis.baratheon",
            target_domain="all",
            relation="all",
        )
        targets = {(ace["target"], ace["relation"]) for ace in aces}
        # BRAAVOS$ does not have system_tags = "admin_tier_0", so it should NOT appear with high-value filter
        assert ("BRAAVOS$", "ReadLAPSPassword") not in targets
        # Only KINGSLANDING$ has system_tags = "admin_tier_0" and should appear
        assert ("KINGSLANDING$", "GenericAll") in targets

    def test_get_critical_aces_group_small_council(self, ce_client):
        """Group Small Council should surface nested ACLs."""
        aces = ce_client.get_critical_aces(
            source_domain="sevenkingdoms.local",
            high_value=False,
            username="small council",
            target_domain="all",
            relation="all",
        )
        triples = {(ace["source"], ace["target"], ace["relation"]) for ace in aces}
        assert ("Spys", "jorah.mormont", "GenericAll") in triples
        assert ("Spys", "BRAAVOS$", "ReadLAPSPassword") in triples
        assert ("Small Council", "DragonStone", "AddMember") in triples

    def test_get_critical_aces_group_small_council_high_value(self, ce_client):
        """High-value filter should retain tier-0 ACEs from Small Council.
        
        Note: BRAAVOS$ does not have system_tags = "admin_tier_0", so it should NOT
        appear when filtering for high-value targets.
        """
        aces = ce_client.get_critical_aces(
            source_domain="sevenkingdoms.local",
            high_value=True,
            username="small council",
            target_domain="all",
            relation="all",
        )
        triples = {(ace["source"], ace["target"], ace["relation"]) for ace in aces}
        # BRAAVOS$ is not high-value (no system_tags = "admin_tier_0"), so no results expected
        assert triples == set(), f"Expected empty set for high-value filter, but got: {triples}"

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

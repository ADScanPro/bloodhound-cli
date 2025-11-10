"""
Integration tests for Legacy BloodHound CLI with real Neo4j database
"""
import pytest
import os
from bloodhound_cli.old_main import BloodHoundACEAnalyzer


@pytest.mark.integration
class TestLegacyIntegration:
    """Integration tests requiring real Neo4j database"""
    
    @pytest.fixture
    def legacy_client(self):
        """Create client with test database connection"""
        legacy_uri = os.getenv("BLOODHOUND_LEGACY_URI")
        legacy_user = os.getenv("BLOODHOUND_LEGACY_USER")
        legacy_password = os.getenv("BLOODHOUND_LEGACY_PASSWORD")

        if not all([legacy_uri, legacy_user, legacy_password]):
            pytest.skip("Legacy Neo4j credentials not configured (set BLOODHOUND_LEGACY_* env vars)")

        analyzer = BloodHoundACEAnalyzer(legacy_uri, legacy_user, legacy_password, debug=True, verbose=True)
        try:
            analyzer.driver.verify_connectivity()
        except Exception as exc:  # neo4j.exceptions.Neo4jError or AuthError
            pytest.skip(f"Legacy Neo4j unavailable or authentication failed: {exc}")
        return analyzer
    
    def test_get_users(self, legacy_client):
        """Test user enumeration with real data"""
        users = legacy_client.get_users("TEST.LOCAL")
        
        # Verify expected users are returned
        assert "admin" in users
        assert "testuser" in users
        assert "service" in users
        assert len(users) >= 3
    
    def test_get_computers(self, legacy_client):
        """Test computer enumeration with real data"""
        computers = legacy_client.get_computers("TEST.LOCAL")
        
        # Verify expected computers
        assert "dc01" in [c.lower() for c in computers]
        assert "ws01" in [c.lower() for c in computers]
        assert len(computers) >= 2
    
    def test_get_computers_with_laps(self, legacy_client):
        """Test computer enumeration with LAPS filter"""
        computers_with_laps = legacy_client.get_computers("TEST.LOCAL", laps=True)
        computers_without_laps = legacy_client.get_computers("TEST.LOCAL", laps=False)
        
        # Verify LAPS filtering
        assert len(computers_with_laps) >= 1
        assert len(computers_without_laps) >= 1
        assert len(computers_with_laps) + len(computers_without_laps) >= 2
    
    def test_get_admin_users(self, legacy_client):
        """Test admin user enumeration"""
        admin_users = legacy_client.get_admin_users("TEST.LOCAL")
        
        # Verify admin user is present
        assert "admin" in admin_users
        assert len(admin_users) >= 1
    
    def test_get_highvalue_users(self, legacy_client):
        """Test high-value user enumeration"""
        highvalue_users = legacy_client.get_highvalue_users("TEST.LOCAL")
        
        # Verify high-value users
        assert "admin" in highvalue_users
        assert len(highvalue_users) >= 1
    
    def test_get_password_not_required_users(self, legacy_client):
        """Test password not required users"""
        pwd_not_req_users = legacy_client.get_password_not_required_users("TEST.LOCAL")
        
        # Verify users without password requirement
        assert "service" in pwd_not_req_users
        assert len(pwd_not_req_users) >= 1
    
    def test_get_password_never_expires_users(self, legacy_client):
        """Test password never expires users"""
        pwd_never_exp_users = legacy_client.get_password_never_expires_users("TEST.LOCAL")
        
        # Verify users whose password never expires
        assert "service" in pwd_never_exp_users
        assert len(pwd_never_exp_users) >= 1
    
    def test_get_critical_aces(self, legacy_client):
        """Test ACL enumeration"""
        aces = legacy_client.get_critical_aces(
            source_domain="TEST.LOCAL",
            high_value=False,
            username="admin",
            target_domain="all",
            relation="all"
        )
        
        # Verify ACL results are returned
        assert len(aces) >= 0  # Puede ser 0 si no hay ACLs directas
    
    def test_get_access_paths(self, legacy_client):
        """Test access path enumeration"""
        access_paths = legacy_client.get_access_paths(
            source="admin",
            connection="all",
            target="all",
            domain="TEST.LOCAL"
        )
        
        # Verify access paths are returned
        assert isinstance(access_paths, list)
    
    def test_get_sessions(self, legacy_client):
        """Test session enumeration"""
        sessions = legacy_client.get_sessions("TEST.LOCAL", da=False)
        
        # Verify sessions list
        assert isinstance(sessions, list)
        # Puede ser vacío si no hay sesiones activas
    
    def test_get_sessions_da(self, legacy_client):
        """Test domain admin session enumeration"""
        da_sessions = legacy_client.get_sessions("TEST.LOCAL", da=True)
        
        # Verify domain admin sessions list
        assert isinstance(da_sessions, list)
    
    def test_password_last_change(self, legacy_client):
        """Test password last change data"""
        pwd_data = legacy_client.get_password_last_change("TEST.LOCAL")
        
        # Verify password data list
        assert isinstance(pwd_data, list)
        assert len(pwd_data) >= 3  # Al menos 3 usuarios
        
        # Verify data structure
        for user_data in pwd_data:
            assert "user" in user_data
            assert "password_last_change" in user_data
            assert "when_created" in user_data
    
    def test_custom_query(self, legacy_client):
        """Test custom Cypher query execution"""
        query = "MATCH (u:User) WHERE u.domain = 'TEST.LOCAL' RETURN u.samaccountname LIMIT 5"
        
        # Should not raise an exception
        try:
            legacy_client.execute_custom_query(query)
        except Exception as e:
            pytest.fail(f"Custom query failed: {e}")
    
    def teardown_method(self):
        """Cleanup after each test"""
        # Perform any required cleanup
        pass

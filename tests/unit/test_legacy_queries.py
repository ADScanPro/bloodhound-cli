"""
Unit tests for Legacy BloodHound queries using mocks
"""
import pytest
from unittest.mock import Mock, patch
from bloodhound_cli.main import BloodHoundACEAnalyzer


class TestLegacyQueries:
    """Test Legacy BloodHound queries with mocked Neo4j session"""
    
    @pytest.fixture
    def mock_analyzer(self):
        """Create analyzer with mocked Neo4j driver"""
        with patch('bloodhound_cli.main.GraphDatabase.driver') as mock_driver:
            mock_session = Mock()
            mock_session.run.return_value.data.return_value = []
            mock_driver.return_value.session.return_value.__enter__.return_value = mock_session
            mock_driver.return_value.session.return_value.__exit__.return_value = None
            
            analyzer = BloodHoundACEAnalyzer(
                uri="bolt://localhost:7687",
                user="neo4j", 
                password="test",
                debug=False,
                verbose=False
            )
            analyzer.driver = mock_driver.return_value
            return analyzer
    
    def test_get_users_basic(self, mock_analyzer):
        """Test basic user enumeration"""
        # Mock response
        mock_data = [
            {"samaccountname": "admin"},
            {"samaccountname": "user1"},
            {"samaccountname": "user2"}
        ]
        mock_analyzer.driver.session.return_value.__enter__.return_value.run.return_value.data.return_value = mock_data
        
        users = mock_analyzer.get_users("test.local")
        
        assert len(users) == 3
        assert "admin" in users
        assert "user1" in users
        assert "user2" in users
    
    def test_get_computers_basic(self, mock_analyzer):
        """Test basic computer enumeration"""
        # Mock response
        mock_data = [
            {"name": "dc01.test.local"},
            {"name": "ws01.test.local"}
        ]
        mock_analyzer.driver.session.return_value.__enter__.return_value.run.return_value.data.return_value = mock_data
        
        computers = mock_analyzer.get_computers("test.local")
        
        assert len(computers) == 2
        assert "dc01" in computers[0]
        assert "ws01" in computers[1]
    
    def test_get_computers_with_laps(self, mock_analyzer):
        """Test computer enumeration with LAPS filter"""
        # Mock response for computers with LAPS
        mock_data = [{"name": "dc01.test.local"}]
        mock_analyzer.driver.session.return_value.__enter__.return_value.run.return_value.data.return_value = mock_data
        
        computers_with_laps = mock_analyzer.get_computers("test.local", laps=True)
        
        assert len(computers_with_laps) == 1
        assert "dc01" in computers_with_laps[0]
    
    def test_get_admin_users(self, mock_analyzer):
        """Test admin user enumeration"""
        # Mock response
        mock_data = [
            {"samaccountname": "admin"},
            {"samaccountname": "domain_admin"}
        ]
        mock_analyzer.driver.session.return_value.__enter__.return_value.run.return_value.data.return_value = mock_data
        
        admin_users = mock_analyzer.get_admin_users("test.local")
        
        assert len(admin_users) == 2
        assert "admin" in admin_users
        assert "domain_admin" in admin_users
    
    def test_get_highvalue_users(self, mock_analyzer):
        """Test high-value user enumeration"""
        # Mock response
        mock_data = [
            {"samaccountname": "ceo"},
            {"samaccountname": "admin"}
        ]
        mock_analyzer.driver.session.return_value.__enter__.return_value.run.return_value.data.return_value = mock_data
        
        highvalue_users = mock_analyzer.get_highvalue_users("test.local")
        
        assert len(highvalue_users) == 2
        assert "ceo" in highvalue_users
        assert "admin" in highvalue_users
    
    def test_get_password_not_required_users(self, mock_analyzer):
        """Test password not required users"""
        # Mock response
        mock_data = [
            {"samaccountname": "service_account"}
        ]
        mock_analyzer.driver.session.return_value.__enter__.return_value.run.return_value.data.return_value = mock_data
        
        pwd_not_req_users = mock_analyzer.get_password_not_required_users("test.local")
        
        assert len(pwd_not_req_users) == 1
        assert "service_account" in pwd_not_req_users
    
    def test_get_password_never_expires_users(self, mock_analyzer):
        """Test password never expires users"""
        # Mock response
        mock_data = [
            {"samaccountname": "service_account"}
        ]
        mock_analyzer.driver.session.return_value.__enter__.return_value.run.return_value.data.return_value = mock_data
        
        pwd_never_exp_users = mock_analyzer.get_password_never_expires_users("test.local")
        
        assert len(pwd_never_exp_users) == 1
        assert "service_account" in pwd_never_exp_users
    
    def test_get_critical_aces_basic(self, mock_analyzer):
        """Test basic ACL enumeration"""
        # Mock response
        mock_data = [
            {
                "result": {
                    "source": "user1",
                    "sourceType": "User",
                    "target": "group1", 
                    "targetType": "Group",
                    "type": "MemberOf",
                    "sourceDomain": "test.local",
                    "targetDomain": "test.local",
                    "targetEnabled": True
                }
            }
        ]
        mock_analyzer.driver.session.return_value.__enter__.return_value.run.return_value.data.return_value = mock_data
        
        aces = mock_analyzer.get_critical_aces(
            source_domain="test.local",
            high_value=False,
            username="user1",
            target_domain="all",
            relation="all"
        )
        
        assert len(aces) == 1
        assert aces[0]["source"] == "user1"
        assert aces[0]["target"] == "group1"
        assert aces[0]["type"] == "MemberOf"
    
    def test_get_sessions_basic(self, mock_analyzer):
        """Test basic session enumeration"""
        # Mock response
        mock_data = [
            {"computer": "dc01.test.local"}
        ]
        mock_analyzer.driver.session.return_value.__enter__.return_value.run.return_value.data.return_value = mock_data
        
        sessions = mock_analyzer.get_sessions("test.local", da=False)
        
        assert len(sessions) == 1
        assert sessions[0]["computer"] == "dc01.test.local"
    
    def test_get_sessions_da(self, mock_analyzer):
        """Test domain admin session enumeration"""
        # Mock response
        mock_data = [
            {"computer": "dc01.test.local", "domain_admin": "admin"}
        ]
        mock_analyzer.driver.session.return_value.__enter__.return_value.run.return_value.data.return_value = mock_data
        
        da_sessions = mock_analyzer.get_sessions("test.local", da=True)
        
        assert len(da_sessions) == 1
        assert da_sessions[0]["computer"] == "dc01.test.local"
        assert da_sessions[0]["domain_admin"] == "admin"
    
    def test_get_access_paths_basic(self, mock_analyzer):
        """Test basic access path enumeration"""
        # Mock response
        mock_data = [
            {
                "source": "user1",
                "sourceType": "User",
                "target": "computer1",
                "targetType": "Computer", 
                "type": "AdminTo",
                "sourceDomain": "test.local",
                "targetDomain": "test.local"
            }
        ]
        mock_analyzer.driver.session.return_value.__enter__.return_value.run.return_value.data.return_value = mock_data
        
        access_paths = mock_analyzer.get_access_paths(
            source="user1",
            connection="AdminTo",
            target="all",
            domain="test.local"
        )
        
        assert len(access_paths) == 1
        assert access_paths[0]["source"] == "user1"
        assert access_paths[0]["target"] == "computer1"
        assert access_paths[0]["type"] == "AdminTo"

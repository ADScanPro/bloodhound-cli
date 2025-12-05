"""
Unit tests for BloodHound CE queries using mocks
"""
from types import SimpleNamespace
import pytest
from unittest.mock import Mock, patch
from bloodhound_cli.core.ce import BloodHoundCEClient
from bloodhound_cli import main as cli_main


class TestCEQueries:
    """Test BloodHound CE queries with mocked HTTP API"""
    
    @pytest.fixture
    def mock_ce_client(self):
        """Create CE client with mocked execute_query method"""
        client = BloodHoundCEClient(
            base_url="http://localhost:8080",
            debug=False,
            verbose=False
        )
        
        # Mock execute_query to return real data from north.sevenkingdoms.local
        client.execute_query = Mock(return_value=[
            {
                "samaccountname": "jeor.mormont",
                "name": "JEOR.MORMONT@NORTH.SEVENKINGDOMS.LOCAL",
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            },
            {
                "samaccountname": "sql_svc",
                "name": "SQL_SVC@NORTH.SEVENKINGDOMS.LOCAL",
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            },
            {
                "samaccountname": "samwell.tarly",
                "name": "SAMWELL.TARLY@NORTH.SEVENKINGDOMS.LOCAL",
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            },
            {
                "samaccountname": "hodor",
                "name": "HODOR@NORTH.SEVENKINGDOMS.LOCAL",
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            },
            {
                "samaccountname": "brandon.stark",
                "name": "BRANDON.STARK@NORTH.SEVENKINGDOMS.LOCAL",
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            },
            {
                "samaccountname": "robb.stark",
                "name": "ROBB.STARK@NORTH.SEVENKINGDOMS.LOCAL",
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            },
            {
                "samaccountname": "rickon.stark",
                "name": "RICKON.STARK@NORTH.SEVENKINGDOMS.LOCAL",
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            },
            {
                "samaccountname": "jon.snow",
                "name": "JON.SNOW@NORTH.SEVENKINGDOMS.LOCAL",
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            },
            {
                "samaccountname": "catelyn.stark",
                "name": "CATELYN.STARK@NORTH.SEVENKINGDOMS.LOCAL",
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            },
            {
                "samaccountname": "sansa.stark",
                "name": "SANSA.STARK@NORTH.SEVENKINGDOMS.LOCAL",
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            },
            {
                "samaccountname": "eddard.stark",
                "name": "EDDARD.STARK@NORTH.SEVENKINGDOMS.LOCAL",
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            },
            {
                "samaccountname": "arya.stark",
                "name": "ARYA.STARK@NORTH.SEVENKINGDOMS.LOCAL",
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            },
            {
                "samaccountname": "Administrator",
                "name": "ADMINISTRATOR@NORTH.SEVENKINGDOMS.LOCAL",
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            }
        ])
        
        return client
    
    @pytest.fixture
    def mock_ce_client_admin(self):
        """Create CE client with mocked admin users data"""
        client = BloodHoundCEClient(
            base_url="http://localhost:8080",
            debug=False,
            verbose=False
        )
        
        # Mock execute_query to return real enabled admin users from north.sevenkingdoms.local
        client.execute_query = Mock(return_value=[
            {
                "samaccountname": "robb.stark",
                "name": "ROBB.STARK@NORTH.SEVENKINGDOMS.LOCAL",
                "admincount": True,
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            },
            {
                "samaccountname": "catelyn.stark",
                "name": "CATELYN.STARK@NORTH.SEVENKINGDOMS.LOCAL",
                "admincount": True,
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            },
            {
                "samaccountname": "eddard.stark",
                "name": "EDDARD.STARK@NORTH.SEVENKINGDOMS.LOCAL",
                "admincount": True,
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            },
            {
                "samaccountname": "Administrator",
                "name": "ADMINISTRATOR@NORTH.SEVENKINGDOMS.LOCAL",
                "admincount": True,
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            }
        ])
        
        return client
    
    @pytest.fixture
    def mock_ce_client_highvalue(self):
        """Create CE client with mocked high value users data"""
        client = BloodHoundCEClient(
            base_url="http://localhost:8080",
            debug=False,
            verbose=False
        )
        
        # Mock execute_query to return real enabled high value users from north.sevenkingdoms.local
        client.execute_query = Mock(return_value=[
            {
                "samaccountname": "robb.stark",
                "name": "ROBB.STARK@NORTH.SEVENKINGDOMS.LOCAL",
                "system_tags": "admin_tier_0",
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            },
            {
                "samaccountname": "catelyn.stark",
                "name": "CATELYN.STARK@NORTH.SEVENKINGDOMS.LOCAL",
                "system_tags": "admin_tier_0",
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            },
            {
                "samaccountname": "eddard.stark",
                "name": "EDDARD.STARK@NORTH.SEVENKINGDOMS.LOCAL",
                "system_tags": "admin_tier_0",
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            },
            {
                "samaccountname": "Administrator",
                "name": "ADMINISTRATOR@NORTH.SEVENKINGDOMS.LOCAL",
                "system_tags": "admin_tier_0",
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            }
        ])
        
        return client
    
    @pytest.fixture
    def mock_ce_client_computers(self):
        """Create CE client with mocked computers data"""
        client = BloodHoundCEClient(
            base_url="http://localhost:8080",
            debug=False,
            verbose=False
        )
        
        # Mock execute_query to return real computers from north.sevenkingdoms.local
        client.execute_query = Mock(return_value=[
            {
                "name": "WINTERFELL.NORTH.SEVENKINGDOMS.LOCAL",
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            },
            {
                "name": "CASTELBLACK.NORTH.SEVENKINGDOMS.LOCAL",
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            }
        ])
        
        return client
    
    def test_get_users_basic(self, mock_ce_client):
        """Test basic user enumeration with CySQL query"""
        users = mock_ce_client.get_users("north.sevenkingdoms.local")
        
        # Verify we get the correct number of users (13 total)
        assert len(users) == 13
        
        # Verify specific users are present
        expected_users = [
            "jeor.mormont", "sql_svc", "samwell.tarly", "hodor", "brandon.stark",
            "robb.stark", "rickon.stark", "jon.snow", "catelyn.stark", "sansa.stark",
            "eddard.stark", "arya.stark", "Administrator"
        ]
        for user in expected_users:
            assert user in users
        
        # Verify execute_query was called with correct CySQL query
        mock_ce_client.execute_query.assert_called_once()
        call_args = mock_ce_client.execute_query.call_args[0][0]
        assert "MATCH (u:User)" in call_args
        assert "u.enabled = true" in call_args
        assert "NORTH.SEVENKINGDOMS.LOCAL" in call_args
    
    def test_get_users_empty_response(self, mock_ce_client):
        """Test user enumeration with empty response"""
        mock_ce_client.execute_query.return_value = []
        
        users = mock_ce_client.get_users("empty.domain.local")
        
        assert len(users) == 0
    
    def test_get_users_query_error(self, mock_ce_client):
        """Test user enumeration with query error"""
        mock_ce_client.execute_query.return_value = None
        
        users = mock_ce_client.get_users("error.domain.local")
        
        assert len(users) == 0
    
    def test_get_users_disabled_users_filtered(self, mock_ce_client):
        """Test that disabled users are filtered out by CySQL query"""
        # Mock execute_query to return only enabled users (CySQL query filters by enabled=true)
        mock_ce_client.execute_query.return_value = [
            {
                "samaccountname": "active_user",
                "name": "ACTIVE_USER@NORTH.SEVENKINGDOMS.LOCAL",
                "enabled": True,
                "domain": "NORTH.SEVENKINGDOMS.LOCAL"
            }
        ]
        
        users = mock_ce_client.get_users("north.sevenkingdoms.local")
        
        assert len(users) == 1
        assert "active_user" in users
        # Note: disabled users are filtered out by the CySQL query itself (WHERE u.enabled = true)
    
    def test_get_users_different_domains(self, mock_ce_client):
        """Test user enumeration with different domains"""
        # Test with essos.local
        mock_ce_client.execute_query.return_value = [
            {
                "samaccountname": "khal",
                "name": "KHAL@ESSOS.LOCAL",
                "enabled": True,
                "domain": "ESSOS.LOCAL"
            }
        ]
        
        users = mock_ce_client.get_users("essos.local")
        assert len(users) == 1
        assert "khal" in users
        
        # Test with sevenkingdoms.local
        mock_ce_client.execute_query.return_value = [
            {
                "samaccountname": "tyrion",
                "name": "TYRION@SEVENKINGDOMS.LOCAL",
                "enabled": True,
                "domain": "SEVENKINGDOMS.LOCAL"
            }
        ]
        
        users = mock_ce_client.get_users("sevenkingdoms.local")
        assert len(users) == 1
        assert "tyrion" in users
    
    def test_get_users_exception_handling(self, mock_ce_client):
        """Test exception handling in get_users"""
        mock_ce_client.execute_query.side_effect = Exception("Query error")
        
        users = mock_ce_client.get_users("error.domain.local")
        
        assert len(users) == 0

    def test_get_users_in_ou_exception_handling(self, mock_ce_client):
        """Test exception handling in get_users_in_ou"""
        mock_ce_client.execute_query.side_effect = Exception("Query error")

        users = mock_ce_client.get_users_in_ou(
            "error.domain.local",
            "OU=Winterfell,DC=north,DC=sevenkingdoms,DC=local",
        )

        assert len(users) == 0

    def test_get_users_in_ou_uses_ou_dn_and_domain(self, mock_ce_client):
        """Test OU-based user enumeration builds the correct Cypher query and parses results."""
        ou_dn = "OU=Winterfell,DC=north,DC=sevenkingdoms,DC=local"
        domain = "north.sevenkingdoms.local"

        users = mock_ce_client.get_users_in_ou(domain, ou_dn)

        # Same mocked execute_query data as for get_users
        assert len(users) == 13
        assert "jeor.mormont" in users

        mock_ce_client.execute_query.assert_called_once()
        query = mock_ce_client.execute_query.call_args[0][0]
        assert "MATCH (ou:OU)" in query
        assert "MATCH (u:User)" in query
        assert "ou.distinguishedname" in query
        assert domain.upper() in query
        assert ou_dn in query
    
    def test_get_computers_basic(self, mock_ce_client_computers):
        """Test basic computer enumeration with CySQL query"""
        computers = mock_ce_client_computers.get_computers("north.sevenkingdoms.local")
        
        # Verify we get the correct number of computers (2 total)
        assert len(computers) == 2
        
        # Verify specific computers are present (exact names from CLI output)
        expected_computers = ["winterfell.north.sevenkingdoms.local", "castelblack.north.sevenkingdoms.local"]
        for computer in expected_computers:
            assert computer in computers
        
        # Verify execute_query was called with correct CySQL query
        mock_ce_client_computers.execute_query.assert_called_once()
        call_args = mock_ce_client_computers.execute_query.call_args[0][0]
        assert "MATCH (c:Computer)" in call_args
        assert "c.enabled = true" in call_args
        assert "NORTH.SEVENKINGDOMS.LOCAL" in call_args
    
    def test_get_computers_with_laps_filter(self, mock_ce_client):
        """Test computer enumeration with LAPS filtering using real essos.local data"""
        # Mock execute_query to return different data based on LAPS filter
        def mock_execute_query_with_laps(query):
            if "c.haslaps = true" in query:
                # Computers with LAPS
                return [
                    {
                        "name": "BRAAVOS@ESSOS.LOCAL",
                        "enabled": True,
                        "haslaps": True,
                        "domain": "ESSOS.LOCAL"
                    }
                ]
            elif "c.haslaps = false" in query:
                # Computers without LAPS
                return [
                    {
                        "name": "MEEREEN@ESSOS.LOCAL",
                        "enabled": True,
                        "haslaps": False,
                        "domain": "ESSOS.LOCAL"
                    }
                ]
            else:
                # All computers
                return [
                    {
                        "name": "BRAAVOS@ESSOS.LOCAL",
                        "enabled": True,
                        "haslaps": True,
                        "domain": "ESSOS.LOCAL"
                    },
                    {
                        "name": "MEEREEN@ESSOS.LOCAL",
                        "enabled": True,
                        "haslaps": False,
                        "domain": "ESSOS.LOCAL"
                    }
                ]
        
        mock_ce_client.execute_query = Mock(side_effect=mock_execute_query_with_laps)
        
        # Test with LAPS=True
        computers_with_laps = mock_ce_client.get_computers("essos.local", laps=True)
        assert len(computers_with_laps) == 1
        assert "braavos" in computers_with_laps
        
        # Test with LAPS=False
        computers_without_laps = mock_ce_client.get_computers("essos.local", laps=False)
        assert len(computers_without_laps) == 1
        assert "meereen" in computers_without_laps
        
        # Test without LAPS filter (all computers)
        all_computers = mock_ce_client.get_computers("essos.local", laps=None)
        assert len(all_computers) == 2
        assert "braavos" in all_computers
        assert "meereen" in all_computers
    
    def test_get_computers_empty_response(self, mock_ce_client):
        """Test computer enumeration with empty response"""
        mock_ce_client.execute_query.return_value = []
        
        computers = mock_ce_client.get_computers("empty.domain.local")
        
        assert len(computers) == 0
    
    def test_get_computers_disabled_computers_filtered(self, mock_ce_client):
        """Test that disabled computers are filtered out by CySQL query"""
        # Mock should only return enabled computers since CySQL query filters by enabled = true
        mock_ce_client.execute_query.return_value = [
            {
                "name": "ACTIVE_COMPUTER@north.sevenkingdoms.local",
                "enabled": True,
                "domain": "north.sevenkingdoms.local"
            }
        ]
        
        computers = mock_ce_client.get_computers("north.sevenkingdoms.local")
        
        assert len(computers) == 1
        assert "active_computer" in computers
        
        # Verify the CySQL query includes enabled = true filter
        mock_ce_client.execute_query.assert_called_once()
        call_args = mock_ce_client.execute_query.call_args[0][0]
        assert "c.enabled = true" in call_args
    
    def test_get_computers_exception_handling(self, mock_ce_client):
        """Test exception handling in get_computers"""
        mock_ce_client.execute_query.side_effect = Exception("Network error")
        
        computers = mock_ce_client.get_computers("error.domain.local")
        
        assert len(computers) == 0
    
    def test_get_admin_users_basic(self, mock_ce_client_admin):
        """Test basic admin user enumeration with CySQL query"""
        admin_users = mock_ce_client_admin.get_admin_users("north.sevenkingdoms.local")
        
        # Verify we get the correct number of enabled admin users (4 total)
        assert len(admin_users) == 4
        
        # Verify specific enabled admin users are present
        expected_admin_users = [
            "robb.stark", "catelyn.stark", "eddard.stark", "Administrator"
        ]
        for user in expected_admin_users:
            assert user in admin_users
        
        # Verify execute_query was called with correct CySQL query
        mock_ce_client_admin.execute_query.assert_called_once()
        call_args = mock_ce_client_admin.execute_query.call_args[0][0]
        assert "MATCH (u:User)" in call_args
        assert "u.admincount = true" in call_args
        assert "NORTH.SEVENKINGDOMS.LOCAL" in call_args
    
    def test_get_highvalue_users_basic(self, mock_ce_client_highvalue):
        """Test basic high value user enumeration with CySQL query"""
        hv_users = mock_ce_client_highvalue.get_highvalue_users("north.sevenkingdoms.local")
        
        # Verify we get the correct number of enabled high value users (4 total)
        assert len(hv_users) == 4
        
        # Verify specific enabled high value users are present
        expected_hv_users = [
            "robb.stark", "catelyn.stark", "eddard.stark", "Administrator"
        ]
        for user in expected_hv_users:
            assert user in hv_users
        
        # Verify execute_query was called with correct CySQL query
        mock_ce_client_highvalue.execute_query.assert_called_once()
        call_args = mock_ce_client_highvalue.execute_query.call_args[0][0]
        assert "MATCH (u:User)" in call_args
        assert "u.system_tags = \"admin_tier_0\"" in call_args
        assert "NORTH.SEVENKINGDOMS.LOCAL" in call_args
    
    def test_get_admin_users_empty_response(self, mock_ce_client):
        """Test admin user enumeration with empty response"""
        mock_ce_client.execute_query.return_value = []
        
        admin_users = mock_ce_client.get_admin_users("empty.domain.local")
        
        assert len(admin_users) == 0
    
    def test_get_highvalue_users_empty_response(self, mock_ce_client):
        """Test high value user enumeration with empty response"""
        mock_ce_client.execute_query.return_value = []
        
        hv_users = mock_ce_client.get_highvalue_users("empty.domain.local")
        
        assert len(hv_users) == 0
    
    def test_get_admin_users_exception_handling(self, mock_ce_client):
        """Test exception handling in get_admin_users"""
        mock_ce_client.execute_query.side_effect = Exception("Query error")
        
        admin_users = mock_ce_client.get_admin_users("error.domain.local")
        
        assert len(admin_users) == 0
    
    def test_get_highvalue_users_exception_handling(self, mock_ce_client):
        """Test exception handling in get_highvalue_users"""
        mock_ce_client.execute_query.side_effect = Exception("Query error")
        
        hv_users = mock_ce_client.get_highvalue_users("error.domain.local")
        
        assert len(hv_users) == 0


class TestCLICommands:
    """Test CLI commands end-to-end with mocked BloodHound CE"""
    
    @pytest.fixture
    def mock_ce_client_complete(self):
        """Create a complete CE client with all mocked data"""
        client = BloodHoundCEClient(
            base_url="http://localhost:8080",
            debug=False,
            verbose=False
        )
        
        # Mock execute_query to return different data based on query type
        def mock_execute_query(query):
            if "u.enabled = true" in query and "User" in query and "admincount" not in query and "system_tags" not in query:
                # get_users query - only enabled users (vagrant and krbtgt are disabled)
                return [
                    {"samaccountname": "jeor.mormont", "name": "JEOR.MORMONT@NORTH.SEVENKINGDOMS.LOCAL", "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"},
                    {"samaccountname": "sql_svc", "name": "SQL_SVC@NORTH.SEVENKINGDOMS.LOCAL", "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"},
                    {"samaccountname": "samwell.tarly", "name": "SAMWELL.TARLY@NORTH.SEVENKINGDOMS.LOCAL", "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"},
                    {"samaccountname": "hodor", "name": "HODOR@NORTH.SEVENKINGDOMS.LOCAL", "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"},
                    {"samaccountname": "brandon.stark", "name": "BRANDON.STARK@NORTH.SEVENKINGDOMS.LOCAL", "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"},
                    {"samaccountname": "robb.stark", "name": "ROBB.STARK@NORTH.SEVENKINGDOMS.LOCAL", "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"},
                    {"samaccountname": "rickon.stark", "name": "RICKON.STARK@NORTH.SEVENKINGDOMS.LOCAL", "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"},
                    {"samaccountname": "jon.snow", "name": "JON.SNOW@NORTH.SEVENKINGDOMS.LOCAL", "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"},
                    {"samaccountname": "catelyn.stark", "name": "CATELYN.STARK@NORTH.SEVENKINGDOMS.LOCAL", "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"},
                    {"samaccountname": "sansa.stark", "name": "SANSA.STARK@NORTH.SEVENKINGDOMS.LOCAL", "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"},
                    {"samaccountname": "eddard.stark", "name": "EDDARD.STARK@NORTH.SEVENKINGDOMS.LOCAL", "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"},
                    {"samaccountname": "arya.stark", "name": "ARYA.STARK@NORTH.SEVENKINGDOMS.LOCAL", "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"},
                    {"samaccountname": "Administrator", "name": "ADMINISTRATOR@NORTH.SEVENKINGDOMS.LOCAL", "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"}
                ]
            elif "u.admincount = true" in query and "u.enabled = true" in query:
                # get_admin_users query - only enabled admin users
                return [
                    {"samaccountname": "robb.stark", "name": "ROBB.STARK@NORTH.SEVENKINGDOMS.LOCAL", "admincount": True, "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"},
                    {"samaccountname": "catelyn.stark", "name": "CATELYN.STARK@NORTH.SEVENKINGDOMS.LOCAL", "admincount": True, "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"},
                    {"samaccountname": "eddard.stark", "name": "EDDARD.STARK@NORTH.SEVENKINGDOMS.LOCAL", "admincount": True, "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"},
                    {"samaccountname": "Administrator", "name": "ADMINISTRATOR@NORTH.SEVENKINGDOMS.LOCAL", "admincount": True, "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"}
                ]
            elif "u.system_tags = \"admin_tier_0\"" in query and "u.enabled = true" in query:
                # get_highvalue_users query - only enabled high value users
                return [
                    {"samaccountname": "robb.stark", "name": "ROBB.STARK@NORTH.SEVENKINGDOMS.LOCAL", "system_tags": "admin_tier_0", "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"},
                    {"samaccountname": "catelyn.stark", "name": "CATELYN.STARK@NORTH.SEVENKINGDOMS.LOCAL", "system_tags": "admin_tier_0", "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"},
                    {"samaccountname": "eddard.stark", "name": "EDDARD.STARK@NORTH.SEVENKINGDOMS.LOCAL", "system_tags": "admin_tier_0", "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"},
                    {"samaccountname": "Administrator", "name": "ADMINISTRATOR@NORTH.SEVENKINGDOMS.LOCAL", "system_tags": "admin_tier_0", "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"}
                ]
            elif "c.enabled = true" in query and "Computer" in query:
                # get_computers query
                return [
                    {"name": "WINTERFELL.NORTH.SEVENKINGDOMS.LOCAL", "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"},
                    {"name": "CASTELBLACK.NORTH.SEVENKINGDOMS.LOCAL", "enabled": True, "domain": "NORTH.SEVENKINGDOMS.LOCAL"}
                ]
            else:
                return []
        
        client.execute_query = Mock(side_effect=mock_execute_query)
        return client
    
    def test_user_command_simulation(self, mock_ce_client_complete):
        """Test user command simulation - simulates: python3 -m src.bloodhound_cli.main --edition ce user -d north.sevenkingdoms.local"""
        # Simulate the user command execution
        users = mock_ce_client_complete.get_users("north.sevenkingdoms.local")
        
        # Verify the expected output matches real CLI output
        expected_users = [
            "jeor.mormont", "sql_svc", "samwell.tarly", "hodor", "brandon.stark",
            "robb.stark", "rickon.stark", "jon.snow", "catelyn.stark", "sansa.stark",
            "eddard.stark", "arya.stark", "Administrator"
        ]
        
        assert len(users) == 13
        for user in expected_users:
            assert user in users
        
        # Verify the correct CySQL query was executed
        mock_ce_client_complete.execute_query.assert_called()
        call_args = mock_ce_client_complete.execute_query.call_args[0][0]
        assert "MATCH (u:User)" in call_args
        assert "u.enabled = true" in call_args
        assert "NORTH.SEVENKINGDOMS.LOCAL" in call_args
    
    def test_admin_command_simulation(self, mock_ce_client_complete):
        """Test admin command simulation - simulates: python3 -m src.bloodhound_cli.main --edition ce admin -d north.sevenkingdoms.local"""
        # Simulate the admin command execution
        admin_users = mock_ce_client_complete.get_admin_users("north.sevenkingdoms.local")
        
        # Verify the expected output matches real CLI output
        expected_admin_users = [
            "robb.stark", "catelyn.stark", "eddard.stark", "Administrator"
        ]
        
        assert len(admin_users) == 4
        for user in expected_admin_users:
            assert user in admin_users
        
        # Verify the correct CySQL query was executed
        mock_ce_client_complete.execute_query.assert_called()
        call_args = mock_ce_client_complete.execute_query.call_args[0][0]
        assert "MATCH (u:User)" in call_args
        assert "u.admincount = true" in call_args
        assert "NORTH.SEVENKINGDOMS.LOCAL" in call_args
    
    def test_highvalue_command_simulation(self, mock_ce_client_complete):
        """Test highvalue command simulation - simulates: python3 -m src.bloodhound_cli.main --edition ce highvalue -d north.sevenkingdoms.local"""
        # Simulate the highvalue command execution
        hv_users = mock_ce_client_complete.get_highvalue_users("north.sevenkingdoms.local")
        
        # Verify the expected output matches real CLI output
        expected_hv_users = [
            "robb.stark", "catelyn.stark", "eddard.stark", "Administrator"
        ]
        
        assert len(hv_users) == 4
        for user in expected_hv_users:
            assert user in hv_users
        
        # Verify the correct CySQL query was executed
        mock_ce_client_complete.execute_query.assert_called()
        call_args = mock_ce_client_complete.execute_query.call_args[0][0]
        assert "MATCH (u:User)" in call_args
        assert "u.system_tags = \"admin_tier_0\"" in call_args
        assert "NORTH.SEVENKINGDOMS.LOCAL" in call_args
    
    def test_computer_command_simulation(self, mock_ce_client_complete):
        """Test computer command simulation - simulates: python3 -m src.bloodhound_cli.main --edition ce computer -d north.sevenkingdoms.local"""
        # Simulate the computer command execution
        computers = mock_ce_client_complete.get_computers("north.sevenkingdoms.local")
        
        # Verify the expected output matches real CLI output
        expected_computers = [
            "winterfell.north.sevenkingdoms.local", "castelblack.north.sevenkingdoms.local"
        ]
        
        assert len(computers) == 2
        for computer in expected_computers:
            assert computer in computers
        
        # Verify the correct CySQL query was executed
        mock_ce_client_complete.execute_query.assert_called()
        call_args = mock_ce_client_complete.execute_query.call_args[0][0]
        assert "MATCH (c:Computer)" in call_args
        assert "c.enabled = true" in call_args
        assert "NORTH.SEVENKINGDOMS.LOCAL" in call_args
    
    def test_all_commands_consistency(self, mock_ce_client_complete):
        """Test that all commands work consistently and return expected data"""
        # Test all commands with the same domain
        domain = "north.sevenkingdoms.local"
        
        # Execute all commands
        users = mock_ce_client_complete.get_users(domain)
        admin_users = mock_ce_client_complete.get_admin_users(domain)
        hv_users = mock_ce_client_complete.get_highvalue_users(domain)
        computers = mock_ce_client_complete.get_computers(domain)
        
        # Verify counts match expected real data
        assert len(users) == 13, f"Expected 13 users, got {len(users)}"
        assert len(admin_users) == 4, f"Expected 4 admin users, got {len(admin_users)}"
        assert len(hv_users) == 4, f"Expected 4 high value users, got {len(hv_users)}"
        assert len(computers) == 2, f"Expected 2 computers, got {len(computers)}"
        
        # Verify that all admin users are enabled and appear in regular users
        for admin_user in admin_users:
            assert admin_user in users, f"Admin user {admin_user} should be in all users"
        
        # Verify that high value users are a subset of admin users
        for hv_user in hv_users:
            assert hv_user in admin_users, f"High value user {hv_user} should be in admin users"
        
        # Verify no disabled users are included in any results
        assert "krbtgt" not in users, "Disabled user krbtgt should not be in regular users"
        assert "krbtgt" not in admin_users, "Disabled user krbtgt should not be in admin users"
        assert "vagrant" not in users, "Disabled user vagrant should not be in regular users"
        assert "vagrant" not in admin_users, "Disabled user vagrant should not be in admin users"

    def test_group_command_outputs_recursive_memberships(self, monkeypatch, capsys):
        """Simulate `bloodhound-cli group -u daenerys.targaryen -d essos.local` output."""
        expected_groups = [
            "DRAGONSFRIENDS@ESSOS.LOCAL",
            "TARGARYEN@ESSOS.LOCAL",
            "ACROSSTHENARROWSEA@SEVENKINGDOMS.LOCAL",
            "EVERYONE@ESSOS.LOCAL",
            "AUTHENTICATED USERS@ESSOS.LOCAL",
            "DENIED RODC PASSWORD REPLICATION GROUP@ESSOS.LOCAL",
            "PRE-WINDOWS 2000 COMPATIBLE ACCESS@ESSOS.LOCAL",
            "DOMAIN ADMINS@ESSOS.LOCAL",
            "DOMAIN USERS@ESSOS.LOCAL",
            "REMOTE DESKTOP USERS@ESSOS.LOCAL",
            "USERS@ESSOS.LOCAL",
            "ADMINISTRATORS@ESSOS.LOCAL",
        ]

        class DummyClient:
            def __init__(self):
                self.closed = False
                self.calls = []

            def get_user_groups(self, domain, username, recursive=True):
                self.calls.append((domain, username, recursive))
                assert recursive is True
                return expected_groups

            def close(self):
                self.closed = True

        dummy_client = DummyClient()
        monkeypatch.setattr(
            cli_main,
            "get_client",
            lambda *_, **__: dummy_client,
        )

        args = SimpleNamespace(
            edition="ce",
            uri=None,
            user=None,
            password=None,
            base_url="http://localhost:8080",
            username="admin",
            ce_password="Bloodhound123!",
            debug=False,
            verbose=False,
            domain="essos.local",
            group_user="daenerys.targaryen",
            direct_only=False,
            output=None,
        )

        cli_main.cmd_group(args)

        captured = capsys.readouterr()
        assert captured.out.strip().splitlines() == expected_groups
        assert dummy_client.calls == [("essos.local", "daenerys.targaryen", True)]
        assert dummy_client.closed is True

    def test_user_command_ou_filter_outputs_expected_users(self, monkeypatch, capsys):
        """Simulate `bloodhound-cli user --ou-dn ... -d sevenkingdoms.local` output."""
        expected_users = [
            "maester.pycelle",
            "lord.varys",
            "petyer.baelish",
            "stannis.baratheon",
            "joffrey.baratheon",
            "renly.baratheon",
            "robert.baratheon",
            "cersei.lannister",
            "jaime.lannister",
            "tywin.lannister",
        ]

        class DummyClient:
            def __init__(self):
                self.closed = False
                self.calls = []

            def get_users_in_ou(self, domain, ou_distinguished_name):
                self.calls.append((domain, ou_distinguished_name))
                return expected_users

            def close(self):
                self.closed = True

        dummy_client = DummyClient()
        monkeypatch.setattr(
            cli_main,
            "get_client",
            lambda *_, **__: dummy_client,
        )

        args = SimpleNamespace(
            edition="ce",
            uri=None,
            user=None,
            password=None,
            base_url="http://localhost:8080",
            username="admin",
            ce_password="Bloodhound123!",
            debug=False,
            verbose=False,
            domain="sevenkingdoms.local",
            ou_dn="OU=crownlands,DC=sevenkingdoms,DC=local",
            high_value=False,
            admin_count=False,
            password_never_expires=False,
            password_not_required=False,
            password_last_change=False,
            output=None,
        )

        cli_main.cmd_users(args)

        captured = capsys.readouterr()
        assert captured.out.strip().splitlines() == expected_users
        assert dummy_client.calls == [
            ("sevenkingdoms.local", "OU=crownlands,DC=sevenkingdoms,DC=local")
        ]
        assert dummy_client.closed is True

    def test_version_command_prints_version(self, capsys):
        """Ensure `bloodhound-cli version` prints the version string."""
        cli_main.cmd_version(SimpleNamespace())
        captured = capsys.readouterr()
        assert captured.out.strip() == f"bloodhound-cli {cli_main.get_cli_version()}"

    @pytest.fixture
    def mock_ce_client_graph(self):
        client = BloodHoundCEClient(
            base_url="http://localhost:8080",
            debug=False,
            verbose=False
        )
        client.logger = Mock()
        client._debug = Mock()
        return client

    def test_get_critical_aces_processes_graph(self, mock_ce_client_graph):
        nodes = {
            "100": {
                "properties": {"samaccountname": "alice", "domain": "ESSOS.LOCAL"},
                "kind": "User",
            },
            "200": {
                "properties": {"samaccountname": "acl_group", "domain": "ESSOS.LOCAL"},
                "kind": "Group",
            },
            "300": {
                "properties": {
                    "samaccountname": "server$",
                    "domain": "ESSOS.LOCAL",
                    "enabled": False,
                },
                "kind": "Computer",
            },
        }
        edges = [{"source": "200", "target": "300", "label": "GenericAll", "properties": {}}]
        mock_ce_client_graph.execute_query_with_relationships = Mock(return_value={
            "nodes": nodes,
            "edges": edges,
        })

        aces = mock_ce_client_graph.get_critical_aces(
            source_domain="essos.local",
            high_value=False,
            username="alice",
            target_domain="all",
            relation="all",
        )

        assert len(aces) == 1
        entry = aces[0]
        assert entry["source"] == "alice"
        assert entry["target"] == "server$"
        assert entry["relation"] == "GenericAll"
        assert entry["targetEnabled"] is False

    def test_get_critical_aces_includes_high_value_filter(self, mock_ce_client_graph):
        mock_ce_client_graph.execute_query_with_relationships = Mock(return_value={"nodes": {}, "edges": []})
        mock_ce_client_graph.get_critical_aces(
            source_domain="essos.local",
            high_value=True,
            username="all",
            target_domain="all",
            relation="all",
        )
        query = mock_ce_client_graph.execute_query_with_relationships.call_args[0][0]
        assert 'system_tags = "admin_tier_0"' in query
        assert "NOT m.system_tags" not in query

    def test_get_critical_aces_username_filter_matches_name(self, mock_ce_client_graph):
        mock_ce_client_graph.execute_query_with_relationships = Mock(return_value={"nodes": {}, "edges": []})
        mock_ce_client_graph.get_critical_aces(
            source_domain="sevenkingdoms.local",
            high_value=False,
            username="small council",
            target_domain="all",
            relation="all",
        )
        query = mock_ce_client_graph.execute_query_with_relationships.call_args[0][0]
        assert "toLower(n.samaccountname)" in query
        assert "toLower(n.name)" in query
        assert "small council" in query

    def test_get_access_paths_trims_upn(self, mock_ce_client_graph):
        mock_ce_client_graph.execute_query = Mock(return_value=[
            {"source": "user@ESSOS.LOCAL", "target": "SERVER@ESSOS.LOCAL", "relation": "Owns"}
        ])

        paths = mock_ce_client_graph.get_access_paths(
            source="user",
            connection="all",
            target="all",
            domain="ESSOS.LOCAL",
        )

        assert len(paths) == 1
        assert paths[0]["source"] == "user"
        assert paths[0]["target"] == "SERVER"
        assert paths[0]["relation"] == "Owns"

    def test_get_users_with_dc_access_primary_query(self, mock_ce_client_graph):
        mock_ce_client_graph.execute_query = Mock(return_value=[
            {"user": "alice@essos.local", "dc": "dc01@essos.local", "relation": "AdminTo"}
        ])

        results = mock_ce_client_graph.get_users_with_dc_access("essos.local")

        assert results == [
            {"source": "alice", "target": "dc01", "path": "alice -> dc01 (AdminTo)"}
        ]
        assert mock_ce_client_graph.execute_query.call_count == 1

    def test_get_users_with_dc_access_fallback_query(self, mock_ce_client_graph):
        mock_ce_client_graph.execute_query = Mock(side_effect=[
            [],
            [{"user": "alice@essos.local", "computer": "ws01@essos.local", "relation": "CanRDP"}],
        ])

        results = mock_ce_client_graph.get_users_with_dc_access("essos.local")

        assert results == [
            {"source": "alice", "target": "ws01", "path": "alice -> ws01 (CanRDP)"}
        ]
        assert mock_ce_client_graph.execute_query.call_count == 2

    def test_get_critical_aces_by_domain_formats_results(self, mock_ce_client_graph):
        mock_ce_client_graph.execute_query = Mock(return_value=[
            {"name": "alice@essos.local", "relation": "GenericAll"}
        ])

        aces = mock_ce_client_graph.get_critical_aces_by_domain("essos.local", blacklist=[], high_value=False)

        assert aces == [{"source": "alice", "relation": "GenericAll", "target": "alice"}]

    def test_headers_include_authorization(self):
        with patch.object(BloodHoundCEClient, "_load_config", return_value=None):
            client = BloodHoundCEClient(base_url="http://localhost:8080", api_token="abc123")
        headers = client._get_headers()
        assert headers["Authorization"] == "Bearer abc123"
        assert "User-Agent" in headers

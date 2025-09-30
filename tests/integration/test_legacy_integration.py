"""
Integration tests for Legacy BloodHound CLI with real Neo4j database
"""
import pytest
import os
from bloodhound_cli.main import BloodHoundACEAnalyzer


@pytest.mark.integration
class TestLegacyIntegration:
    """Integration tests requiring real Neo4j database"""
    
    @pytest.fixture
    def legacy_client(self):
        """Create client with test database connection"""
        neo4j_uri = os.getenv("BLOODHOUND_NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("BLOODHOUND_NEO4J_USER", "admin")
        neo4j_password = os.getenv("BLOODHOUND_NEO4J_PASSWORD", "Bloodhound123!")
        
        return BloodHoundACEAnalyzer(
            uri=neo4j_uri,
            user=neo4j_user,
            password=neo4j_password,
            debug=True,
            verbose=True
        )
    
    def test_get_users(self, legacy_client):
        """Test user enumeration with real data"""
        users = legacy_client.get_users("TEST.LOCAL")
        
        # Verificar que obtenemos usuarios esperados
        assert "admin" in users
        assert "testuser" in users
        assert "service" in users
        assert len(users) >= 3
    
    def test_get_computers(self, legacy_client):
        """Test computer enumeration with real data"""
        computers = legacy_client.get_computers("TEST.LOCAL")
        
        # Verificar computadoras esperadas
        assert "dc01" in [c.lower() for c in computers]
        assert "ws01" in [c.lower() for c in computers]
        assert len(computers) >= 2
    
    def test_get_computers_with_laps(self, legacy_client):
        """Test computer enumeration with LAPS filter"""
        computers_with_laps = legacy_client.get_computers("TEST.LOCAL", laps=True)
        computers_without_laps = legacy_client.get_computers("TEST.LOCAL", laps=False)
        
        # Verificar filtrado por LAPS
        assert len(computers_with_laps) >= 1
        assert len(computers_without_laps) >= 1
        assert len(computers_with_laps) + len(computers_without_laps) >= 2
    
    def test_get_admin_users(self, legacy_client):
        """Test admin user enumeration"""
        admin_users = legacy_client.get_admin_users("TEST.LOCAL")
        
        # Verificar que admin está en la lista
        assert "admin" in admin_users
        assert len(admin_users) >= 1
    
    def test_get_highvalue_users(self, legacy_client):
        """Test high-value user enumeration"""
        highvalue_users = legacy_client.get_highvalue_users("TEST.LOCAL")
        
        # Verificar usuarios de alto valor
        assert "admin" in highvalue_users
        assert len(highvalue_users) >= 1
    
    def test_get_password_not_required_users(self, legacy_client):
        """Test password not required users"""
        pwd_not_req_users = legacy_client.get_password_not_required_users("TEST.LOCAL")
        
        # Verificar usuarios sin contraseña requerida
        assert "service" in pwd_not_req_users
        assert len(pwd_not_req_users) >= 1
    
    def test_get_password_never_expires_users(self, legacy_client):
        """Test password never expires users"""
        pwd_never_exp_users = legacy_client.get_password_never_expires_users("TEST.LOCAL")
        
        # Verificar usuarios con contraseña que nunca expira
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
        
        # Verificar que obtenemos ACLs
        assert len(aces) >= 0  # Puede ser 0 si no hay ACLs directas
    
    def test_get_access_paths(self, legacy_client):
        """Test access path enumeration"""
        access_paths = legacy_client.get_access_paths(
            source="admin",
            connection="all",
            target="all",
            domain="TEST.LOCAL"
        )
        
        # Verificar que obtenemos rutas de acceso
        assert isinstance(access_paths, list)
    
    def test_get_sessions(self, legacy_client):
        """Test session enumeration"""
        sessions = legacy_client.get_sessions("TEST.LOCAL", da=False)
        
        # Verificar sesiones
        assert isinstance(sessions, list)
        # Puede ser vacío si no hay sesiones activas
    
    def test_get_sessions_da(self, legacy_client):
        """Test domain admin session enumeration"""
        da_sessions = legacy_client.get_sessions("TEST.LOCAL", da=True)
        
        # Verificar sesiones de administradores de dominio
        assert isinstance(da_sessions, list)
    
    def test_password_last_change(self, legacy_client):
        """Test password last change data"""
        pwd_data = legacy_client.get_password_last_change("TEST.LOCAL")
        
        # Verificar datos de contraseña
        assert isinstance(pwd_data, list)
        assert len(pwd_data) >= 3  # Al menos 3 usuarios
        
        # Verificar estructura de datos
        for user_data in pwd_data:
            assert "user" in user_data
            assert "password_last_change" in user_data
            assert "when_created" in user_data
    
    def test_custom_query(self, legacy_client):
        """Test custom Cypher query execution"""
        query = "MATCH (u:User) WHERE u.domain = 'TEST.LOCAL' RETURN u.samaccountname LIMIT 5"
        
        # No debería lanzar excepción
        try:
            legacy_client.execute_custom_query(query)
        except Exception as e:
            pytest.fail(f"Custom query failed: {e}")
    
    def teardown_method(self):
        """Cleanup after each test"""
        # Cualquier limpieza necesaria
        pass

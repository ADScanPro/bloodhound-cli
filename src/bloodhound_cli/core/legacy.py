"""
Legacy BloodHound implementation using Neo4j
"""
from typing import List, Dict, Optional
from neo4j import GraphDatabase
from .base import BloodHoundClient


class BloodHoundLegacyClient(BloodHoundClient):
    """Legacy BloodHound client using Neo4j"""
    
    def __init__(self, uri: str, user: str, password: str, debug: bool = False, verbose: bool = False):
        super().__init__(debug, verbose)
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def execute_query(self, query: str, **params) -> List[Dict]:
        """Execute a Cypher query"""
        with self.driver.session() as session:
            return session.run(query, **params).data()
    
    def get_users(self, domain: str) -> List[str]:
        query = """
        MATCH (u:User)
        WHERE u.enabled = true AND toLower(u.domain) = toLower($domain)
        RETURN u.samaccountname AS samaccountname
        """
        results = self.execute_query(query, domain=domain)
        return [record["samaccountname"] for record in results]
    
    def get_computers(self, domain: str, laps: Optional[bool] = None) -> List[str]:
        if laps is None:
            query = """
            MATCH (c:Computer)
            WHERE toLower(c.domain) = toLower($domain) AND c.enabled = true
            RETURN toLower(c.name) AS name
            """
            params = {"domain": domain}
        else:
            query = """
            MATCH (c:Computer)
            WHERE toLower(c.domain) = toLower($domain)
              AND c.haslaps = $laps AND c.enabled = true
            RETURN toLower(c.name) AS name
            """
            params = {"domain": domain, "laps": laps}
        results = self.execute_query(query, **params)
        return [record["name"] for record in results]
    
    def get_admin_users(self, domain: str) -> List[str]:
        query = """
        MATCH (u:User)
        WHERE u.enabled = true AND toLower(u.domain) = toLower($domain)
          AND u.admincount = true
        RETURN u.samaccountname AS samaccountname
        """
        results = self.execute_query(query, domain=domain)
        return [record["samaccountname"] for record in results]
    
    def get_highvalue_users(self, domain: str) -> List[str]:
        query = """
        MATCH (u:User)
        WHERE u.enabled = true AND toLower(u.domain) = toLower($domain)
          AND u.highvalue = true
        RETURN u.samaccountname AS samaccountname
        """
        results = self.execute_query(query, domain=domain)
        return [record["samaccountname"] for record in results]
    
    def get_password_not_required_users(self, domain: str) -> List[str]:
        query = """
        MATCH (u:User)
        WHERE u.enabled = true AND toLower(u.domain) = toLower($domain)
          AND u.passwordnotreqd = true
        RETURN u.samaccountname AS samaccountname
        """
        results = self.execute_query(query, domain=domain)
        return [record["samaccountname"] for record in results]
    
    def get_password_never_expires_users(self, domain: str) -> List[str]:
        query = """
        MATCH (u:User)
        WHERE u.enabled = true AND toLower(u.domain) = toLower($domain)
          AND u.pwdneverexpires = true
        RETURN u.samaccountname AS samaccountname
        """
        results = self.execute_query(query, domain=domain)
        return [record["samaccountname"] for record in results]
    
    def get_sessions(self, domain: str, da: bool = False) -> List[Dict]:
        if da:
            query = """
            MATCH (c:Computer)-[r:HasSession]->(u:User)
            WHERE toLower(c.domain) = toLower($domain) AND u.enabled = true
            RETURN c.name AS computer, u.samaccountname AS user
            """
        else:
            query = """
            MATCH (u:User)-[r:HasSession]->(c:Computer)
            WHERE toLower(u.domain) = toLower($domain) AND u.enabled = true
            RETURN u.samaccountname AS user, c.name AS computer
            """
        return self.execute_query(query, domain=domain)
    
    def get_password_last_change(self, domain: str, user: Optional[str] = None) -> List[Dict]:
        if user:
            query = """
            MATCH (u:User)
            WHERE u.enabled = true AND toLower(u.domain) = toLower($domain)
              AND u.samaccountname = $user
            RETURN u.samaccountname AS samaccountname, u.pwdlastset AS pwdlastset, u.whencreated AS whencreated
            """
            params = {"domain": domain, "user": user}
        else:
            query = """
            MATCH (u:User)
            WHERE u.enabled = true AND toLower(u.domain) = toLower($domain)
            RETURN u.samaccountname AS samaccountname, u.pwdlastset AS pwdlastset, u.whencreated AS whencreated
            """
            params = {"domain": domain}
        return self.execute_query(query, **params)
    
    def get_critical_aces(self, source_domain: str, high_value: bool = False, 
                         username: str = "all", target_domain: str = "all", 
                         relation: str = "all") -> List[Dict]:
        # Implementation for critical ACEs
        query = """
        MATCH (s)-[r]->(t)
        WHERE toLower(s.domain) = toLower($source_domain)
        RETURN s.name AS source, r.relation AS relation, t.name AS target
        """
        return self.execute_query(query, source_domain=source_domain)
    
    def get_access_paths(self, source: str, connection: str, target: str, domain: str) -> List[Dict]:
        # Implementation for access paths
        query = """
        MATCH path = (s)-[*1..10]->(t)
        WHERE s.name = $source AND t.name = $target
        RETURN path
        """
        return self.execute_query(query, source=source, target=target)
    
    def get_critical_aces_by_domain(self, domain: str, blacklist: List[str], 
                                   high_value: bool = False) -> List[Dict]:
        # Implementation for critical ACEs by domain
        query = """
        MATCH (s)-[r]->(t)
        WHERE toLower(s.domain) = toLower($domain)
        RETURN s.name AS source, r.relation AS relation, t.name AS target
        """
        return self.execute_query(query, domain=domain)
    
    def close(self):
        """Close the Neo4j driver"""
        if hasattr(self, 'driver'):
            self.driver.close()

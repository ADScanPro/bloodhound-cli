"""
BloodHound CE implementation using HTTP API
"""
import requests
import os
import configparser
from typing import List, Dict, Optional
from pathlib import Path
from .base import BloodHoundClient


class BloodHoundCEClient(BloodHoundClient):
    """BloodHound CE client using HTTP API"""
    
    def __init__(self, base_url: str = None, api_token: Optional[str] = None, 
                 debug: bool = False, verbose: bool = False, verify: bool = True):
        super().__init__(debug, verbose)
        
        # Try to load configuration from ~/.bloodhound_config
        config = self._load_config()
        if config:
            self.base_url = config.get('base_url', base_url or 'http://localhost:8080')
            self.api_token = config.get('api_token', api_token)
        else:
            self.base_url = (base_url or 'http://localhost:8080').rstrip("/")
            self.api_token = api_token
            
        self.verify = verify
        self.session = requests.Session()
        if self.api_token:
            self.session.headers.update({"Authorization": f"Bearer {self.api_token}"})
    
    def _load_config(self) -> Optional[Dict[str, str]]:
        """Load configuration from ~/.bloodhound_config file"""
        config_path = os.path.expanduser("~/.bloodhound_config")
        if not os.path.exists(config_path):
            return None
            
        try:
            config = configparser.ConfigParser()
            config.read(config_path)
            
            if 'CE' in config:
                return {
                    'base_url': config['CE'].get('base_url'),
                    'api_token': config['CE'].get('api_token')
                }
        except Exception:
            pass
            
        return None
    
    def authenticate(self, username: str, password: str, login_path: str = "/api/v2/login") -> Optional[str]:
        """Authenticate against CE and return token"""
        url = f"{self.base_url}{login_path}"
        try:
            payload = {"login_method": "secret", "username": username, "secret": password}
            response = self.session.post(url, json=payload, verify=self.verify, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("data", {}).get("session_token")
                if token:
                    self.api_token = token
                    self.session.headers.update({"Authorization": f"Bearer {token}"})
                    return token
            return None
        except Exception:
            return None
    
    def execute_query(self, query: str, **params) -> List[Dict]:
        """Execute a Cypher query using BloodHound CE API"""
        try:
            url = f"{self.base_url}/api/v2/graphs/cypher"
            
            # Clean up query: normalize whitespace but preserve structure
            # Using split() + join() preserves all non-whitespace characters
            cleaned_query = ' '.join(query.split())
            
            payload = {
                "query": cleaned_query,
                "include_properties": True
            }
            
            # Show query in debug mode - use plain text to avoid rendering issues
            if self.debug:
                print("\n" + "="*80)
                print("Debug: Cypher Query")
                print("="*80)
                print(query)
                print("="*80)
                print(f"Debug: Cleaned Query: {cleaned_query}")
                print(f"Debug: API URL: {url}")
                print("="*80 + "\n")
            
            response = self.session.post(url, json=payload, verify=self.verify, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                if self.debug:
                    print(f"Debug: Response data keys: {data.keys() if isinstance(data, dict) else 'not a dict'}")
                    if "data" in data:
                        print(f"Debug: Data keys: {data['data'].keys() if isinstance(data.get('data'), dict) else 'not a dict'}")
                
                # BloodHound CE returns data in a different format
                if "data" in data and "nodes" in data["data"]:
                    # Convert nodes to list format
                    nodes = []
                    for node_id, node_data in data["data"]["nodes"].items():
                        if "properties" in node_data:
                            nodes.append(node_data["properties"])
                    return nodes
                return []
            else:
                if self.debug:
                    print(f"Debug: API returned status code {response.status_code}")
                    print(f"Debug: Response: {response.text}")
                return []
                
        except Exception as e:
            if self.debug:
                print(f"Debug: Exception in execute_query: {e}")
                import traceback
                traceback.print_exc()
            return []
    
    def execute_query_with_relationships(self, query: str) -> Dict:
        """Execute a Cypher query and return both nodes and edges"""
        try:
            url = f"{self.base_url}/api/v2/graphs/cypher"
            
            # Clean up query: normalize whitespace but preserve structure
            # Using split() + join() preserves all non-whitespace characters
            cleaned_query = ' '.join(query.split())
            
            payload = {
                "query": cleaned_query,
                "include_properties": True
            }
            
            # Show query in debug mode - use plain text to avoid rendering issues
            if self.debug:
                print("\n" + "="*80)
                print("Debug: Cypher Query (with relationships)")
                print("="*80)
                print(query)
                print("="*80)
                print(f"Debug: Cleaned Query: {cleaned_query}")
                print(f"Debug: API URL: {url}")
                print(f"Debug: Auth Token: {'Set' if self.api_token else 'Not set'}")
                print("="*80 + "\n")
            
            response = self.session.post(url, json=payload, verify=self.verify, timeout=60)
            
            if self.debug:
                print(f"Debug: Response status code: {response.status_code}")
                print(f"Debug: Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                
                if self.debug:
                    print(f"Debug: Full response: {data}")
                
                return data.get("data", {})
            else:
                if self.debug:
                    print(f"Debug: API returned status code {response.status_code}")
                    print(f"Debug: Response: {response.text}")
                    try:
                        error_json = response.json()
                        print(f"Debug: Error details: {error_json}")
                    except:
                        pass
                return {}
                
        except Exception as e:
            if self.debug:
                print(f"Debug: Exception in execute_query_with_relationships: {e}")
                import traceback
                traceback.print_exc()
            return {}
    
    def get_users(self, domain: str) -> List[str]:
        """Get enabled users using CySQL query"""
        try:
            # Use CySQL query to get enabled users in specific domain
            cypher_query = f"""
            MATCH (u:User) 
            WHERE u.enabled = true AND toUpper(u.domain) = '{domain.upper()}'
            RETURN u
            """
            
            result = self.execute_query(cypher_query)
            users = []
            
            # execute_query returns a list of node properties
            if result and isinstance(result, list):
                for node_properties in result:
                    samaccountname = node_properties.get('samaccountname') or node_properties.get('name', '')
                    if samaccountname:
                        # Extract just the username part (before @) if it's in UPN format
                        if "@" in samaccountname:
                            samaccountname = samaccountname.split("@")[0]
                        users.append(samaccountname)
            
            return users

        except Exception:
            return []
    
    def get_computers(self, domain: str, laps: Optional[bool] = None) -> List[str]:
        """Get enabled computers using CySQL query"""
        try:
            # Build CySQL query with optional LAPS filter
            if laps is not None:
                laps_condition = "true" if laps else "false"
                cypher_query = f"""
                MATCH (c:Computer) 
                WHERE c.enabled = true AND c.haslaps = {laps_condition} AND toUpper(c.domain) = '{domain.upper()}'
                RETURN c
                """
            else:
                cypher_query = f"""
                MATCH (c:Computer) 
                WHERE c.enabled = true AND toUpper(c.domain) = '{domain.upper()}'
                RETURN c
                """
            
            result = self.execute_query(cypher_query)
            computers = []
            
            # execute_query returns a list of node properties
            if result and isinstance(result, list):
                for node_properties in result:
                    computer_name = node_properties.get('name', '')
                    if computer_name:
                        # Extract just the computer name part (before @) if it's in UPN format
                        if "@" in computer_name:
                            computer_name = computer_name.split("@")[0]
                        
                        computers.append(computer_name.lower())
            
            return computers

        except Exception:
            return []
    
    def get_admin_users(self, domain: str) -> List[str]:
        """Get enabled admin users using CySQL query (admincount approach)"""
        try:
            # Use CySQL query to get enabled users with admincount = true in specific domain
            # Note: CySQL has stricter typing and different null handling
            cypher_query = f"""
            MATCH (u:User) 
            WHERE u.admincount = true AND u.enabled = true AND toUpper(u.domain) = '{domain.upper()}'
            RETURN u
            """
            
            result = self.execute_query(cypher_query)
            admin_users = []
            
            # execute_query returns a list of node properties
            if result and isinstance(result, list):
                for node_properties in result:
                    if node_properties.get('admincount') is True:
                        samaccountname = node_properties.get('samaccountname') or node_properties.get('name', '')
                        if samaccountname:
                            # Extract just the username part (before @) if it's in UPN format
                            if "@" in samaccountname:
                                samaccountname = samaccountname.split("@")[0]
                            admin_users.append(samaccountname)
            
            return admin_users

        except Exception:
            return []
    
    def get_highvalue_users(self, domain: str) -> List[str]:
        """Get enabled high value users using CySQL query (system_tags approach)"""
        try:
            # In BloodHound CE, tier 0 (high value) users are identified by system_tags = "admin_tier_0"
            # This indicates users in critical administrative groups (Domain Admins, etc.)
            cypher_query = f"""
            MATCH (u:User) 
            WHERE u.system_tags = "admin_tier_0" AND u.enabled = true AND toUpper(u.domain) = '{domain.upper()}'
            RETURN u
            """
            
            result = self.execute_query(cypher_query)
            highvalue_users = []
            
            # execute_query returns a list of node properties
            if result and isinstance(result, list):
                for node_properties in result:
                    samaccountname = node_properties.get('samaccountname') or node_properties.get('name', '')
                    if samaccountname:
                        # Extract just the username part (before @) if it's in UPN format
                        if "@" in samaccountname:
                            samaccountname = samaccountname.split("@")[0]
                        highvalue_users.append(samaccountname)
            
            return highvalue_users

        except Exception:
            return []
    
    def get_password_not_required_users(self, domain: str) -> List[str]:
        """Get enabled users with password not required using CySQL query"""
        try:
            # Use CySQL query to get enabled users with passwordnotreqd = true in specific domain
            cypher_query = f"""
            MATCH (u:User) 
            WHERE u.passwordnotreqd = true AND u.enabled = true AND toUpper(u.domain) = '{domain.upper()}'
            RETURN u
            """
            
            result = self.execute_query(cypher_query)
            users = []
            
            # execute_query returns a list of node properties
            if result and isinstance(result, list):
                for node_properties in result:
                    samaccountname = node_properties.get('samaccountname') or node_properties.get('name', '')
                    if samaccountname:
                        # Extract just the username part (before @) if it's in UPN format
                        if "@" in samaccountname:
                            samaccountname = samaccountname.split("@")[0]
                        users.append(samaccountname)
            
            return users

        except Exception:
            return []
    
    def get_password_never_expires_users(self, domain: str) -> List[str]:
        """Get enabled users with password never expires using CySQL query"""
        try:
            # Use CySQL query to get enabled users with pwdneverexpires = true in specific domain
            cypher_query = f"""
            MATCH (u:User) 
            WHERE u.pwdneverexpires = true AND u.enabled = true AND toUpper(u.domain) = '{domain.upper()}'
            RETURN u
            """
            
            result = self.execute_query(cypher_query)
            users = []
            
            # execute_query returns a list of node properties
            if result and isinstance(result, list):
                for node_properties in result:
                    samaccountname = node_properties.get('samaccountname') or node_properties.get('name', '')
                    if samaccountname:
                        # Extract just the username part (before @) if it's in UPN format
                        if "@" in samaccountname:
                            samaccountname = samaccountname.split("@")[0]
                        users.append(samaccountname)
            
            return users

        except Exception:
            return []
    
    def get_sessions(self, domain: str, da: bool = False) -> List[Dict]:
        """Get user sessions using CySQL query"""
        try:
            if da:
                # Get sessions from computer perspective
                cypher_query = f"""
                MATCH (c:Computer)-[r:HasSession]->(u:User)
                WHERE toUpper(c.domain) = '{domain.upper()}' AND u.enabled = true
                RETURN c, u
                """
            else:
                # Get sessions from user perspective
                cypher_query = f"""
                MATCH (u:User)-[r:HasSession]->(c:Computer)
                WHERE toUpper(u.domain) = '{domain.upper()}' AND u.enabled = true
                RETURN u, c
                """
            
            result = self.execute_query(cypher_query)
            sessions = []
            
            if result and isinstance(result, list):
                for node_properties in result:
                    if da:
                        # Computer -> User session
                        computer_name = node_properties.get('name', '')
                        user_name = node_properties.get('samaccountname', '')
                        if computer_name and user_name:
                            # Extract just the computer name part (before @) if it's in UPN format
                            if "@" in computer_name:
                                computer_name = computer_name.split("@")[0]
                            # Extract just the username part (before @) if it's in UPN format
                            if "@" in user_name:
                                user_name = user_name.split("@")[0]
                            sessions.append({"computer": computer_name.lower(), "user": user_name})
                    else:
                        # User -> Computer session
                        user_name = node_properties.get('samaccountname', '')
                        computer_name = node_properties.get('name', '')
                        if user_name and computer_name:
                            # Extract just the username part (before @) if it's in UPN format
                            if "@" in user_name:
                                user_name = user_name.split("@")[0]
                            # Extract just the computer name part (before @) if it's in UPN format
                            if "@" in computer_name:
                                computer_name = computer_name.split("@")[0]
                            sessions.append({"user": user_name, "computer": computer_name.lower()})
            
            return sessions

        except Exception:
            return []
    
    def get_password_last_change(self, domain: str, user: Optional[str] = None) -> List[Dict]:
        """Get password last change information using CySQL query"""
        try:
            if user:
                cypher_query = f"""
                MATCH (u:User)
                WHERE u.enabled = true AND toUpper(u.domain) = '{domain.upper()}'
                  AND u.samaccountname = '{user}'
                RETURN u
                """
            else:
                cypher_query = f"""
                MATCH (u:User)
                WHERE u.enabled = true AND toUpper(u.domain) = '{domain.upper()}'
                RETURN u
                """
            
            result = self.execute_query(cypher_query)
            password_info = []
            
            if result and isinstance(result, list):
                for node_properties in result:
                    samaccountname = node_properties.get('samaccountname', '')
                    pwdlastset = node_properties.get('pwdlastset', 0)
                    whencreated = node_properties.get('whencreated', 0)
                    
                    if samaccountname:
                        # Extract just the username part (before @) if it's in UPN format
                        if "@" in samaccountname:
                            samaccountname = samaccountname.split("@")[0]
                        
                        password_info.append({
                            "samaccountname": samaccountname,
                            "pwdlastset": pwdlastset,
                            "whencreated": whencreated
                        })
            
            return password_info

        except Exception:
            return []
    
    def get_critical_aces(self, source_domain: str, high_value: bool = False, 
                         username: str = "all", target_domain: str = "all", 
                         relation: str = "all") -> List[Dict]:
        """Get critical ACEs using simplified Cypher query compatible with BloodHound CE"""
        try:
            # BloodHound CE doesn't support CASE or UNION, so we need simpler queries
            # We'll run two separate queries and combine results
            
            aces = []
            
            # Build filters
            username_filter = ""
            if username.lower() != "all":
                username_filter = f" AND toLower(n.samaccountname) = toLower('{username}')"
            
            target_domain_filter = ""
            if target_domain.lower() != "all" and target_domain.lower() != "high-value":
                target_domain_filter = f" AND toLower(m.domain) = toLower('{target_domain}')"
            
            high_value_filter = ""
            if high_value:
                # In BloodHound CE, tier 0 (high value) is identified by system_tags = "admin_tier_0"
                high_value_filter = ' AND NOT m.system_tags = "admin_tier_0"'
            
            relation_filter = ""
            if relation.lower() != "all":
                relation_filter = f":{relation}"
            
            # Single query using *0.. to include both direct ACEs and through group membership
            cypher_query = f"""
            MATCH (n)-[:MemberOf*0..]->(g)-[r{relation_filter}]->(m)
            WHERE r.isacl = true
              AND toLower(n.domain) = toLower('{source_domain}')
              {username_filter}
              {target_domain_filter}
              {high_value_filter}
            RETURN n, m, r
            LIMIT 1000
            """
            
            result = self.execute_query_with_relationships(cypher_query)
            if result:
                aces.extend(self._process_ace_results_from_graph(result))
            
            # Remove duplicates based on source, target, and relation
            unique_aces = []
            seen = set()
            for ace in aces:
                key = (ace['source'], ace['target'], ace['relation'])
                if key not in seen:
                    seen.add(key)
                    unique_aces.append(ace)
            
            return unique_aces

        except Exception as e:
            if self.debug:
                print(f"Debug: Exception in get_critical_aces: {e}")
                import traceback
                traceback.print_exc()
            return []
    
    def _process_ace_results_from_graph(self, graph_data: Dict) -> List[Dict]:
        """Process ACE query results from BloodHound CE graph format"""
        aces = []
        
        nodes = graph_data.get('nodes', {})
        edges = graph_data.get('edges', [])  # edges is a list, not dict
        
        if self.debug:
            print(f"Debug: Processing {len(nodes)} nodes and {len(edges)} edges")
        
        # Process each edge (relationship) - edges is a list
        for edge_data in edges:
            source_id = str(edge_data.get('source'))  # Convert to string for dict lookup
            target_id = str(edge_data.get('target'))  # Convert to string for dict lookup
            edge_props = edge_data.get('properties', {})
            edge_label = edge_data.get('label', 'Unknown')
            
            # Get source and target node data
            source_node = nodes.get(source_id, {})
            target_node = nodes.get(target_id, {})
            
            source_props = source_node.get('properties', {})
            target_props = target_node.get('properties', {})
            
            # Extract source info
            source_name = source_props.get('samaccountname') or source_props.get('name', '')
            source_domain = source_props.get('domain', 'N/A')
            source_kind = source_node.get('kind', 'Unknown')
            
            # Extract target info  
            target_name = target_props.get('samaccountname') or target_props.get('name', '')
            target_domain = target_props.get('domain', 'N/A')
            target_enabled = target_props.get('enabled', True)
            target_kind = target_node.get('kind', 'Unknown')
            
            if source_name and target_name:
                # Extract just the name part (before @) if it's in UPN format
                if "@" in source_name:
                    source_name = source_name.split("@")[0]
                if "@" in target_name:
                    target_name = target_name.split("@")[0]
                
                aces.append({
                    "source": source_name,
                    "sourceType": source_kind,
                    "target": target_name,
                    "targetType": target_kind,
                    "relation": edge_label,
                    "sourceDomain": source_domain.lower() if source_domain != 'N/A' else 'N/A',
                    "targetDomain": target_domain.lower() if target_domain != 'N/A' else 'N/A',
                    "targetEnabled": target_enabled
                })
        
        return aces
    
    def get_access_paths(self, source: str, connection: str, target: str, domain: str) -> List[Dict]:
        """Get access paths using CySQL query - adapted from old_main.py"""
        try:
            # Determine relationship conditions
            if connection.lower() == "all":
                rel_condition = "AND type(r) IN ['AdminTo','CanRDP','CanPSRemote']"
                rel_pattern = "[r]->"
            else:
                rel_condition = ""
                rel_pattern = f"[r:{connection}]->"
            
            # Case 1: source != "all" and target == "all" - find what source can access
            if source.lower() != "all" and target.lower() == "all":
                cypher_query = f"""
                MATCH p = (n)-{rel_pattern}(m)
                WHERE toLower(n.samaccountname) = toLower('{source}')
                AND toLower(n.domain) = toLower('{domain}')
                AND m.enabled = true
                {rel_condition}
                RETURN n.samaccountname AS source, m.samaccountname AS target, type(r) AS relation
                """
            
            # Case 2: source == "all" and target == "all" - find all access paths in domain
            elif source.lower() == "all" and target.lower() == "all":
                cypher_query = f"""
                MATCH p = (n)-{rel_pattern}(m)
                WHERE toLower(n.domain) = toLower('{domain}')
                AND n.enabled = true
                AND m.enabled = true
                {rel_condition}
                RETURN n.samaccountname AS source, m.samaccountname AS target, type(r) AS relation
                """
            
            # Case 3: source != "all" and target == "dcs" - find users with DC access
            elif source.lower() != "all" and target.lower() == "dcs":
                cypher_query = f"""
                MATCH p = (n)-{rel_pattern}(m)
                WHERE toLower(n.samaccountname) = toLower('{source}')
                AND toLower(n.domain) = toLower('{domain}')
                AND m.enabled = true
                AND (m.operatingsystem CONTAINS 'Windows Server' OR m.operatingsystem CONTAINS 'Domain Controller')
                {rel_condition}
                RETURN n.samaccountname AS source, m.samaccountname AS target, type(r) AS relation
                """
            
            # Case 4: source == "all" and target == "dcs" - find all users with DC access
            elif source.lower() == "all" and target.lower() == "dcs":
                cypher_query = f"""
                MATCH p = (n)-{rel_pattern}(m)
                WHERE toLower(n.domain) = toLower('{domain}')
                AND n.enabled = true
                AND m.enabled = true
                AND (m.operatingsystem CONTAINS 'Windows Server' OR m.operatingsystem CONTAINS 'Domain Controller')
                {rel_condition}
                RETURN n.samaccountname AS source, m.samaccountname AS target, type(r) AS relation
                """
            
            # Case 5: specific source to specific target
            else:
                cypher_query = f"""
                MATCH p = (n)-{rel_pattern}(m)
                WHERE toLower(n.samaccountname) = toLower('{source}')
                AND toLower(n.domain) = toLower('{domain}')
                AND toLower(m.samaccountname) = toLower('{target}')
                AND m.enabled = true
                {rel_condition}
                RETURN n.samaccountname AS source, m.samaccountname AS target, type(r) AS relation
                """
            
            result = self.execute_query(cypher_query)
            paths = []
            
            if result and isinstance(result, list):
                for record in result:
                    source_name = record.get('source', '')
                    target_name = record.get('target', '')
                    relation = record.get('relation', '')
                    
                    if source_name and target_name:
                        # Extract just the username part (before @) if it's in UPN format
                        if "@" in source_name:
                            source_name = source_name.split("@")[0]
                        if "@" in target_name:
                            target_name = target_name.split("@")[0]
                        
                        paths.append({
                            "source": source_name,
                            "target": target_name,
                            "relation": relation,
                            "path": f"{source_name} -> {target_name} ({relation})"
                        })
            
            return paths

        except Exception:
            return []
    
    def get_users_with_dc_access(self, domain: str) -> List[Dict]:
        """Get users who have access to Domain Controllers"""
        try:
            # First try to find actual DCs
            cypher_query = f"""
            MATCH (u:User)-[r]->(dc:Computer)
            WHERE u.enabled = true AND toUpper(u.domain) = '{domain.upper()}'
              AND dc.enabled = true AND toUpper(dc.domain) = '{domain.upper()}'
              AND (dc.operatingsystem CONTAINS 'Windows Server' OR dc.operatingsystem CONTAINS 'Domain Controller')
            RETURN u.samaccountname AS user, dc.name AS dc, type(r) AS relation
            """
            
            result = self.execute_query(cypher_query)
            users_with_access = []
            
            if result and isinstance(result, list):
                for record in result:
                    user = record.get('user', '')
                    dc = record.get('dc', '')
                    relation = record.get('relation', '')
                    
                    if user and dc:
                        # Extract just the username part (before @) if it's in UPN format
                        if "@" in user:
                            user = user.split("@")[0]
                        if "@" in dc:
                            dc = dc.split("@")[0]
                        
                        users_with_access.append({
                            "source": user,
                            "target": dc,
                            "path": f"{user} -> {dc} ({relation})"
                        })
            
            # If no DCs found, try to find any user-computer relationships
            if not users_with_access:
                fallback_query = f"""
                MATCH (u:User)-[r]->(c:Computer)
                WHERE u.enabled = true AND toUpper(u.domain) = '{domain.upper()}'
                  AND c.enabled = true AND toUpper(c.domain) = '{domain.upper()}'
                RETURN u.samaccountname AS user, c.name AS computer, type(r) AS relation
                """
                
                result = self.execute_query(fallback_query)
                
                if result and isinstance(result, list):
                    for record in result:
                        user = record.get('user', '')
                        computer = record.get('computer', '')
                        relation = record.get('relation', '')
                        
                        if user and computer:
                            # Extract just the username part (before @) if it's in UPN format
                            if "@" in user:
                                user = user.split("@")[0]
                            if "@" in computer:
                                computer = computer.split("@")[0]
                            
                            users_with_access.append({
                                "source": user,
                                "target": computer,
                                "path": f"{user} -> {computer} ({relation})"
                            })
            
            return users_with_access

        except Exception:
            return []
    
    def get_critical_aces_by_domain(self, domain: str, blacklist: List[str], 
                                   high_value: bool = False) -> List[Dict]:
        """Get critical ACEs by domain using CySQL query"""
        try:
            cypher_query = f"""
            MATCH (s)-[r]->(t)
            WHERE toUpper(s.domain) = '{domain.upper()}'
            RETURN s, r, t
            """
            
            result = self.execute_query(cypher_query)
            aces = []
            
            if result and isinstance(result, list):
                for node_properties in result:
                    source_name = node_properties.get('name', '')
                    target_name = node_properties.get('name', '')
                    relation_type = node_properties.get('relation', '')
                    
                    if source_name and target_name:
                        # Extract just the name part (before @) if it's in UPN format
                        if "@" in source_name:
                            source_name = source_name.split("@")[0]
                        if "@" in target_name:
                            target_name = target_name.split("@")[0]
                        
                        aces.append({
                            "source": source_name,
                            "relation": relation_type,
                            "target": target_name
                        })
            
            return aces

        except Exception:
            return []
    
    def _get_headers(self):
        """Get headers for API requests"""
        headers = {
            'User-Agent': 'BloodHound-CLI/1.0'
        }
        
        if self.api_token:
            headers['Authorization'] = f'Bearer {self.api_token}'
        
        return headers
    
    def upload_data(self, file_path: str) -> bool:
        """Upload BloodHound data using the file upload API"""
        try:
            # Step 1: Create file upload job
            create_response = self.session.post(
                f"{self.base_url}/api/v2/file-upload/start",
                headers=self._get_headers(),
                json={"collection_method": "manual"}
            )
            
            if create_response.status_code not in [200, 201]:
                print(f"Error creating upload job: {create_response.status_code} - {create_response.text}")
                return False
                
            job_data = create_response.json()
            # The response structure is {"data": {"id": "..."}}
            job_id = job_data.get("data", {}).get("id")
            
            if not job_id:
                print(f"Error: Failed to create upload job. Response: {job_data}")
                return False
            
            # Step 2: Upload file to job
            fpath = Path(file_path)
            if not fpath.exists() or not fpath.is_file():
                print(f"Error: File {file_path} not found")
                return False
            
            # Determine content type
            suffix = fpath.suffix.lower()
            if suffix == ".zip":
                content_type = "application/zip"
            elif suffix == ".json":
                content_type = "application/json"
            else:
                content_type = "application/octet-stream"
            
            headers = self._get_headers()
            headers["Content-Type"] = content_type
            
            with open(file_path, 'rb') as f:
                body = f.read()
                upload_response = self.session.post(
                    f"{self.base_url}/api/v2/file-upload/{job_id}",
                    data=body,
                    headers=headers
                )
                
                if upload_response.status_code >= 400:
                    print(f"Error uploading file: HTTP {upload_response.status_code} - {upload_response.text}")
                    return False
            
            # Step 3: End upload job
            end_response = self.session.post(
                f"{self.base_url}/api/v2/file-upload/{job_id}/end",
                headers=self._get_headers()
            )
            
            if end_response.status_code >= 400:
                print(f"Error ending upload job: HTTP {end_response.status_code} - {end_response.text}")
                return False
            
            return True
            
        except Exception as e:
            print(f"Error uploading data: {e}")
            return False
    
    def list_upload_jobs(self) -> List[Dict]:
        """List file upload jobs"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v2/file-upload",
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()
            # The response structure might be {"data": [...]} or just [...]
            if isinstance(data, dict) and "data" in data:
                return data["data"]
            elif isinstance(data, list):
                return data
            else:
                return []
        except Exception as e:
            print(f"Error listing upload jobs: {e}")
            return []
    
    def get_accepted_upload_types(self) -> List[str]:
        """Get accepted file upload types"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v2/file-upload/accepted-types",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting accepted types: {e}")
            return []
    
    def get_file_upload_job(self, job_id: int) -> Optional[Dict]:
        """Get specific file upload job details"""
        try:
            # Use the list endpoint and filter by job_id
            response = self.session.get(
                f"{self.base_url}/api/v2/file-upload",
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()
            
            # The response structure might be {"data": [...]} or just [...]
            jobs = []
            if isinstance(data, dict) and "data" in data:
                jobs = data["data"]
            elif isinstance(data, list):
                jobs = data
            
            # Find the job with the matching ID
            for job in jobs:
                if job.get("id") == job_id:
                    return job
            
            return None
        except Exception as e:
            print(f"Error getting upload job {job_id}: {e}")
            return None
    
    def infer_latest_file_upload_job_id(self) -> Optional[int]:
        """Infer the latest file upload job ID from the list"""
        try:
            jobs = self.list_upload_jobs()
            if not jobs:
                return None
            
            # Find the most recent job (highest ID or most recent timestamp)
            latest_job = max(jobs, key=lambda x: x.get('id', 0))
            return latest_job.get('id')
        except Exception as e:
            print(f"Error inferring latest job ID: {e}")
            return None
    
    def upload_data_and_wait(self, file_path: str, poll_interval: int = 5, timeout_seconds: int = 1800) -> bool:
        """Upload BloodHound data and wait for processing to complete"""
        import time
        
        try:
            # Step 1: Upload the file
            success = self.upload_data(file_path)
            if not success:
                return False
            
            # Step 2: Wait for processing to complete
            start_time = time.time()
            last_status = None
            job = None
            
            print("Waiting for ingestion to complete...")
            
            while True:
                # Get the latest job ID
                job_id = self.infer_latest_file_upload_job_id()
                if job_id is None:
                    # Brief grace period immediately after upload
                    if time.time() - start_time > 15:
                        print("Timeout: Could not find upload job")
                        return False
                else:
                    # Get job details
                    job = self.get_file_upload_job(job_id)
                    if job is None:
                        if time.time() - start_time > 15:
                            print("Timeout: Could not get job details")
                            return False
                    else:
                        status = job.get("status")
                        status_message = job.get("status_message", "")
                        
                        # Show status if it changed
                        if status != last_status:
                            print(f"Job status: {status} - {status_message}")
                            last_status = status
                        
                        # Terminal statuses: -1 invalid, 2 complete, 3 canceled, 4 timed out, 5 failed, 8 partially complete
                        if status in [-1, 2, 3, 4, 5, 8]:
                            if status == 2:
                                print("✅ Upload and processing completed successfully")
                                return True
                            elif status in [3, 4, 5]:
                                print(f"❌ Upload failed with status {status}: {status_message}")
                                return False
                            elif status == 8:
                                print("⚠️ Upload completed with warnings (partially complete)")
                                return True
                            else:
                                print(f"❌ Upload failed with status {status}: {status_message}")
                                return False
                
                # Check timeout
                if time.time() - start_time > timeout_seconds:
                    print(f"❌ Timeout after {timeout_seconds} seconds")
                    return False
                
                time.sleep(max(1, poll_interval))
            
        except Exception as e:
            print(f"Error in upload and wait: {e}")
            return False
    
    def verify_token(self) -> bool:
        """Verify if the current token is valid by making a test request"""
        try:
            # Try to make a simple API call to verify the token
            response = self.session.get(
                f"{self.base_url}/api/v2/file-upload",
                headers=self._get_headers()
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def auto_renew_token(self) -> bool:
        """Automatically renew the token using stored credentials"""
        try:
            # Load config to get stored credentials
            config = configparser.ConfigParser()
            config.read(os.path.expanduser("~/.bloodhound_config"))
            
            if 'CE' not in config:
                return False
            
            username = config['CE'].get('username', 'admin')
            password = config['CE'].get('password')
            base_url = config['CE'].get('base_url', 'http://localhost:8080')
            
            if not password:
                return False
            
            # Create a new session for authentication (without the expired token)
            import requests
            temp_session = requests.Session()
            temp_session.verify = self.session.verify
            
            # Authenticate with stored credentials using the temp session
            login_url = f"{base_url}/api/v2/login"
            payload = {"login_method": "secret", "username": username, "secret": password}
            
            response = temp_session.post(login_url, json=payload, timeout=60)
            if response.status_code >= 400:
                return False
                
            data = response.json()
            token = None
            if isinstance(data, dict):
                data_field = data.get("data")
                if isinstance(data_field, dict):
                    token = data_field.get("session_token")
            if not token:
                token = data.get("token") or data.get("access_token") or data.get("jwt")
            
            if not token:
                return False
            
            # Update the stored token and our session
            config['CE']['api_token'] = token
            with open(os.path.expanduser("~/.bloodhound_config"), 'w') as f:
                config.write(f)
            
            # Update our session with the new token
            self.api_token = token
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            
            return True
            
        except Exception as e:
            print(f"Error auto-renewing token: {e}")
            return False
    
    def ensure_valid_token(self) -> bool:
        """Ensure we have a valid token, auto-renew if necessary"""
        if not self.api_token:
            return self.auto_renew_token()
        
        # Check if current token is valid
        if self.verify_token():
            return True
        
        # Token is invalid, try to renew
        print("Token expired, attempting to renew...")
        return self.auto_renew_token()
    
    def close(self):
        """Close the HTTP session"""
        try:
            self.session.close()
        except Exception:
            pass

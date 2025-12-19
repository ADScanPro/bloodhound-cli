"""
BloodHound CE implementation using HTTP API
"""
# pylint: skip-file
import configparser
import os
from json import JSONDecodeError
from typing import List, Dict, Optional
from pathlib import Path
import requests
from .base import BloodHoundClient
from .logging_utils import get_logger
from .settings import CONFIG_FILE


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
        self.logger = get_logger("BloodHoundCE", base_url=self.base_url)
        # Store credentials for token renewal
        self._stored_username = None
        self._stored_password = None
    
    def _debug(self, message: str, **context) -> None:
        if self.debug:
            self.logger.debug(message, **context)
    
    def _load_config(self) -> Optional[Dict[str, str]]:
        """Load configuration from the resolved config path."""
        config_path = str(CONFIG_FILE)
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
            # Remove stale token headers before logging in
            self.session.headers.pop("Authorization", None)
            response = self.session.post(url, json=payload, verify=self.verify, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("data", {}).get("session_token")
                if token:
                    self.api_token = token
                    self.session.headers.update({"Authorization": f"Bearer {token}"})
                    # Store credentials for token renewal
                    self._stored_username = username
                    self._stored_password = password
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
            
            self._debug(
                "executing cypher query",
                raw_query=query,
                cleaned_query=cleaned_query,
                url=url,
                params=params,
            )
            
            response = self.session.post(url, json=payload, verify=self.verify, timeout=60)
            
            # Handle authentication errors by attempting token renewal
            if response.status_code == 401:
                self._debug("authentication failed, attempting token renewal")
                if self.ensure_valid_token():
                    # Retry the request with renewed token
                    response = self.session.post(url, json=payload, verify=self.verify, timeout=60)
                    self._debug(
                        "cypher query retry response",
                        status=response.status_code,
                    )
                else:
                    self._debug(
                        "token renewal failed",
                        status=response.status_code,
                        response_text=response.text,
                    )
                    return []
            
            if response.status_code == 200:
                data = response.json()
                self._debug(
                    "cypher response",
                    keys=list(data.keys()) if isinstance(data, dict) else "non-dict",
                )
                
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
                self._debug(
                    "cypher query failed",
                    status=response.status_code,
                    response_text=response.text,
                )
                return []
                
        except JSONDecodeError as json_error:
            self._debug("failed to parse CE response", error=str(json_error))
            return []
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self._debug("cypher query error", error=str(exc))
            return []
    
    def execute_query_with_relationships(self, query: str) -> Dict:
        """Execute a Cypher query and include relationships in the response"""
        try:
            url = f"{self.base_url}/api/v2/graphs/cypher"
            
            cleaned_query = ' '.join(query.split())
            payload = {
                "query": cleaned_query,
                "include_properties": True,
                "include_relationships": True
            }
            
            self._debug("executing relationship query", raw_query=query, cleaned_query=cleaned_query)
            
            response = self.session.post(url, json=payload, verify=self.verify, timeout=60)
            
            self._debug(
                "relationship query response",
                status=response.status_code,
                headers=dict(response.headers),
            )
            
            # Handle authentication errors by attempting token renewal
            if response.status_code == 401:
                self._debug("authentication failed, attempting token renewal")
                if self.ensure_valid_token():
                    # Retry the request with renewed token
                    response = self.session.post(url, json=payload, verify=self.verify, timeout=60)
                    self._debug(
                        "relationship query retry response",
                        status=response.status_code,
                    )
                else:
                    self._debug("token renewal failed", status=response.status_code, response=response.text)
                    return {}
            
            if response.status_code == 200:
                data = response.json()
                self._debug(
                    "relationship query data",
                    has_data=isinstance(data, dict),
                    keys=list(data.keys()) if isinstance(data, dict) else None,
                )
                return data.get("data", {})
            
            self._debug("relationship query failed", status=response.status_code, response=response.text)
            return {}
                
        except JSONDecodeError as json_error:
            self._debug("failed to parse relationship response", error=str(json_error))
            return {}
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self._debug("relationship query error", error=str(exc))
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

    def get_users_in_ou(self, domain: str, ou_distinguished_name: str) -> List[str]:
        """Get enabled users that belong to a specific OU using its distinguished name.

        Args:
            domain: AD domain name to filter users by (e.g. "north.sevenkingdoms.local").
            ou_distinguished_name: Distinguished Name (DN) of the OU to search under.

        Returns:
            List of `samaccountname` values for users that belong to the OU.
        """
        try:
            # Escape single quotes to avoid breaking the Cypher string
            sanitized_ou_dn = ou_distinguished_name.replace("'", "\\'")

            cypher_query = f"""
            MATCH (ou:OU)
            WHERE toLower(ou.distinguishedname) = toLower('{sanitized_ou_dn}')
            MATCH (u:User)
            WHERE u.enabled = true
              AND toUpper(u.domain) = '{domain.upper()}'
              AND toLower(u.distinguishedname) CONTAINS toLower(ou.distinguishedname)
            RETURN u
            """

            result = self.execute_query(cypher_query)
            users: List[str] = []

            if result and isinstance(result, list):
                for node_properties in result:
                    samaccountname = node_properties.get("samaccountname") or node_properties.get("name", "")
                    if samaccountname:
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

    def get_user_groups(
        self, domain: str, username: str, recursive: bool = True
    ) -> List[str]:
        """Get group memberships for a user (optionally recursive)"""
        try:
            membership_pattern = "-[:MemberOf*1..]->" if recursive else "-[:MemberOf]->"
            sanitized_user = username.replace("'", "\\'")

            cypher_query = f"""
            MATCH (u:User)
            WHERE u.enabled = true
              AND toLower(u.domain) = toLower('{domain}')
              AND (
                toLower(u.samaccountname) = toLower('{sanitized_user}')
                OR toLower(u.name) = toLower('{sanitized_user}')
              )
            MATCH (u){membership_pattern}(g:Group)
            RETURN DISTINCT g
            ORDER BY toLower(g.name)
            """
            
            result = self.execute_query(cypher_query)
            groups: List[str] = []
            
            if result and isinstance(result, list):
                for node_properties in result:
                    display_name = node_properties.get("name")
                    if not display_name:
                        group_domain = node_properties.get("domain")
                        samaccountname = node_properties.get("samaccountname")
                        if group_domain and samaccountname:
                            display_name = f"{group_domain}\\{samaccountname}"
                        else:
                            display_name = samaccountname or group_domain
                    
                    if display_name:
                        groups.append(display_name)
            
            return groups

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
                lowered = username.replace("'", "\\'")
                username_filter = (
                    " AND (toLower(n.samaccountname) = toLower('{value}') "
                    "OR toLower(n.name) = toLower('{value}'))"
                ).format(value=lowered)
            
            target_domain_filter = ""
            if target_domain.lower() != "all" and target_domain.lower() != "high-value":
                target_domain_filter = f" AND toLower(m.domain) = toLower('{target_domain}')"
            
            high_value_filter = ""
            if high_value:
                # In BloodHound CE, tier 0 (high value) is identified by system_tags = "admin_tier_0"
                high_value_filter = ' AND m.system_tags = "admin_tier_0"'
            
            relation_filter = ""
            if relation.lower() != "all":
                relation_filter = f":{relation}"
            
            # Single query using *0.. to include both direct ACEs and through group membership
            # We return n, g, m, r so we can track the original source node (n) even when ACLs are through groups (g)
            cypher_query = f"""
            MATCH (n)-[:MemberOf*0..]->(g)-[r{relation_filter}]->(m)
            WHERE r.isacl = true
              AND toLower(n.domain) = toLower('{source_domain}')
              {username_filter}
              {target_domain_filter}
              {high_value_filter}
            RETURN n, g, m, r
            LIMIT 1000
            """
            
            result = self.execute_query_with_relationships(cypher_query)
            if result:
                aces.extend(self._process_ace_results_from_graph(result, source_domain, username))
            
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
                self._debug("exception processing critical aces", error=str(e))
            return []
    
    def _process_ace_results_from_graph(self, graph_data: Dict, source_domain: str = None, username: str = None) -> List[Dict]:
        """Process ACE query results from BloodHound CE graph format"""
        aces = []
        
        nodes = graph_data.get('nodes', {})
        edges = graph_data.get('edges', [])  # edges is a list, not dict
        
        self._debug("processing graph results", node_count=len(nodes), edge_count=len(edges))
        
        # Find the original source node(s) (n) that match our search criteria
        # This is needed when ACLs are through groups (even nested groups) and the edge source is the group, not the original node
        # The query uses [:MemberOf*0..] which is recursive, so it handles nested groups automatically
        original_source_nodes = []
        if source_domain:
            for node_id, node_data in nodes.items():
                node_props = node_data.get('properties', {})
                node_kind = node_data.get('kind', '')
                node_domain = node_props.get('domain', '')
                
                # Look for User or Computer (not Group) with matching domain
                if node_kind in ['User', 'Computer']:
                    if node_domain and node_domain.upper() == source_domain.upper():
                        # If username is specified, check if it matches
                        if username and username.lower() != "all":
                            node_sam = node_props.get('samaccountname', '')
                            if node_sam and node_sam.lower() == username.lower():
                                original_source_nodes.append((node_id, node_data))
                                self._debug(
                                    "found source node",
                                    node=node_sam,
                                    node_id=node_id,
                                    kind=node_kind,
                                )
                        else:
                            # If no specific username, collect all matching User/Computer nodes
                            node_sam = node_props.get('samaccountname', '') or node_props.get('name', '')
                            original_source_nodes.append((node_id, node_data))
                            self._debug(
                                "found source node",
                                node=node_sam,
                                node_id=node_id,
                                kind=node_kind,
                            )
        
        self._debug("identified original sources", count=len(original_source_nodes))
        
        # Process each edge (relationship) - edges is a list
        for edge_data in edges:
            source_id = str(edge_data.get('source'))  # Convert to string for dict lookup
            target_id = str(edge_data.get('target'))  # Convert to string for dict lookup
            edge_label = edge_data.get('label', 'Unknown')
            
            # Get source and target node data
            source_node = nodes.get(source_id, {})
            target_node = nodes.get(target_id, {})
            
            source_kind = source_node.get('kind', '') if source_node else ''
            use_fallback = (
                not source_node
                or source_id not in nodes
                or (
                    original_source_nodes
                    and username
                    and username.lower() != "all"
                    and source_kind == 'Group'
                )
            )
            if use_fallback:
                # Use the first matching original source node
                # If username was specified, there should be only one
                # If username was "all", all edges apply to all matching users
                if original_source_nodes:
                    _, original_node = original_source_nodes[0]
                    source_node = original_node
                    source_props = original_node.get('properties', {})
                    source_domain_value = source_props.get('domain', 'N/A')
                    source_kind = original_node.get('kind', 'Unknown')
                    self._debug(
                        "using fallback source node",
                        edge_source_id=source_id,
                        fallback_kind=source_kind,
                    )
                else:
                    source_props = {}
                    source_domain_value = 'N/A'
            else:
                source_props = source_node.get('properties', {})
                source_domain_value = source_props.get('domain', 'N/A')
            
            target_props = target_node.get('properties', {})
            
            # Extract source info
            source_name = source_props.get('samaccountname') or source_props.get('name', '')
            
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
                    "sourceDomain": source_domain_value.lower() if source_domain_value != 'N/A' else 'N/A',
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
            self.logger.error("upload error", error=str(e))
            print(f"Error uploading file: {e}")
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
            self.logger.error("list upload jobs failed", error=str(e))
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
            self.logger.error("accepted types request failed", error=str(e))
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
            self.logger.error("get upload job failed", job_id=job_id, error=str(e))
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
            self.logger.error("infer latest upload job failed", error=str(e))
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
            self.logger.info("waiting for ingestion", file=file_path)
            
            while True:
                # Get the latest job ID
                job_id = self.infer_latest_file_upload_job_id()
                if job_id is None:
                    # Brief grace period immediately after upload
                    if time.time() - start_time > 15:
                        self.logger.warning("could not locate upload job")
                        print("Timeout: Could not find upload job")
                        return False
                else:
                    # Get job details
                    job = self.get_file_upload_job(job_id)
                    if job is None:
                        if time.time() - start_time > 15:
                            self.logger.warning("could not fetch job details")
                            print("Timeout: Could not get job details")
                            return False
                    else:
                        status = job.get("status")
                        status_message = job.get("status_message", "")
                        
                        # Show status if it changed
                        if status != last_status:
                            self.logger.info("upload status", status=status, message=status_message)
                            print(f"Job status: {status} - {status_message}")
                            last_status = status
                        
                        # Terminal statuses: -1 invalid, 2 complete, 3 canceled, 4 timed out, 5 failed, 8 partially complete
                        if status in [-1, 2, 3, 4, 5, 8]:
                            if status == 2:
                                print("✅ Upload and processing completed successfully")
                                self.logger.info("upload complete", status=status)
                                return True
                            elif status in [3, 4, 5]:
                                self.logger.error("upload failed", status=status, message=status_message)
                                print(f"❌ Upload failed with status {status}: {status_message}")
                                return False
                            elif status == 8:
                                self.logger.warning("upload partial", status=status, message=status_message)
                                print("⚠️ Upload completed with warnings (partially complete)")
                                return True
                            else:
                                self.logger.error("upload failed", status=status, message=status_message)
                                print(f"❌ Upload failed with status {status}: {status_message}")
                                return False
                
                # Check timeout
                if time.time() - start_time > timeout_seconds:
                    self.logger.error("upload timeout", timeout_seconds=timeout_seconds)
                    print(f"❌ Timeout after {timeout_seconds} seconds")
                    return False
                
                time.sleep(max(1, poll_interval))
            
        except Exception as e:
            self.logger.exception("upload wait error", error=str(e))
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
            self.logger.exception("token verification error")
            return False
    
    def auto_renew_token(self) -> bool:
        """Automatically renew the token using stored credentials"""
        try:
            # First try to use credentials stored in memory (from authenticate())
            if self._stored_username and self._stored_password:
                login_url = f"{self.base_url}/api/v2/login"
                payload = {"login_method": "secret", "username": self._stored_username, "secret": self._stored_password}
                
                # Remove stale token headers before logging in
                self.session.headers.pop("Authorization", None)
                response = self.session.post(login_url, json=payload, verify=self.verify, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    token = data.get("data", {}).get("session_token")
                    if token:
                        self.api_token = token
                        self.session.headers.update({"Authorization": f"Bearer {token}"})
                        return True
                return False
            
            # Fallback: Load config to get stored credentials
            config = configparser.ConfigParser()
            config.read(str(CONFIG_FILE))
            
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
            with open(str(CONFIG_FILE), 'w', encoding="utf-8") as f:
                config.write(f)
            
            # Update our session with the new token
            self.api_token = token
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            
            return True
            
        except Exception as e:
            self.logger.exception("token auto-renew error", error=str(e))
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
        self.logger.info("token expired, attempting renewal")
        print("Token expired, attempting to renew...")
        return self.auto_renew_token()
    
    def close(self):
        """Close the HTTP session"""
        try:
            self.session.close()
        except Exception:
            pass

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
            payload = {
                "query": query,
                "include_properties": True
            }
            
            response = self.session.post(url, json=payload, verify=self.verify, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
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
                return []
                
        except Exception:
            return []
    
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
            # In BloodHound CE, high value users are identified by system_tags = "admin_tier_0"
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
        """Get critical ACEs using CySQL query"""
        try:
            cypher_query = f"""
            MATCH (s)-[r]->(t)
            WHERE toUpper(s.domain) = '{source_domain.upper()}'
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
    
    def get_access_paths(self, source: str, connection: str, target: str, domain: str) -> List[Dict]:
        """Get access paths using CySQL query"""
        try:
            cypher_query = f"""
            MATCH path = (s)-[*1..10]->(t)
            WHERE s.name = '{source}' AND t.name = '{target}'
            RETURN path
            """
            
            result = self.execute_query(cypher_query)
            paths = []
            
            if result and isinstance(result, list):
                for path_data in result:
                    # Process path data - this might need adjustment based on actual CySQL response format
                    if isinstance(path_data, dict):
                        paths.append({
                            "source": source,
                            "target": target,
                            "path": path_data
                        })
            
            return paths

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
    
    def close(self):
        """Close the HTTP session"""
        try:
            self.session.close()
        except Exception:
            pass

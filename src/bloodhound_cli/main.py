#!/usr/bin/env python3
import os
import stat
import configparser
from neo4j import GraphDatabase
import argparse
from typing import List, Dict

CONFIG_PATH = os.path.expanduser("~/.bloodhound_config") 

class BloodHoundACEAnalyzer:
    def __init__(self, uri: str, user: str, password: str):
        """Initializes the connection with Neo4j."""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """Closes the connection with Neo4j."""
        self.driver.close()

    def get_critical_aces(self, username: str, high_value: bool = False) -> List[Dict]:
        """Queries ACLs for a specific user."""
        with self.driver.session() as session:
            query = """
            MATCH p=(n)-[r1]->(m)
            WHERE toLower(n.samaccountname) = toLower($samaccountname)
              AND r1.isacl = true AND (m.enabled = true OR m.enabled is NULL)
              """ + ("""AND m.highvalue = true""" if high_value else "") + """
            WITH n, m, r1,
                 CASE 
                     WHEN 'User' IN labels(n) THEN 'User'
                     WHEN 'Group' IN labels(n) THEN 'Group'
                     WHEN 'Computer' IN labels(n) THEN 'Computer'
                     WHEN 'OU' IN labels(n) THEN 'OU'
                     WHEN 'GPO' IN labels(n) THEN 'GPO'
                     WHEN 'Domain' IN labels(n) THEN 'Domain'
                     ELSE 'Other'
                 END AS sourceType,
                 CASE 
                     WHEN 'User' IN labels(n) THEN n.samaccountname
                     WHEN 'Group' IN labels(n) THEN n.samaccountname
                     WHEN 'Computer' IN labels(n) THEN n.samaccountname
                     WHEN 'OU' IN labels(n) THEN n.distinguishedname
                     ELSE n.name
                 END AS source,
                 CASE 
                     WHEN 'User' IN labels(m) THEN 'User'
                     WHEN 'Group' IN labels(m) THEN 'Group'
                     WHEN 'Computer' IN labels(m) THEN 'Computer'
                     WHEN 'OU' IN labels(m) THEN 'OU'
                     WHEN 'GPO' IN labels(m) THEN 'GPO'
                     WHEN 'Domain' IN labels(m) THEN 'Domain'
                     ELSE 'Other'
                 END AS targetType,
                 CASE 
                     WHEN 'User' IN labels(m) THEN m.samaccountname
                     WHEN 'Group' IN labels(m) THEN m.samaccountname
                     WHEN 'Computer' IN labels(m) THEN m.samaccountname
                     WHEN 'OU' IN labels(m) THEN m.distinguishedname
                     ELSE m.name
                 END AS target,
                 CASE
                     WHEN n.domain IS NOT NULL THEN toLower(n.domain)
                     ELSE 'N/A'
                 END AS sourceDomain,
                 CASE
                     WHEN m.domain IS NOT NULL THEN toLower(m.domain)
                     ELSE 'N/A'
                 END AS targetDomain
            RETURN DISTINCT {
                source: source,
                sourceType: sourceType,
                target: target,
                targetType: targetType,
                type: type(r1),
                sourceDomain: sourceDomain,
                targetDomain: targetDomain
            } AS result
            UNION
            MATCH p=(n)-[:MemberOf*1..]->(g:Group)-[r1]->(m)
            WHERE toLower(n.samaccountname) = toLower($samaccountname)
              AND r1.isacl = true AND (m.enabled = true OR m.enabled is NULL)
              """ + ("""AND m.highvalue = true""" if high_value else "") + """
            WITH n, m, r1,
                 CASE 
                     WHEN 'User' IN labels(n) THEN 'User'
                     WHEN 'Group' IN labels(n) THEN 'Group'
                     WHEN 'Computer' IN labels(n) THEN 'Computer'
                     WHEN 'OU' IN labels(n) THEN 'OU'
                     WHEN 'GPO' IN labels(n) THEN 'GPO'
                     WHEN 'Domain' IN labels(n) THEN 'Domain'
                     ELSE 'Other'
                 END AS sourceType,
                 CASE 
                     WHEN 'User' IN labels(n) THEN n.samaccountname
                     WHEN 'Group' IN labels(n) THEN n.samaccountname
                     WHEN 'Computer' IN labels(n) THEN n.samaccountname
                     WHEN 'OU' IN labels(n) THEN n.distinguishedname
                     ELSE n.name
                 END AS source,
                 CASE 
                     WHEN 'User' IN labels(m) THEN 'User'
                     WHEN 'Group' IN labels(m) THEN 'Group'
                     WHEN 'Computer' IN labels(m) THEN 'Computer'
                     WHEN 'OU' IN labels(m) THEN 'OU'
                     WHEN 'GPO' IN labels(m) THEN 'GPO'
                     WHEN 'Domain' IN labels(m) THEN 'Domain'
                     ELSE 'Other'
                 END AS targetType,
                 CASE 
                     WHEN 'User' IN labels(m) THEN m.samaccountname
                     WHEN 'Group' IN labels(m) THEN m.samaccountname
                     WHEN 'Computer' IN labels(m) THEN m.samaccountname
                     WHEN 'OU' IN labels(m) THEN m.distinguishedname
                     ELSE m.name
                 END AS target,
                 CASE
                     WHEN n.domain IS NOT NULL THEN toLower(n.domain)
                     ELSE 'N/A'
                 END AS sourceDomain,
                 CASE
                     WHEN m.domain IS NOT NULL THEN toLower(m.domain)
                     ELSE 'N/A'
                 END AS targetDomain
            RETURN DISTINCT {
                source: source,
                sourceType: sourceType,
                target: target,
                targetType: targetType,
                type: type(r1),
                sourceDomain: sourceDomain,
                targetDomain: targetDomain
            } AS result
            """
            results = session.run(query, samaccountname=username).data()
            return [r["result"] for r in results]

    def print_aces(self, username: str, high_value: bool = False):
        aces = self.get_critical_aces(username, high_value)
        value_suffix = " (high-value targets only)" if high_value else ""
        print(f"\nACLs for user: {username}{value_suffix}")
        print("=" * 50)
        if not aces:
            print("No ACLs found for this user")
            return
        for ace in aces:
            print(f"\nSource: {ace['source']}")
            print(f"Source Type: {ace['sourceType']}")
            print(f"Source Domain: {ace['sourceDomain']}")
            print(f"Target: {ace['target']}")
            print(f"Target Type: {ace['targetType']}")
            print(f"Target Domain: {ace['targetDomain']}")
            print(f"ACL: {ace['type']}")
            print("-" * 50)

    def get_critical_aces_by_domain(self, domain: str, blacklist: List[str], high_value: bool = False) -> List[Dict]:
        with self.driver.session() as session:
            query = """
            MATCH p=(n)-[r1]->(m)
            WHERE r1.isacl = true
              AND toUpper(n.domain) = toUpper($domain)
              AND toUpper(n.domain) <> toUpper(m.domain)
              AND (size($blacklist) = 0 OR NOT toUpper(m.domain) IN $blacklist)
              """ + ("""AND m.highvalue = true""" if high_value else "") + """
            WITH n, m, r1,
                 CASE 
                     WHEN 'User' IN labels(n) THEN 'User'
                     WHEN 'Group' IN labels(n) THEN 'Group'
                     WHEN 'Computer' IN labels(n) THEN 'Computer'
                     WHEN 'OU' IN labels(n) THEN 'OU'
                     WHEN 'GPO' IN labels(n) THEN 'GPO'
                     WHEN 'Domain' IN labels(n) THEN 'Domain'
                     ELSE 'Other'
                 END AS sourceType,
                 CASE 
                     WHEN 'User' IN labels(n) THEN n.samaccountname
                     WHEN 'Group' IN labels(n) THEN n.samaccountname
                     WHEN 'Computer' IN labels(n) THEN n.samaccountname
                     WHEN 'OU' IN labels(n) THEN n.distinguishedname
                     ELSE n.name
                 END AS source,
                 CASE 
                     WHEN 'User' IN labels(m) THEN 'User'
                     WHEN 'Group' IN labels(m) THEN 'Group'
                     WHEN 'Computer' IN labels(m) THEN 'Computer'
                     WHEN 'OU' IN labels(m) THEN 'OU'
                     WHEN 'GPO' IN labels(m) THEN 'GPO'
                     WHEN 'Domain' IN labels(m) THEN 'Domain'
                     ELSE 'Other'
                 END AS targetType,
                 CASE 
                     WHEN 'User' IN labels(m) THEN m.samaccountname
                     WHEN 'Group' IN labels(m) THEN m.samaccountname
                     WHEN 'Computer' IN labels(m) THEN m.samaccountname
                     WHEN 'OU' IN labels(m) THEN m.distinguishedname
                     ELSE m.name
                 END AS target,
                 CASE
                     WHEN n.domain IS NOT NULL THEN toLower(n.domain)
                     ELSE 'N/A'
                 END AS sourceDomain,
                 CASE
                     WHEN m.domain IS NOT NULL THEN toLower(m.domain)
                     ELSE 'N/A'
                 END AS targetDomain
            RETURN DISTINCT {
                source: source,
                sourceType: sourceType,
                target: target,
                targetType: targetType,
                type: type(r1),
                sourceDomain: sourceDomain,
                targetDomain: targetDomain
            } AS result
            UNION
            MATCH p=(n)-[:MemberOf*1..]->(g:Group)-[r1]->(m)
            WHERE r1.isacl = true
              AND toUpper(n.domain) = toUpper($domain)
              AND toUpper(n.domain) <> toUpper(m.domain)
              AND (size($blacklist) = 0 OR NOT toUpper(m.domain) IN $blacklist)
              """ + ("""AND m.highvalue = true""" if high_value else "") + """
            WITH n, m, r1,
                 CASE 
                     WHEN 'User' IN labels(n) THEN 'User'
                     WHEN 'Group' IN labels(n) THEN 'Group'
                     WHEN 'Computer' IN labels(n) THEN 'Computer'
                     WHEN 'OU' IN labels(n) THEN 'OU'
                     WHEN 'GPO' IN labels(n) THEN 'GPO'
                     WHEN 'Domain' IN labels(n) THEN 'Domain'
                     ELSE 'Other'
                 END AS sourceType,
                 CASE 
                     WHEN 'User' IN labels(n) THEN n.samaccountname
                     WHEN 'Group' IN labels(n) THEN n.samaccountname
                     WHEN 'Computer' IN labels(n) THEN n.samaccountname
                     WHEN 'OU' IN labels(n) THEN n.distinguishedname
                     ELSE n.name
                 END AS source,
                 CASE 
                     WHEN 'User' IN labels(m) THEN m.samaccountname
                     WHEN 'Group' IN labels(m) THEN m.samaccountname
                     WHEN 'Computer' IN labels(m) THEN m.samaccountname
                     WHEN 'OU' IN labels(m) THEN m.distinguishedname
                     ELSE m.name
                 END AS targetType,
                 CASE 
                     WHEN 'User' IN labels(m) THEN m.samaccountname
                     WHEN 'Group' IN labels(m) THEN m.samaccountname
                     WHEN 'Computer' IN labels(m) THEN m.samaccountname
                     WHEN 'OU' IN labels(m) THEN m.distinguishedname
                     ELSE m.name
                 END AS target,
                 CASE
                     WHEN n.domain IS NOT NULL THEN toLower(n.domain)
                     ELSE 'N/A'
                 END AS sourceDomain,
                 CASE
                     WHEN m.domain IS NOT NULL THEN toLower(m.domain)
                     ELSE 'N/A'
                 END AS targetDomain
            RETURN DISTINCT {
                source: source,
                sourceType: sourceType,
                target: target,
                targetType: targetType,
                type: type(r1),
                sourceDomain: sourceDomain,
                targetDomain: targetDomain
            } AS result
            """
            results = session.run(query, domain=domain.upper(), blacklist=[d.upper() for d in blacklist]).data()
            return [r["result"] for r in results]

    def print_critical_aces_by_domain(self, domain: str, blacklist: List[str], high_value: bool = False):
        aces = self.get_critical_aces_by_domain(domain, blacklist, high_value)
        value_suffix = " (high-value targets only)" if high_value else ""
        print(f"\nACLs for domain: {domain}{value_suffix}")
        print("=" * 50)
        if not aces:
            print("No ACLs found for this domain")
            return
        for ace in aces:
            print(f"\nSource: {ace['source']}")
            print(f"Source Type: {ace['sourceType']}")
            print(f"Source Domain: {ace['sourceDomain']}")
            print(f"Target: {ace['target']}")
            print(f"Target Type: {ace['targetType']}")
            print(f"Target Domain: {ace['targetDomain']}")
            print(f"ACL: {ace['type']}")
            print("-" * 50)

    def get_computers(self, domain: str, laps: bool = None) -> List[str]:
        with self.driver.session() as session:
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
            results = session.run(query, **params).data()
            return [record["name"] for record in results]

    def print_computers(self, domain: str, output: str = None, laps: bool = None):
        computers = self.get_computers(domain, laps)
        if output:
            try:
                with open(output, "w") as f:
                    for comp in computers:
                        f.write(f"{comp}\n")
                print(f"Results saved to: {output}")
            except Exception as e:
                print(f"Error writing the file: {e}")
        else:
            print(f"\nComputers in domain: {domain}")
            print("=" * 50)
            if not computers:
                print("No computers found for this domain")
            else:
                for comp in computers:
                    print(comp)

    def get_users(self, domain: str) -> List[str]:
        with self.driver.session() as session:
            query = """
            MATCH (u:User)
            WHERE u.enabled = true AND toLower(u.domain) = toLower($domain)
            RETURN u.samaccountname AS samaccountname
            """
            results = session.run(query, domain=domain).data()
            return [record["samaccountname"] for record in results]

    def print_users(self, domain: str, output: str = None):
        users = self.get_users(domain)
        if output:
            try:
                with open(output, "w") as f:
                    for user in users:
                        f.write(f"{user}\n")
                print(f"Results saved to: {output}")
            except Exception as e:
                print(f"Error writing the file: {e}")
        else:
            print(f"\nUsers in domain: {domain}")
            print("=" * 50)
            if not users:
                print("No users found for this domain")
            else:
                for user in users:
                    print(user)

    def get_admin_users(self, domain: str) -> List[str]:
        with self.driver.session() as session:
            query = """
            MATCH p=(u:User)-[:MemberOf*1..]->(g:Group)
            WHERE g.admincount = true
              AND u.admincount = false
              AND u.enabled = true
              AND toLower(u.domain) = toLower($domain)
            RETURN u.samaccountname AS samaccountname
            UNION
            MATCH (u:User {admincount:true})
            WHERE u.enabled = true
              AND toLower(u.domain) = toLower($domain)
            RETURN u.samaccountname AS samaccountname
            """
            results = session.run(query, domain=domain).data()
            return [record["samaccountname"] for record in results]

    def print_admin_users(self, domain: str, output: str = None):
        admin_users = self.get_admin_users(domain)
        if output:
            try:
                with open(output, "w") as f:
                    for user in admin_users:
                        f.write(f"{user}\n")
                print(f"Results saved to: {output}")
            except Exception as e:
                print(f"Error writing the file: {e}")
        else:
            print(f"\nPrivileged (admin) users in domain: {domain}")
            print("=" * 50)
            if not admin_users:
                print("No privileged users found for this domain")
            else:
                for user in admin_users:
                    print(user)

    def get_highvalue_users(self, domain: str) -> List[str]:
        with self.driver.session() as session:
            query = """
            MATCH (u:User {highvalue: true})
            WHERE u.enabled = true AND toLower(u.domain) = toLower($domain)
            RETURN u.samaccountname AS samaccountname
            UNION
            MATCH p=(u:User)-[:MemberOf*1..]->(g:Group {highvalue: true})-[r1]->(m)
            WHERE u.enabled = true AND toLower(u.domain) = toLower($domain)
            RETURN u.samaccountname AS samaccountname
            """
            results = session.run(query, domain=domain).data()
            return [record["samaccountname"] for record in results]

    def print_highvalue_users(self, domain: str, output: str = None):
        highvalue_users = self.get_highvalue_users(domain)
        if output:
            try:
                with open(output, "w") as f:
                    for user in highvalue_users:
                        f.write(f"{user}\n")
                print(f"Results saved to: {output}")
            except Exception as e:
                print(f"Error writing the file: {e}")
        else:
            print(f"\nHigh-value users in domain: {domain}")
            print("=" * 50)
            if not highvalue_users:
                print("No high-value users found for this domain")
            else:
                for user in highvalue_users:
                    print(user)

    def get_password_not_required_users(self, domain: str) -> List[str]:
        with self.driver.session() as session:
            query = """
            MATCH (u:User)
            WHERE u.enabled = true
              AND u.passwordnotreqd = true
              AND toLower(u.domain) = toLower($domain)
            RETURN u.samaccountname AS samaccountname
            """
            results = session.run(query, domain=domain).data()
            return [record["samaccountname"] for record in results]

    def print_password_not_required_users(self, domain: str, output: str = None):
        users = self.get_password_not_required_users(domain)
        if output:
            try:
                with open(output, "w") as f:
                    for user in users:
                        f.write(f"{user}\n")
                print(f"Results saved to: {output}")
            except Exception as e:
                print(f"Error writing the file: {e}")
        else:
            print(f"\nUsers with password not required in domain: {domain}")
            print("=" * 50)
            if not users:
                print("No users with 'passwordnotreqd' found for this domain")
            else:
                for user in users:
                    print(user)

    def get_password_never_expires_users(self, domain: str) -> List[str]:
        """Queries users that have 'pwdneverexpires' enabled in the specified domain."""
        with self.driver.session() as session:
            query = """
            MATCH (u:User)
            WHERE u.enabled = true
              AND u.pwdneverexpires = true
              AND toLower(u.domain) = toLower($domain)
            RETURN u.samaccountname AS samaccountname
            """
            results = session.run(query, domain=domain).data()
            return [record["samaccountname"] for record in results]

    def print_password_never_expires_users(self, domain: str, output: str = None):
        """Prints or saves to a file the list of users with 'pwdneverexpires' enabled in a domain."""
        users = self.get_password_never_expires_users(domain)
        if output:
            try:
                with open(output, "w") as f:
                    for user in users:
                        f.write(f"{user}\n")
                print(f"Results saved to: {output}")
            except Exception as e:
                print(f"Error writing the file: {e}")
        else:
            print(f"\nUsers with 'pwdneverexpires' enabled in domain: {domain}")
            print("=" * 50)
            if not users:
                print("No users with 'pwdneverexpires' found for this domain")
            else:
                for user in users:
                    print(user)
                    
    def execute_custom_query(self, query: str, output: str = None):
        """Executes a custom Cypher query provided by the user."""
        with self.driver.session() as session:
            try:
                results = session.run(query).data()
                if output:
                    try:
                        with open(output, "w") as f:
                            for result in results:
                                f.write(f"{result}\n")
                        print(f"Results saved to: {output}")
                    except Exception as e:
                        print(f"Error writing the file: {e}")
                else:
                    print("\nCustom query results:")
                    print("=" * 50)
                    if not results:
                        print("No results found for this query")
                    else:
                        for result in results:
                            print(result)
                            print("-" * 50)
            except Exception as e:
                print(f"Error executing query: {str(e)}")

def save_config(host: str, port: str, db_user: str, db_password: str):
    """Saves the Neo4j connection configuration to a file in the user's directory."""
    config = configparser.ConfigParser()
    config["NEO4J"] = {
        "host": host,
        "port": port,
        "db_user": db_user,
        "db_password": db_password
    }
    with open(CONFIG_PATH, "w") as configfile:
        config.write(configfile)
    os.chmod(CONFIG_PATH, stat.S_IRUSR | stat.S_IWUSR)
    print(f"Configuration saved at {CONFIG_PATH}")

def load_config():
    """Loads the configuration from the file, if it exists."""
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH)
        return config["NEO4J"]
    else:
        return None

def main():
    parser = argparse.ArgumentParser(
        description="Script to query data in BloodHound (Neo4j)"
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True, help="Available subcommands")

    # set subcommand
    parser_set = subparsers.add_parser("set", help="Saves the connection configuration for Neo4j")
    parser_set.add_argument("--host", required=True, help="Neo4j host")
    parser_set.add_argument("--port", required=True, help="Neo4j port")
    parser_set.add_argument("--db-user", required=True, help="Neo4j user")
    parser_set.add_argument("--db-password", required=True, help="Neo4j password")

    # acl subcommand
    parser_acl = subparsers.add_parser("acl", help="Query ACLs in BloodHound")
    group_acl = parser_acl.add_mutually_exclusive_group(required=True)
    group_acl.add_argument("-u", "--user", help="Username (samaccountname)")
    group_acl.add_argument("-d", "--domain", help="Domain to enumerate ACLs")
    parser_acl.add_argument("-bd", "--blacklist-domains", nargs="*", default=[], help="Exclude these domains (space-separated)")
    parser_acl.add_argument("--high-value", action="store_true", help="Show only ACLs to high-value targets")

    # computer subcommand
    parser_computer = subparsers.add_parser("computer", help="Query computers in BloodHound")
    parser_computer.add_argument("-d", "--domain", required=True, help="Domain to enumerate computers")
    parser_computer.add_argument("-o", "--output", help="Path to file to save results")
    parser_computer.add_argument("--laps", type=str, choices=["True", "False"], help="Filter by haslaps: True or False")

    # user subcommand
    parser_user = subparsers.add_parser("user", help="Query users in BloodHound")
    parser_user.add_argument("-d", "--domain", required=True, help="Domain to enumerate users")
    parser_user.add_argument("-o", "--output", help="Path to file to save results")
    group_value = parser_user.add_mutually_exclusive_group()
    group_value.add_argument("--admin-count", action="store_true", help="Show only users with domain admin privileges (admincount)")
    group_value.add_argument("--high-value", action="store_true", help="Show only high-value users")
    group_value.add_argument("--password-not-required", action="store_true", help="Show only users with 'passwordnotreqd' enabled")
    group_value.add_argument("--password-never-expires", action="store_true", help="Show only users with 'pwdneverexpires' enabled")
    
    # custom subcommand
    parser_custom = subparsers.add_parser("custom", help="Execute a custom Cypher query in BloodHound")
    parser_custom.add_argument("--query", required=True, help="Custom Cypher query to execute")
    parser_custom.add_argument("-o", "--output", help="Path to file to save results")

    args = parser.parse_args()

    if args.subcommand == "set":
        save_config(args.host, args.port, args.db_user, args.db_password)
        return

    if args.subcommand != "set" and not os.path.exists(CONFIG_PATH):
        print("Error: Configuration file not found.")
        print("Please run the 'set' subcommand to set the connection variables, for example:")
        print("  bloodhound-cli.py set --host localhost --port 7687 --db-user neo4j --db-password Bl00dh0und")
        exit(1)

    conf = load_config()
    if conf is None:
        print("Error: No connection configuration found. Please run 'bloodhound-cli.py set ...'")
        exit(1)
    for key in ["host", "port", "db_user", "db_password"]:
        if key not in conf:
            print(f"Error: The key '{key}' was not found in the configuration. Please run 'bloodhound-cli.py set ...'")
            exit(1)

    host = conf["host"]
    port = conf["port"]
    db_user = conf["db_user"]
    db_password = conf["db_password"]
    uri = f"bolt://{host}:{port}"

    analyzer = BloodHoundACEAnalyzer(uri, db_user, db_password)
    try:
        if args.subcommand == "acl":
            if args.user:
                analyzer.print_aces(args.user, args.high_value)
            elif args.domain:
                analyzer.print_critical_aces_by_domain(args.domain, args.blacklist_domains, args.high_value)
        elif args.subcommand == "computer":
            laps = None
            if args.laps is not None:
                laps = True if args.laps.lower() == "true" else False
            analyzer.print_computers(args.domain, args.output, laps)
        elif args.subcommand == "user":
            if args.admin_count:
                analyzer.print_admin_users(args.domain, args.output)
            elif args.high_value:
                analyzer.print_highvalue_users(args.domain, args.output)
            elif args.password_not_required:
                analyzer.print_password_not_required_users(args.domain, args.output)
            elif args.password_never_expires:
                analyzer.print_password_never_expires_users(args.domain, args.output)
            else:
                analyzer.print_users(args.domain, args.output)
        elif args.subcommand == "custom":
            analyzer.execute_custom_query(args.query, args.output)
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()
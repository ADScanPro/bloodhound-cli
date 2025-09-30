#!/usr/bin/env python3
"""
BloodHound CLI - Modular Architecture
"""
import os
import argparse
from typing import List, Dict, Optional
from pathlib import Path

try:
    from rich.console import Console
    from rich import print as rprint
    _RICH_AVAILABLE = True
    console = Console()
except Exception:
    _RICH_AVAILABLE = False
    console = None

from .core.factory import create_bloodhound_client


def load_config():
    """Load configuration from ~/.bloodhound_config"""
    config_path = os.path.expanduser("~/.bloodhound_config")
    if os.path.exists(config_path):
        import configparser
        config = configparser.ConfigParser()
        config.read(config_path)
        return config
    return None


def output_results(results, output_file=None, verbose=False, result_type="results"):
    """Output results to console or file"""
    if output_file:
        try:
            with open(output_file, 'w') as f:
                for result in results:
                    f.write(f"{result}\n")
            if verbose:
                print(f"Results saved to {output_file}")
        except Exception as e:
            print(f"Error writing to file {output_file}: {e}")
            # Fallback to console output
            for result in results:
                print(result)
    else:
        # Console output
        for result in results:
            print(result)


def get_client(edition: str, **kwargs):
    """Get BloodHound client based on edition"""
    config = load_config()
    
    if edition.lower() == 'legacy':
        # Legacy Neo4j connection
        uri = kwargs.get('uri', 'bolt://localhost:7687')
        user = kwargs.get('user', 'neo4j')
        password = kwargs.get('password', 'neo4j')
        
        return create_bloodhound_client(
            'legacy',
            uri=uri,
            user=user,
            password=password,
            debug=kwargs.get('debug', False),
            verbose=kwargs.get('verbose', False)
        )
    
    elif edition.lower() == 'ce':
        # CE HTTP API connection - client will auto-load config from ~/.bloodhound_config
        client = create_bloodhound_client(
            'ce',
            base_url=kwargs.get('base_url'),
            api_token=kwargs.get('api_token'),
            debug=kwargs.get('debug', False),
            verbose=kwargs.get('verbose', False),
            verify=kwargs.get('verify', True)
        )
        
        # Only authenticate if no token is available (either from config or parameters)
        if not client.api_token:
            username = kwargs.get('username', 'admin')
            password = kwargs.get('ce_password', kwargs.get('password', 'Bloodhound123!'))
            client.authenticate(username, password)
        
        return client
    
    else:
        raise ValueError(f"Unsupported edition: {edition}")


def cmd_users(args):
    """List users in a domain"""
    if args.debug:
        print(f"Debug: Creating client for edition {args.edition}")
        print(f"Debug: Domain = {args.domain}")
        print(f"Debug: Password = {args.password}")
        print(f"Debug: High value filter = {args.high_value}")
        print(f"Debug: Admin count filter = {args.admin_count}")
        print(f"Debug: Password never expires filter = {args.password_never_expires}")
        print(f"Debug: Password not required filter = {args.password_not_required}")
        print(f"Debug: Password last change filter = {args.password_last_change}")
        print(f"Debug: Specific user = {args.user}")
    
    client = get_client(
        args.edition,
        uri=args.uri,
        user=args.user,
        password=args.password,
        base_url=args.base_url,
        username=args.username,
        ce_password=getattr(args, 'ce_password', 'Bloodhound123!'),
        debug=args.debug,
        verbose=args.verbose
    )
    
    try:
        if args.debug:
            print(f"Debug: Client created, getting users...")
        
        # Determine which function to call based on parameters
        if args.password_last_change:
            password_info = client.get_password_last_change(args.domain, args.user)
            if args.verbose:
                if args.user:
                    print(f"Password last change information for user {args.user} in domain {args.domain}:")
                else:
                    print(f"Password last change information for all users in domain {args.domain}:")
            
            # Format password info for output
            results = []
            for info in password_info:
                results.append(f"{info['samaccountname']}: pwdlastset={info['pwdlastset']}, whencreated={info['whencreated']}")
            
            output_results(results, args.output, args.verbose, "password info")
            return
            
        elif args.high_value:
            users = client.get_highvalue_users(args.domain)
            user_type = "high value users"
        elif args.admin_count:
            users = client.get_admin_users(args.domain)
            user_type = "admin users"
        elif args.password_never_expires:
            users = client.get_password_never_expires_users(args.domain)
            user_type = "users with password never expires"
        elif args.password_not_required:
            users = client.get_password_not_required_users(args.domain)
            user_type = "users with password not required"
        else:
            users = client.get_users(args.domain)
            user_type = "users"
        
        if args.debug:
            print(f"Debug: Got {len(users)} {user_type}")
        
        if args.verbose:
            print(f"Found {len(users)} {user_type} in domain {args.domain}")
        
        # Output results to console or file
        output_results(users, args.output, args.verbose, user_type)
            
    finally:
        client.close()


def cmd_computers(args):
    """List computers in a domain"""
    client = get_client(
        args.edition,
        uri=args.uri,
        user=args.user,
        password=args.password,
        base_url=args.base_url,
        username=args.username,
        ce_password=getattr(args, 'ce_password', 'Bloodhound123!'),
        debug=args.debug,
        verbose=args.verbose
    )
    
    try:
        # Convert laps string to boolean if provided
        laps_filter = None
        if args.laps:
            laps_filter = args.laps.lower() == 'true'
        
        computers = client.get_computers(args.domain, laps=laps_filter)
        
        if args.verbose:
            print(f"Found {len(computers)} computers in domain {args.domain}")
        
        # Output results to console or file
        output_results(computers, args.output, args.verbose, "computers")
            
    finally:
        client.close()


def cmd_sessions(args):
    """List user sessions in a domain"""
    if args.debug:
        print(f"Debug: Creating client for edition {args.edition}")
        print(f"Debug: Domain = {args.domain}")
        print(f"Debug: DA mode = {args.da}")
    
    client = get_client(
        args.edition,
        uri=args.uri,
        user=args.user,
        password=args.password,
        base_url=args.base_url,
        username=args.username,
        ce_password=getattr(args, 'ce_password', 'Bloodhound123!'),
        debug=args.debug,
        verbose=args.verbose
    )
    
    try:
        sessions = client.get_sessions(args.domain, da=args.da)
        
        if args.verbose:
            if args.da:
                print(f"Found {len(sessions)} sessions from computer perspective in domain {args.domain}")
            else:
                print(f"Found {len(sessions)} sessions from user perspective in domain {args.domain}")
        
        # Format sessions for output
        results = []
        for session in sessions:
            if args.da:
                # Computer -> User format
                results.append(f"{session['computer']} -> {session['user']}")
            else:
                # User -> Computer format
                results.append(f"{session['user']} -> {session['computer']}")
        
        # Output results to console or file
        output_results(results, args.output, args.verbose, "sessions")
            
    finally:
        client.close()


def cmd_acl(args):
    """List critical ACEs"""
    if args.debug:
        print(f"Debug: Creating client for edition {args.edition}")
        print(f"Debug: Source domain = {args.source_domain}")
        print(f"Debug: Source = {args.source}")
        print(f"Debug: Relation = {args.relation}")
        print(f"Debug: Target = {args.target}")
        print(f"Debug: High value = {args.high_value}")
    
    client = get_client(
        args.edition,
        uri=args.uri,
        user=args.user,
        password=args.password,
        base_url=args.base_url,
        username=args.username,
        ce_password=getattr(args, 'ce_password', 'Bloodhound123!'),
        debug=args.debug,
        verbose=args.verbose
    )
    
    try:
        # Use get_critical_aces_by_domain for now (can be enhanced later)
        aces = client.get_critical_aces_by_domain(
            args.source_domain, 
            blacklist=[], 
            high_value=args.high_value
        )
        
        if args.verbose:
            print(f"Found {len(aces)} critical ACEs in domain {args.source_domain}")
        
        # Format ACEs for output
        results = []
        for ace in aces:
            ace_str = f"{ace['source']} -> {ace['target']} ({ace['relation']})"
            results.append(ace_str)
        
        # Output results to console or file
        output_results(results, args.output, args.verbose, "ACEs")
            
    finally:
        client.close()


def main():
    """Main CLI entry point"""
    # Load configuration to get default edition
    config = load_config()
    default_edition = 'ce'  # fallback default to CE
    if config and 'GENERAL' in config and 'edition' in config['GENERAL']:
        default_edition = config['GENERAL']['edition']
    
    parser = argparse.ArgumentParser(description='BloodHound CLI')
    parser.add_argument('--edition', choices=['legacy', 'ce'], default=default_edition,
                       help='BloodHound edition to use')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('-o', '--output', help='Output file to save results')
    
    # Legacy connection options
    parser.add_argument('--uri', default='bolt://localhost:7687',
                       help='Neo4j URI for legacy edition')
    parser.add_argument('--user', default='neo4j', help='Neo4j username')
    parser.add_argument('--password', help='Neo4j password')
    
    # CE connection options
    parser.add_argument('--base-url', default='http://localhost:8080',
                       help='BloodHound CE base URL')
    parser.add_argument('--username', default='admin',
                       help='BloodHound CE username')
    parser.add_argument('--ce-password', default='Bloodhound123!',
                       help='BloodHound CE password')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Users command
    users_parser = subparsers.add_parser('user', help='List users')
    users_parser.add_argument('-d', '--domain', required=True, help='Domain to query')
    users_parser.add_argument('-u', '--user', help='Specific user to query (for password-last-change)')
    users_parser.add_argument('--high-value', action='store_true', help='Show only high value users')
    users_parser.add_argument('--admin-count', action='store_true', help='Show only admin users')
    users_parser.add_argument('--password-never-expires', action='store_true', help='Show only users with password never expires')
    users_parser.add_argument('--password-not-required', action='store_true', help='Show only users with password not required')
    users_parser.add_argument('--password-last-change', action='store_true', help='Show password last change information')
    users_parser.set_defaults(func=cmd_users)
    
    # Computers command
    computers_parser = subparsers.add_parser('computer', help='List computers')
    computers_parser.add_argument('-d', '--domain', required=True, help='Domain to query')
    computers_parser.add_argument('--laps', choices=['true', 'false'], help='Filter by LAPS status (true/false)')
    computers_parser.set_defaults(func=cmd_computers)
    
    # Sessions command
    sessions_parser = subparsers.add_parser('session', help='List user sessions')
    sessions_parser.add_argument('-d', '--domain', required=True, help='Domain to query')
    sessions_parser.add_argument('--da', action='store_true', help='Show sessions from computer perspective (Domain Admin view)')
    sessions_parser.set_defaults(func=cmd_sessions)
    
    # ACL command
    acl_parser = subparsers.add_parser('acl', help='List critical ACEs')
    acl_parser.add_argument('-s', '--source', help='Source username to filter by')
    acl_parser.add_argument('-sd', '--source-domain', required=True, help='Source domain to query')
    acl_parser.add_argument('-r', '--relation', help='Relation type to filter by')
    acl_parser.add_argument('-t', '--target', help='Target to filter by (e.g., high-value)')
    acl_parser.add_argument('--high-value', action='store_true', help='Show only high value targets')
    acl_parser.set_defaults(func=cmd_acl)
    
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        args.func(args)
    except Exception as e:
        if args.debug:
            import traceback
            traceback.print_exc()
        else:
            print(f"Error: {e}")


if __name__ == '__main__':
    main()

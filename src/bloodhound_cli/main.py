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
        users = client.get_users(args.domain)
        
        if args.debug:
            print(f"Debug: Got {len(users)} users")
        
        if args.verbose:
            print(f"Found {len(users)} users in domain {args.domain}")
        
        for user in users:
            print(user)
            
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
        computers = client.get_computers(args.domain, laps=args.laps)
        
        if args.verbose:
            print(f"Found {len(computers)} computers in domain {args.domain}")
        
        for computer in computers:
            print(computer)
            
    finally:
        client.close()


def cmd_admin_users(args):
    """List admin users in a domain"""
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
        admin_users = client.get_admin_users(args.domain)
        
        if args.verbose:
            print(f"Found {len(admin_users)} admin users in domain {args.domain}")
        
        for user in admin_users:
            print(user)
            
    finally:
        client.close()


def cmd_highvalue_users(args):
    """List high value users in a domain"""
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
        hv_users = client.get_highvalue_users(args.domain)
        
        if args.verbose:
            print(f"Found {len(hv_users)} high value users in domain {args.domain}")
        
        for user in hv_users:
            print(user)
            
    finally:
        client.close()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='BloodHound CLI')
    parser.add_argument('--edition', choices=['legacy', 'ce'], default='legacy',
                       help='BloodHound edition to use')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
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
    users_parser.set_defaults(func=cmd_users)
    
    # Computers command
    computers_parser = subparsers.add_parser('computer', help='List computers')
    computers_parser.add_argument('-d', '--domain', required=True, help='Domain to query')
    computers_parser.add_argument('--laps', type=bool, help='Filter by LAPS status')
    computers_parser.set_defaults(func=cmd_computers)
    
    # Admin users command
    admin_parser = subparsers.add_parser('admin', help='List admin users')
    admin_parser.add_argument('-d', '--domain', required=True, help='Domain to query')
    admin_parser.set_defaults(func=cmd_admin_users)
    
    # High value users command
    hv_parser = subparsers.add_parser('highvalue', help='List high value users')
    hv_parser.add_argument('-d', '--domain', required=True, help='Domain to query')
    hv_parser.set_defaults(func=cmd_highvalue_users)
    
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

#!/usr/bin/env python3
import os
import stat
import configparser
from neo4j import GraphDatabase
import argparse
from typing import List, Dict
from datetime import datetime, timezone
import re

CONFIG_PATH = os.path.expanduser("~/.bloodhound_config")

class BloodHoundACEAnalyzer:
    def __init__(self, uri: str, user: str, password: str, debug: bool = False):
        """Initializes the connection with Neo4j."""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.debug = debug

    def close(self):
        """Closes the connection with Neo4j."""
        self.driver.close()

    def render_query(self, query: str, params: dict) -> str:
        """
        Returns a string with the query where placeholders (like $param) are replaced by
        their actual values (strings are wrapped with quotes).
        This is only for debugging purposes.
        """
        def replacer(match):
            key = match.group(0)[1:]
            value = params.get(key)
            if isinstance(value, str):
                return f"'{value}'"
            else:
                return str(value)
        return re.sub(r'\$\w+', replacer, query)

    def execute_query(self, query: str, **params) -> List:
        """
        Helper method to execute a Cypher query.
        If debug is enabled, prints the original query with its parameters, plus
        a fully rendered query with parameters substituted.
        """
        with self.driver.session() as session:
            if self.debug:
                print("DEBUG: Executing query:")
                print(query.strip())
                print("DEBUG: With parameters:", params)
                rendered_query = self.render_query(query, params)
                print("DEBUG: Fully rendered query:")
                print(rendered_query)
            return session.run(query, **params).data()

    def get_critical_aces(self, source_domain: str, high_value: bool = False, username: str = "all",
                            target_domain: str = "all", relation: str = "all") -> List[Dict]:
        """
        Queries ACLs for a specific user (source) with optional filtering on
        source and target domains. If high_value is True, only ACLs for high-value targets are returned.
        """
        # Build domain filters if not "all"
        username_filter = ""
        username_enabled = ""
        relation_filter = "[r1]"
        if relation.lower() != "all":
            relation_filter = "[r1:" + relation + "]"
        if username.lower() != "all":
            username_filter = " toLower(n.samaccountname) = toLower($samaccountname) AND "
        else:
            username_enabled = " {enabled: true}"
        target_filter = ""
        if target_domain.lower() != "all":
            target_filter = " AND toLower(m.domain) = toLower($target_domain) "

        query = """
        MATCH p=(n """ + username_enabled + """)-""" + relation_filter + """->(m)
        WHERE """ + username_filter + """
          r1.isacl = true AND (m.enabled = true OR m.enabled is NULL)
          """ + ("""AND ((m.highvalue = true OR EXISTS((m)-[:MemberOf*1..]->(:Group {highvalue:true}))))""" if high_value else "") + """
          AND toLower(n.domain) = toLower($source_domain)
          AND NOT ((n.highvalue = true OR EXISTS((n)-[:MemberOf*1..]->(:Group {highvalue:true}))))
          AND (m.enabled = true OR m.enabled is NULL)
          """ + target_filter + """
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
        MATCH p=(n """ + username_enabled + """)-[:MemberOf*1..]->(g:Group)-""" + relation_filter + """->(m)
        WHERE """ + username_filter + """
          r1.isacl = true AND (m.enabled = true OR m.enabled is NULL)
          """ + ("""AND ((m.highvalue = true OR EXISTS((m)-[:MemberOf*1..]->(:Group {highvalue:true}))))""" if high_value else "") + """
          AND toLower(n.domain) = toLower($source_domain)
          AND NOT ((n.highvalue = true OR EXISTS((n)-[:MemberOf*1..]->(:Group {highvalue:true}))))
          AND (m.enabled = true OR m.enabled is NULL) 
          """ + target_filter + """
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
        return [r["result"] for r in self.execute_query(query,
                                                         samaccountname=username,
                                                         source_domain=source_domain,
                                                         target_domain=target_domain,
                                                         relation=relation)]

    def get_access_paths(self, source: str, connection: str, target: str, domain: str) -> List[Dict]:
        """
        Constructs and executes a dynamic query based on the following three cases:
        1. If source is not "all" and target is "all":
            - Filters the start node by samaccountname and domain (both case-insensitively).
        2. If source is "all" and target is "all":
            - Returns all start nodes from the specified domain with enabled:true and no admincount.
        3. If source is not "all" and target is "dcs":
            - Filters the start node by samaccountname and domain (case-insensitively) and adds additional filtering for DCs.
        The relationship type in the query is set based on the provided 'connection' parameter.
        The query returns a dictionary (as result) with the same keys as get_critical_aces().
        """
        # Determine if we use the generic relationship with type IN (...) or a specific one.
        if connection.lower() == "all":
            rel_condition = "AND type(r) IN ['AdminTo','CanRDP','CanPSRemote']"
            rel_pattern = "[r]->"  # Generic relationship without type-template
        else:
            rel_condition = ""
            rel_pattern = f"[r:{connection}]->"
            
        if source.lower() != "all" and target.lower() == "all":
            query = f"""
            MATCH p = (n)-{rel_pattern}(m)
            WHERE toLower(n.samaccountname) = toLower($source)
            AND toLower(n.domain) = toLower($domain)
            AND m.enabled = true
            {rel_condition}
            WITH n, m, r,
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
            RETURN DISTINCT {{ source: source, sourceType: sourceType, target: target, targetType: targetType, type: type(r), sourceDomain: sourceDomain, targetDomain: targetDomain }} AS result
            UNION
            MATCH p = (n)-[:MemberOf*1..]->(g:Group)-{rel_pattern}(m)
            WHERE toLower(n.samaccountname) = toLower($source)
            AND toLower(n.domain) = toLower($domain)
            AND m.enabled = true
            {rel_condition}
            WITH n, m, r,
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
            RETURN DISTINCT {{ source: source, sourceType: sourceType, target: target, targetType: targetType, type: type(r), sourceDomain: sourceDomain, targetDomain: targetDomain }} AS result
            """
            params = {"source": source, "domain": domain}
        elif source.lower() == "all" and target.lower() == "all":
            query = f"""
            MATCH p = (n)-{rel_pattern}(m)
            WHERE n.enabled = true
            AND toLower(n.domain) = toLower($domain)
            AND NOT ((n.highvalue = true OR EXISTS((n)-[:MemberOf*1..]->(:Group {{highvalue:true}}))))
            AND m.enabled = true
            {rel_condition}
            WITH n, m, r,
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
            RETURN DISTINCT {{ source: source, sourceType: sourceType, target: target, targetType: targetType, type: type(r), sourceDomain: sourceDomain, targetDomain: targetDomain }} AS result
            UNION
            MATCH p = (n)-[:MemberOf*1..]->(g:Group)-{rel_pattern}(m)
            WHERE n.enabled = true
            AND toLower(n.domain) = toLower($domain)
            AND NOT ((n.highvalue = true OR EXISTS((n)-[:MemberOf*1..]->(:Group {{highvalue:true}}))))
            AND m.enabled = true
            {rel_condition}
            WITH n, m, r,
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
            RETURN DISTINCT {{ source: source, sourceType: sourceType, target: target, targetType: targetType, type: type(r), sourceDomain: sourceDomain, targetDomain: targetDomain }} AS result
            """
            params = {"domain": domain}
        elif source.lower() == "all" and target.lower() == "dcs":
            query = f"""
            MATCH p = (n)-{rel_pattern}(m)
            WHERE n.enabled = true
            AND toLower(n.domain) = toLower($domain)
            AND m.enabled = true
            {rel_condition}
            AND (n.admincount IS NULL OR n.admincount = false)
            AND EXISTS {{
                MATCH (m)-[:MemberOf]->(dc:Group)
                WHERE dc.objectid =~ '(?i)S-1-5-.*-516'
            }}
            WITH n, m, r,
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
            RETURN DISTINCT {{ source: source, sourceType: sourceType, target: target, targetType: targetType, type: type(r), sourceDomain: sourceDomain, targetDomain: targetDomain }} AS result
            UNION
            MATCH p = (n)-[:MemberOf*1..]->(g:Group)-{rel_pattern}(m)
            WHERE n.enabled = true
            AND toLower(n.domain) = toLower($domain)
            AND m.enabled = true
            {rel_condition}
            AND (n.admincount IS NULL OR n.admincount = false)
            AND EXISTS {{
                MATCH (m)-[:MemberOf]->(dc:Group)
                WHERE dc.objectid =~ '(?i)S-1-5-.*-516'
            }}
            WITH n, m, r,
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
            RETURN DISTINCT {{ source: source, sourceType: sourceType, target: target, targetType: targetType, type: type(r), sourceDomain: sourceDomain, targetDomain: targetDomain }} AS result
            """
            params = {"domain": domain}
        else:
            return []
        return self.execute_query(query, **params)

    def print_access(self, source: str, connection: str, target: str, domain: str):
        """
        Prints the access paths based on the provided parameters.
        The output format is similar to that of print_aces.
        Expects each record to contain the key 'result' (a dictionary with the desired fields).
        """
        results = self.get_access_paths(source, connection, target, domain)
        print(f"\nAccess paths for source: {source}, connection: {connection}, target: {target}, domain: {domain}")
        print("=" * 50)
        if not results:
            print("No access paths found")
            return
        for record in results:
            ace = record.get("result")
            if not ace:
                continue
            print(f"\nSource: {ace['source']}")
            print(f"Source Type: {ace['sourceType']}")
            print(f"Source Domain: {ace['sourceDomain']}")
            print(f"Target: {ace['target']}")
            print(f"Target Type: {ace['targetType']}")
            print(f"Target Domain: {ace['targetDomain']}")
            print(f"Relation: {ace['type']}")
            print("-" * 50)

    def get_critical_aces_by_domain(self, domain: str, blacklist: List[str], high_value: bool = False) -> List[Dict]:
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
        results = self.execute_query(query, domain=domain.upper(), blacklist=[d.upper() for d in blacklist])
        return [r["result"] for r in results]

    def get_computers(self, domain: str, laps: bool = None) -> List[str]:
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

    def get_users(self, domain: str) -> List[str]:
        query = """
        MATCH (u:User)
        WHERE u.enabled = true AND toLower(u.domain) = toLower($domain)
        RETURN u.samaccountname AS samaccountname
        """
        results = self.execute_query(query, domain=domain)
        return [record["samaccountname"] for record in results]

    def get_password_last_change(self, domain: str, user: str = None) -> List[dict]:
        """
        Retrieves the pwdlastset value and the whencreated value for enabled users in the specified domain.
        If a user is specified, only returns the record for that user.
        """
        if user:
            query = """
            MATCH (u:User)
            WHERE toLower(u.domain) = toLower($domain)
              AND toLower(u.samaccountname) = toLower($user)
            RETURN toLower(u.samaccountname) AS user, 
                   u.pwdlastset AS password_last_change,
                   u.whencreated AS when_created
            """
            params = {"domain": domain, "user": user}
        else:
            query = """
            MATCH (u:User)
            WHERE u.enabled = true
              AND toLower(u.domain) = toLower($domain)
            RETURN toLower(u.samaccountname) AS user, 
                   u.pwdlastset AS password_last_change,
                   u.whencreated AS when_created
            """
            params = {"domain": domain}
        return self.execute_query(query, **params)

    def get_admin_users(self, domain: str) -> List[str]:
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
        results = self.execute_query(query, domain=domain)
        return [record["samaccountname"] for record in results]

    def get_highvalue_users(self, domain: str) -> List[str]:
        query = """
        MATCH (u:User {highvalue: true})
        WHERE u.enabled = true AND toLower(u.domain) = toLower($domain)
        RETURN u.samaccountname AS samaccountname
        UNION
        MATCH p=(u:User)-[:MemberOf*1..]->(g:Group {highvalue: true})-[r1]->(m)
        WHERE u.enabled = true AND toLower(u.domain) = toLower($domain)
        RETURN u.samaccountname AS samaccountname
        """
        results = self.execute_query(query, domain=domain)
        return [record["samaccountname"] for record in results]

    def get_password_not_required_users(self, domain: str) -> List[str]:
        query = """
        MATCH (u:User)
        WHERE u.enabled = true
          AND u.passwordnotreqd = true
          AND toLower(u.domain) = toLower($domain)
        RETURN u.samaccountname AS samaccountname
        """
        results = self.execute_query(query, domain=domain)
        return [record["samaccountname"] for record in results]

    def get_password_never_expires_users(self, domain: str) -> List[str]:
        """Queries users that have 'pwdneverexpires' enabled in the specified domain."""
        query = """
        MATCH (u:User)
        WHERE u.enabled = true
          AND u.pwdneverexpires = true
          AND toLower(u.domain) = toLower($domain)
        RETURN u.samaccountname AS samaccountname
        """
        results = self.execute_query(query, domain=domain)
        return [record["samaccountname"] for record in results]

    def execute_custom_query(self, query: str, output: str = None):
        """Executes a custom Cypher query provided by the user."""
        try:
            results = self.execute_query(query)
            output_str = "\nCustom query results:\n" + "=" * 50 + "\n"
            if not results:
                output_str += "No results found for this query\n"
            else:
                for result in results:
                    output_str += f"{result}\n" + "-" * 50 + "\n"
            if output:
                try:
                    with open(output, "w") as f:
                        f.write(output_str)
                    print(f"Results saved to: {output}")
                except Exception as e:
                    print(f"Error writing the file: {e}")
            else:
                print(output_str)
        except Exception as e:
            print(f"Error executing query: {str(e)}")

    def get_sessions(self, domain: str, da: bool = False) -> List[dict]:
        """
        Retrieves a list of computers with active sessions in the specified domain.
        If 'da' is True, returns computers with sessions from domain admin users,
        along with the domain admin username.
        """
        if da:
            query = """
            MATCH (dc:Computer)-[r1:MemberOf*0..]->(g1:Group)
            WHERE g1.objectid =~ "S-1-5-.*-516" AND toLower(dc.domain) = toLower($domain)
            WITH COLLECT(dc) AS exclude
            MATCH (c:Computer)-[n:HasSession]->(u:User {enabled:true})
            WHERE NOT c IN exclude AND toLower(c.domain) = toLower($domain)
            AND ((u.highvalue = true OR EXISTS((u)-[:MemberOf*1..]->(:Group {highvalue:true}))))
            RETURN DISTINCT toLower(c.name) AS computer, toLower(u.samaccountname) AS domain_admin
            """
        else:
            query = """
            MATCH (c:Computer)-[n:HasSession]->(u:User {enabled:true})
            WHERE toLower(c.domain) = toLower($domain)
            AND ((u.highvalue = true OR EXISTS((u)-[:MemberOf*1..]->(:Group {highvalue:true}))))
            RETURN DISTINCT toLower(c.name) AS computer
            """
        return self.execute_query(query, domain=domain)

    def print_aces(self, source: str, relation: str, target: str,
                   source_domain: str, target_domain: str):
        """
        Prints ACLs for the given source with filtering based on target type and domains.
        The target parameter accepts "all" or "high-value". When target equals "high-value",
        the query filters only high-value targets.
        The relation parameter is currently not used for query modifications (only accepts "all").
        """
        high_value = (target.lower() == "high-value")
        results = self.get_critical_aces(source_domain, high_value, source, target_domain, relation)
        print(f"\nACLs for source: {source}, target: {target}, "
              f"source domain: {source_domain}, target domain: {target_domain}")
        print("=" * 50)
        if not results:
            print("No ACLs found for the given parameters")
            return
        for ace in results:
            print(f"\nSource: {ace['source']}")
            print(f"Source Type: {ace['sourceType']}")
            print(f"Source Domain: {ace['sourceDomain']}")
            print(f"Target: {ace['target']}")
            print(f"Target Type: {ace['targetType']}")
            print(f"Target Domain: {ace['targetDomain']}")
            print(f"Relation: {ace['type']}")
            print("-" * 50)

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
            print(f"Relation: {ace['type']}")
            print("-" * 50)

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

    def print_password_last_change(self, domain: str, user: str = None, output: str = None):
        data = self.get_password_last_change(domain, user)
        output_str = f"\nPassword Last Change for users in domain: {domain}\n" + "=" * 50 + "\n"
        if not data:
            output_str += "No users found with password last change data.\n"
        else:
            for record in data:
                ts = record.get('password_last_change')
                try:
                    ts_float = float(ts)
                    if ts_float == 0:
                        wc = record.get('when_created')
                        dt = datetime.fromtimestamp(float(wc), tz=timezone.utc)
                        formatted_date = dt.strftime("%A, %Y-%m-%d %H:%M:%S UTC")
                    else:
                        dt = datetime.fromtimestamp(ts_float, tz=timezone.utc)
                        formatted_date = dt.strftime("%A, %Y-%m-%d %H:%M:%S UTC")
                except Exception as e:
                    formatted_date = f"{ts} (error: {e})"
                output_str += f"User: {record['user']} | Password Last Change: {formatted_date}\n"
        if output:
            try:
                with open(output, "w") as f:
                    f.write(output_str)
                print(f"Results saved to: {output}")
            except Exception as e:
                print(f"Error writing file: {e}")
        else:
            print(output_str)

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

    def print_password_never_expires_users(self, domain: str, output: str = None):
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

    def print_sessions(self, domain: str, da: bool = False, output: str = None):
        sessions = self.get_sessions(domain, da)
        if da:
            console_output = f"\nDomain Admin Sessions in domain: {domain}\n" + "=" * 50 + "\n"
        else:
            console_output = f"\nSessions in domain: {domain}\n" + "=" * 50 + "\n"
        file_output = ""
        if not sessions:
            console_output += "No sessions found.\n"
            file_output += "No sessions found.\n"
        else:
            for session_record in sessions:
                if da:
                    console_output += f"Computer: {session_record['computer']} | Domain Admin: {session_record['domain_admin']}\n"
                else:
                    console_output += f"{session_record['computer']}\n"
                file_output += f"{session_record['computer']}\n"
        print(console_output)
        if output:
            try:
                with open(output, "w") as f:
                    f.write(file_output)
                print(f"Results saved to: {output}")
            except Exception as e:
                print(f"Error writing the file: {e}")

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
    # Global debug parameter available for any subcommand
    parser.add_argument("--debug", action="store_true", help="Enable debug mode to show queries")
    subparsers = parser.add_subparsers(dest="subcommand", required=True, help="Available subcommands")

    # set subcommand
    parser_set = subparsers.add_parser("set", help="Saves the connection configuration for Neo4j")
    parser_set.add_argument("--host", required=True, help="Neo4j host")
    parser_set.add_argument("--port", required=True, help="Neo4j port")
    parser_set.add_argument("--db-user", required=True, help="Neo4j user")
    parser_set.add_argument("--db-password", required=True, help="Neo4j password")

    # acl subcommand (refactored)
    parser_acl = subparsers.add_parser("acl", help="Query ACLs in BloodHound")
    parser_acl.add_argument("-s", "--source", default="all", help="Source samaccountname or 'all'")
    parser_acl.add_argument("-t", "--target", default="all",
                            choices=["all", "high-value"],
                            help="Target type: 'all' for all targets, 'high-value' for high-value targets only")
    parser_acl.add_argument("-sd", "--source-domain", required=True, help="Domain for filtering the source node")
    parser_acl.add_argument("-tg", "--target-domain", default="all",
                            help="Domain for filtering the target node; use 'all' to disable filtering")
    parser_acl.add_argument("-r", "--relation", default="all", choices=["all", "DCSync", "ReadGMSAPassword", "ReadLAPSPassword"],
                            help="Relation type (currently 'all' and 'DCSync' is supported)")

    # computer subcommand
    parser_computer = subparsers.add_parser("computer", help="Query computers in BloodHound")
    parser_computer.add_argument("-d", "--domain", required=True, help="Domain to enumerate computers")
    parser_computer.add_argument("-o", "--output", help="Path to file to save results")
    parser_computer.add_argument("--laps", type=str, choices=["True", "False"], help="Filter by haslaps: True or False")

    # user subcommand
    parser_user = subparsers.add_parser("user", help="Query users in BloodHound")
    parser_user.add_argument("-d", "--domain", required=True, help="Domain to enumerate users")
    parser_user.add_argument("-u", "--user", help="User (samaccountname) to query (optional)")
    parser_user.add_argument("-o", "--output", help="Path to file to save results")
    group_value = parser_user.add_mutually_exclusive_group()
    group_value.add_argument("--admin-count", action="store_true", help="Show only users with domain admin privileges (admincount)")
    group_value.add_argument("--high-value", action="store_true", help="Show only high-value users")
    group_value.add_argument("--password-not-required", action="store_true", help="Show only users with 'passwordnotreqd' enabled")
    group_value.add_argument("--password-never-expires", action="store_true", help="Show only users with 'pwdneverexpires' enabled")
    group_value.add_argument("--password-last-change", action="store_true", help="Show the last password change value for user(s)")

    # custom subcommand
    parser_custom = subparsers.add_parser("custom", help="Execute a custom Cypher query in BloodHound")
    parser_custom.add_argument("--query", required=True, help="Custom Cypher query to execute")
    parser_custom.add_argument("-o", "--output", help="Path to file to save results")

    # session subcommand
    parser_session = subparsers.add_parser("session", help="Query sessions in BloodHound")
    parser_session.add_argument("-d", "--domain", required=True, help="Domain to enumerate sessions")
    parser_session.add_argument("--da", action="store_true", help="Show only sessions for domain admins")
    parser_session.add_argument("-o", "--output", help="Path to file to save results")

    # access subcommand
    parser_access = subparsers.add_parser("access", help="Query access paths in BloodHound")
    parser_access.add_argument("-s", "--source", default="all", help="Source samaccountname or 'all'")
    parser_access.add_argument("-r", "--relation", default="all",
                           choices=["all", "AdminTo", "CanRDP", "CanPSRemote"],
                           help="Type of relation (or 'all' for any)")
    parser_access.add_argument("-t", "--target", default="all", choices=["all", "dcs"], help="Target type")
    parser_access.add_argument("-d", "--domain", required=True, help="Domain for filtering nodes")

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

    analyzer = BloodHoundACEAnalyzer(uri, db_user, db_password, debug=args.debug)
    try:
        if args.subcommand == "acl":
            analyzer.print_aces(args.source, args.relation, args.target, args.source_domain, args.target_domain)
        elif args.subcommand == "computer":
            laps = None
            if args.laps is not None:
                laps = True if args.laps.lower() == "true" else False
            analyzer.print_computers(args.domain, args.output, laps)
        elif args.subcommand == "user":
            if args.password_last_change:
                analyzer.print_password_last_change(args.domain, user=args.user, output=args.output)
            elif args.admin_count:
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
        elif args.subcommand == "session":
            analyzer.print_sessions(args.domain, da=args.da, output=args.output)
        elif args.subcommand == "access":
            analyzer.print_access(args.source, args.relation, args.target, args.domain)
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()
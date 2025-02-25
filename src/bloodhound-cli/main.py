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
        """Inicializa la conexión con Neo4j"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """Cierra la conexión con Neo4j"""
        self.driver.close()

    # Métodos de consultas para ACLs, ordenadores y usuarios (se mantienen los mismos que antes)
    def get_critical_aces(self, username: str) -> List[Dict]:
        with self.driver.session() as session:
            query = """
            MATCH p=(n)-[r1]->(m)
            WHERE toLower(n.samaccountname) = toLower($samaccountname)
              AND r1.isacl = true AND m.enabled = true
            WITH n, m, r1,
                 CASE 
                     WHEN 'User' IN labels(n) THEN 'Usuario'
                     WHEN 'Group' IN labels(n) THEN 'Grupo'
                     WHEN 'Computer' IN labels(n) THEN 'Ordenador'
                     WHEN 'OU' IN labels(n) THEN 'Unidad Organizativa'
                     WHEN 'GPO' IN labels(n) THEN 'GPO'
                     WHEN 'Domain' IN labels(n) THEN 'Dominio'
                     ELSE 'Otro'
                 END as sourceType,
                 CASE 
                     WHEN 'User' IN labels(n) THEN n.samaccountname
                     WHEN 'Group' IN labels(n) THEN n.samaccountname
                     WHEN 'Computer' IN labels(n) THEN n.samaccountname
                     WHEN 'OU' IN labels(n) THEN n.distinguishedname
                     ELSE n.name
                 END as source,
                 CASE 
                     WHEN 'User' IN labels(m) THEN 'Usuario'
                     WHEN 'Group' IN labels(m) THEN 'Grupo'
                     WHEN 'Computer' IN labels(m) THEN 'Ordenador'
                     WHEN 'OU' IN labels(m) THEN 'Unidad Organizativa'
                     WHEN 'GPO' IN labels(m) THEN 'GPO'
                     WHEN 'Domain' IN labels(m) THEN 'Dominio'
                     ELSE 'Otro'
                 END as targetType,
                 CASE 
                     WHEN 'User' IN labels(m) THEN m.samaccountname
                     WHEN 'Group' IN labels(m) THEN m.samaccountname
                     WHEN 'Computer' IN labels(m) THEN m.samaccountname
                     WHEN 'OU' IN labels(m) THEN m.distinguishedname
                     ELSE m.name
                 END as target,
                 CASE
                     WHEN n.domain IS NOT NULL THEN toLower(n.domain)
                     ELSE 'N/A'
                 END as sourceDomain,
                 CASE
                     WHEN m.domain IS NOT NULL THEN toLower(m.domain)
                     ELSE 'N/A'
                 END as targetDomain
            RETURN DISTINCT {
                source: source,
                sourceType: sourceType,
                target: target,
                targetType: targetType,
                type: type(r1),
                dominioOrigen: sourceDomain,
                dominioDestino: targetDomain
            } as result
            UNION
            MATCH p=(n)-[:MemberOf*1..]->(g:Group)-[r1]->(m)
            WHERE toLower(n.samaccountname) = toLower($samaccountname)
              AND r1.isacl = true AND m.enabled = true
            WITH n, m, r1,
                 CASE 
                     WHEN 'User' IN labels(n) THEN 'Usuario'
                     WHEN 'Group' IN labels(n) THEN 'Grupo'
                     WHEN 'Computer' IN labels(n) THEN 'Ordenador'
                     WHEN 'OU' IN labels(n) THEN 'Unidad Organizativa'
                     WHEN 'GPO' IN labels(n) THEN 'GPO'
                     WHEN 'Domain' IN labels(n) THEN 'Dominio'
                     ELSE 'Otro'
                 END as sourceType,
                 CASE 
                     WHEN 'User' IN labels(n) THEN n.samaccountname
                     WHEN 'Group' IN labels(n) THEN n.samaccountname
                     WHEN 'Computer' IN labels(n) THEN n.samaccountname
                     WHEN 'OU' IN labels(n) THEN n.distinguishedname
                     ELSE n.name
                 END as source,
                 CASE 
                     WHEN 'User' IN labels(m) THEN 'Usuario'
                     WHEN 'Group' IN labels(m) THEN 'Grupo'
                     WHEN 'Computer' IN labels(m) THEN 'Ordenador'
                     WHEN 'OU' IN labels(m) THEN 'Unidad Organizativa'
                     WHEN 'GPO' IN labels(m) THEN 'GPO'
                     WHEN 'Domain' IN labels(m) THEN 'Dominio'
                     ELSE 'Otro'
                 END as targetType,
                 CASE 
                     WHEN 'User' IN labels(m) THEN m.samaccountname
                     WHEN 'Group' IN labels(m) THEN m.samaccountname
                     WHEN 'Computer' IN labels(m) THEN m.samaccountname
                     WHEN 'OU' IN labels(m) THEN m.distinguishedname
                     ELSE m.name
                 END as target,
                 CASE
                     WHEN n.domain IS NOT NULL THEN toLower(n.domain)
                     ELSE 'N/A'
                 END as sourceDomain,
                 CASE
                     WHEN m.domain IS NOT NULL THEN toLower(m.domain)
                     ELSE 'N/A'
                 END as targetDomain
            RETURN DISTINCT {
                source: source,
                sourceType: sourceType,
                target: target,
                targetType: targetType,
                type: type(r1),
                dominioOrigen: sourceDomain,
                dominioDestino: targetDomain
            } as result
            """
            results = session.run(query, samaccountname=username).data()
            return [r["result"] for r in results]

    def print_aces(self, username: str):
        aces = self.get_critical_aces(username)
        print(f"\nACLs para usuario: {username}")
        print("=" * 50)
        if not aces:
            print("No se encontraron ACLs para este usuario")
            return
        for ace in aces:
            print(f"\nOrigen: {ace['source']}")
            print(f"Tipo Origen: {ace['sourceType']}")
            print(f"Dominio Origen: {ace['dominioOrigen']}")
            print(f"Destino: {ace['target']}")
            print(f"Tipo Destino: {ace['targetType']}")
            print(f"Dominio Destino: {ace['dominioDestino']}")
            print(f"ACL: {ace['type']}")
            print("-" * 50)

    def get_critical_aces_by_domain(self, domain: str, blacklist: List[str]) -> List[Dict]:
        with self.driver.session() as session:
            query = """
            MATCH p=(n)-[r1]->(m)
            WHERE r1.isacl = true
              AND toUpper(n.domain) = toUpper($domain)
              AND toUpper(n.domain) <> toUpper(m.domain)
              AND (size($blacklist) = 0 OR NOT toUpper(m.domain) IN $blacklist)
            WITH n, m, r1,
                 CASE 
                     WHEN 'User' IN labels(n) THEN 'Usuario'
                     WHEN 'Group' IN labels(n) THEN 'Grupo'
                     WHEN 'Computer' IN labels(n) THEN 'Ordenador'
                     WHEN 'OU' IN labels(n) THEN 'Unidad Organizativa'
                     WHEN 'GPO' IN labels(n) THEN 'GPO'
                     WHEN 'Domain' IN labels(n) THEN 'Dominio'
                     ELSE 'Otro'
                 END AS sourceType,
                 CASE 
                     WHEN 'User' IN labels(n) THEN n.samaccountname
                     WHEN 'Group' IN labels(n) THEN n.samaccountname
                     WHEN 'Computer' IN labels(n) THEN n.samaccountname
                     WHEN 'OU' IN labels(n) THEN n.distinguishedname
                     ELSE n.name
                 END AS source,
                 CASE 
                     WHEN 'User' IN labels(m) THEN 'Usuario'
                     WHEN 'Group' IN labels(m) THEN 'Grupo'
                     WHEN 'Computer' IN labels(m) THEN 'Ordenador'
                     WHEN 'OU' IN labels(m) THEN 'Unidad Organizativa'
                     WHEN 'GPO' IN labels(m) THEN 'GPO'
                     WHEN 'Domain' IN labels(m) THEN 'Dominio'
                     ELSE 'Otro'
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
                dominioOrigen: sourceDomain,
                dominioDestino: targetDomain
            } AS result
            UNION
            MATCH p=(n)-[:MemberOf*1..]->(g:Group)-[r1]->(m)
            WHERE r1.isacl = true
              AND toUpper(n.domain) = toUpper($domain)
              AND toUpper(n.domain) <> toUpper(m.domain)
              AND (size($blacklist) = 0 OR NOT toUpper(m.domain) IN $blacklist)
            WITH n, m, r1,
                 CASE 
                     WHEN 'User' IN labels(n) THEN 'Usuario'
                     WHEN 'Group' IN labels(n) THEN 'Grupo'
                     WHEN 'Computer' IN labels(n) THEN 'Ordenador'
                     WHEN 'OU' IN labels(n) THEN 'Unidad Organizativa'
                     WHEN 'GPO' IN labels(n) THEN 'GPO'
                     WHEN 'Domain' IN labels(n) THEN 'Dominio'
                     ELSE 'Otro'
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
                dominioOrigen: sourceDomain,
                dominioDestino: targetDomain
            } AS result
            """
            results = session.run(query, domain=domain.upper(), blacklist=[d.upper() for d in blacklist]).data()
            return [r["result"] for r in results]

    def print_aces_by_domain(self, domain: str, blacklist: List[str]):
        aces = self.get_critical_aces_by_domain(domain, blacklist)
        print(f"\nACLs para dominio: {domain}")
        print("=" * 50)
        if not aces:
            print("No se encontraron ACLs para este dominio")
            return
        for ace in aces:
            print(f"\nOrigen: {ace['source']}")
            print(f"Tipo Origen: {ace['sourceType']}")
            print(f"Dominio Origen: {ace['dominioOrigen']}")
            print(f"Destino: {ace['target']}")
            print(f"Tipo Destino: {ace['targetType']}")
            print(f"Dominio Destino: {ace['dominioDestino']}")
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
                print(f"Resultados guardados en: {output}")
            except Exception as e:
                print(f"Error al escribir el archivo: {e}")
        else:
            print(f"\nOrdenadores en el dominio: {domain}")
            print("=" * 50)
            if not computers:
                print("No se encontraron ordenadores para este dominio")
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
                print(f"Resultados guardados en: {output}")
            except Exception as e:
                print(f"Error al escribir el archivo: {e}")
        else:
            print(f"\nUsuarios en el dominio: {domain}")
            print("=" * 50)
            if not users:
                print("No se encontraron usuarios para este dominio")
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
                print(f"Resultados guardados en: {output}")
            except Exception as e:
                print(f"Error al escribir el archivo: {e}")
        else:
            print(f"\nUsuarios con privilegios en el dominio: {domain}")
            print("=" * 50)
            if not admin_users:
                print("No se encontraron usuarios con privilegios para este dominio")
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
                print(f"Resultados guardados en: {output}")
            except Exception as e:
                print(f"Error al escribir el archivo: {e}")
        else:
            print(f"\nUsuarios de alto valor en el dominio: {domain}")
            print("=" * 50)
            if not highvalue_users:
                print("No se encontraron usuarios de alto valor para este dominio")
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
                print(f"Resultados guardados en: {output}")
            except Exception as e:
                print(f"Error al escribir el archivo: {e}")
        else:
            print(f"\nUsuarios con password not required en el dominio: {domain}")
            print("=" * 50)
            if not users:
                print("No se encontraron usuarios con 'passwordnotreqd' habilitado para este dominio")
            else:
                for user in users:
                    print(user)

    def get_password_never_expires_users(self, domain: str) -> List[str]:
        """Consulta los usuarios que tienen habilitado el atributo pwdneverexpires en el dominio especificado."""
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
        """Imprime o guarda en archivo la lista de usuarios con pwdneverexpires habilitado en un dominio."""
        users = self.get_password_never_expires_users(domain)
        if output:
            try:
                with open(output, "w") as f:
                    for user in users:
                        f.write(f"{user}\n")
                print(f"Resultados guardados en: {output}")
            except Exception as e:
                print(f"Error al escribir el archivo: {e}")
        else:
            print(f"\nUsuarios con 'pwdneverexpires' habilitado en el dominio: {domain}")
            print("=" * 50)
            if not users:
                print("No se encontraron usuarios con 'pwdneverexpires' habilitado para este dominio")
            else:
                for user in users:
                    print(user)

def save_config(host: str, port: str, db_user: str, db_password: str):
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
    print(f"Configuración guardada en {CONFIG_PATH}")

def load_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH)
        return config["NEO4J"]
    else:
        return None

def main():
    parser = argparse.ArgumentParser(
        description="Script para consultar datos en BloodHound (Neo4j)"
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True, help="Subcomandos disponibles")

    # Subcomando set
    parser_set = subparsers.add_parser("set", help="Guarda la configuración de conexión a Neo4j")
    parser_set.add_argument("--host", required=True, help="Host de Neo4j")
    parser_set.add_argument("--port", required=True, help="Puerto de Neo4j")
    parser_set.add_argument("--db-user", required=True, help="Usuario de Neo4j")
    parser_set.add_argument("--db-password", required=True, help="Password de Neo4j")

    # Subcomando ACLs
    parser_acl = subparsers.add_parser("acl", help="Consulta ACLs en BloodHound")
    group_acl = parser_acl.add_mutually_exclusive_group(required=True)
    group_acl.add_argument("-u", "--user", help="Nombre de usuario (samaccountname)")
    group_acl.add_argument("-d", "--domain", help="Dominio para enumerar ACLs")
    parser_acl.add_argument("-bd", "--blacklist-domains", nargs="*", default=[], help="Dominios a excluir (separados por espacios)")

    # Subcomando ordenadores
    parser_computer = subparsers.add_parser("computer", help="Consulta ordenadores en BloodHound")
    parser_computer.add_argument("-d", "--domain", required=True, help="Dominio para enumerar ordenadores")
    parser_computer.add_argument("-o", "--output", help="Ruta del archivo para guardar resultados")
    parser_computer.add_argument("--laps", type=str, choices=["True", "False"], help="Filtro por haslaps: True o False")

    # Subcomando usuarios
    parser_user = subparsers.add_parser("user", help="Consulta usuarios en BloodHound")
    parser_user.add_argument("-d", "--domain", required=True, help="Dominio para enumerar usuarios")
    parser_user.add_argument("-o", "--output", help="Ruta del archivo para guardar resultados")
    group_value = parser_user.add_mutually_exclusive_group()
    group_value.add_argument("--admin-count", action="store_true", help="Selecciona solo usuarios con privilegios del dominio")
    group_value.add_argument("--high-value", action="store_true", help="Selecciona solo usuarios de alto valor")
    group_value.add_argument("--password-not-required", action="store_true", help="Selecciona solo usuarios con 'passwordnotreqd' habilitado")
    group_value.add_argument("--password-never-expires", action="store_true", help="Selecciona solo usuarios con 'pwdneverexpires' habilitado")

    args = parser.parse_args()

    if args.subcommand == "set":
        save_config(args.host, args.port, args.db_user, args.db_password)
        return

    if args.subcommand != "set" and not os.path.exists(CONFIG_PATH):
        print("Error: No se encontró el archivo de configuración.")
        print("Por favor, ejecute el subcomando 'set' para establecer las variables de conexión, por ejemplo:")
        print("  python bloodhound_query.py set --host localhost --port 7687 --db-user neo4j --db-password Bl00dh0und")
        exit(1)

    conf = load_config()
    if conf is None:
        print("Error: No se encontró la configuración de conexión. Ejecute 'python bloodhound_query.py set ...'")
        exit(1)
    for key in ["host", "port", "db_user", "db_password"]:
        if key not in conf:
            print(f"Error: La clave '{key}' no se encontró en la configuración. Ejecute 'python bloodhound_query.py set ...'")
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
                analyzer.print_aces(args.user)
            elif args.domain:
                analyzer.print_aces_by_domain(args.domain, args.blacklist_domains)
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
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()
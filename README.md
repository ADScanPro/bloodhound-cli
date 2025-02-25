# bloodhound-cli

**bloodhound-cli** is a Python command-line tool designed to query and manage data from a **BloodHound** database running on **Neo4j**. It enables you to enumerate ACLs, computers, and users (including filtering by attributes like password not required or password never expires) in an Active Directory environment ingested by BloodHound.

## Key Features

1. **Configuration Management**
    
    - Save your Neo4j connection details (host, port, user, and password) to a local configuration file (`~/.bloodhound_config`) using the `set` subcommand.
    - The configuration file is stored with restricted permissions (`chmod 600`) to protect your sensitive credentials.
2. **ACL Queries (`acl` subcommand)**
    
    - Enumerate ACLs related to a single user by specifying `-u/--user`.
    - Enumerate cross-domain ACLs for a domain by specifying `-d/--domain`.
    - Optionally exclude multiple domains with `-bd/--blacklist-domains`.
3. **Computer Queries (`computer` subcommand)**
    
    - Enumerate computers within a specified domain (`-d`).
    - Optionally save results to a file (`-o`).
    - Filter by LAPS status (`--laps True/False`).
4. **User Queries (`user` subcommand)**

    - Enumerate users within a specified domain (`-d`).
    - Optionally save results to a file (`-o`).
    - Use mutually exclusive filters to target specific user attributes:
        - `--admin-count`: Show only privileged (admin) users.
        - `--high-value`: Show only high-value users.
        - `--password-not-required`: Show only users with `passwordnotreqd` enabled.
        - `--password-never-expires`: Show only users with `pwdneverexpires` enabled.
6. **Secure Credential Storage**

    - The `set` subcommand saves your Neo4j credentials in a local file (`~/.bloodhound_config`) which is excluded from source control and has strict file permissions.

## Installation

It is recommended to install **bloodhound-cli** using [pipx](https://github.com/pipxproject/pipx) to ensure it runs in an isolated environment. You can install it from PyPI:

```sh
pipx install bloodhound-cli
```

Alternatively, you can use pip:

```sh
pip install bloodhound-cli
```

## Usage

1. **Set Neo4j Configuration**  
    Before using any other subcommand, run:
    
    ```sh
    bloodhound-cli set --host <neo4j_host> --port <neo4j_port> --db-user <neo4j_user> --db-password <neo4j_password>
    ```
    
    This will create/update a configuration file at `~/.bloodhound_config`.
    
2. **Enumerate ACLs**
    
    - **For a single user:**
        
        ```sh
        bloodhound-cli acl --user myuser
        ```
        
    - **For cross-domain:**
        
        ```sh
        bloodhound-cli acl --domain mydomain.local
        ```
        
    - **Exclude multiple domains:**
        
        ```sh
        bloodhound-cli acl --domain mydomain.local -bd EXCLUDED1 EXCLUDED2
        ```
        
3. **Enumerate Computers**
    
    - **All computers in a domain:**
        
        ```sh
        bloodhound-cli computer --domain mydomain.local
        ```
        
    - **Filter by LAPS and save results:**
        
        ```sh
        bloodhound-cli computer --domain mydomain.local --laps True -o computers_with_laps.txt
        ```
        
4. **Enumerate Users**
    
    - **List all users in a domain:**
        
        ```sh
        bloodhound-cli user --domain mydomain.local
        ```
        
    - **List privileged (admin) users:**
        
        ```sh
        bloodhound-cli user --domain mydomain.local --admin-count
        ```
        
    - **List high-value users:**
        
        ```sh
        bloodhound-cli user --domain mydomain.local --high-value
        ```
        
    - **List users with password not required:**
        
        ```sh
        bloodhound-cli user --domain mydomain.local --password-not-required
        ```
        
    - **List users with password never expires:**
        
        ```sh
        bloodhound-cli user --domain mydomain.local --password-never-expires
        ```
        
    - **Save user query results:**
        
        ```sh
        bloodhound-cli user --domain mydomain.local --admin-count -o admin_users.txt
        ```

## License

This project is licensed under the MIT License.

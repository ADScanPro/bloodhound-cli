# bloodhound-cli

**bloodhound-cli** is a Python command-line tool designed to query and manage data from **BloodHound**.

- Legacy (Neo4j-backed) is fully supported.
- Community Edition (CE) is introduced with a pluggable client skeleton so behavior can be incrementally implemented without breaking legacy users.

>CE support note: This CLI now includes an early CE client. Many CE features are placeholders. If you need the official SpecterOps CE installer CLI, see their project at `https://github.com/specterOps/bloodHound-cli`.

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
5. **Session and Access Queries**

    - Query sessions and access path relations in a domain (legacy).

6. **Debug and Verbose Output**

    - Global flags `--debug` and `--verbose` enhance output. When available, output is formatted with `rich`.

7. **Secure Credential Storage**

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

1. **Set Neo4j (Legacy) Configuration**  

    ```sh
    bloodhound-cli set --host <neo4j_host> --port <neo4j_port> --db-user <neo4j_user> --db-password <neo4j_password>
    ```

2. **Set CE Configuration (optional, early support)**

    (Removed) Use the auth subcommand passing --base-url and credentials instead.

3. **Authenticate to CE (generate and store token)**

    ```sh
    bloodhound-cli --edition ce auth --url http://localhost:7474 --username <user>
    # It will prompt for the password securely
    # Optional flags:
    #   --password <pass>
    #   --login-path /api/v2/login
    #   --insecure
    ```

4. **Run in a chosen edition**

    - The default edition can be persisted in `~/.bloodhound_config` under `[GENERAL] edition`.
      Running `set` will store `legacy`; running `auth` will store `ce`.

    - To target CE explicitly:

    ```sh
    bloodhound-cli --edition ce user --domain mydomain.local
    ```

    - Or via env var:

    ```sh
    BLOODHOUND_EDITION=ce bloodhound-cli user --domain mydomain.local
    ```

5. **Upload collector artifacts to CE (v2 file-upload flow)**

    ```sh
    bloodhound-cli --edition ce upload \
      -f data1.zip data2.json \
      --start-path /api/v2/file-upload/start \
      --upload-path /api/v2/file-upload/{job_id} \
      --end-path /api/v2/file-upload/{job_id}/end
    # Optional flags:
    #   --content-type application/zip|application/json (auto-detected if omitted)
    #   --insecure
    ```

6. **Enumerate ACLs**

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

7. **Enumerate Computers**

    - **All computers in a domain:**

        ```sh
        bloodhound-cli computer --domain mydomain.local
        ```

    - **Filter by LAPS and save results:**

        ```sh
        bloodhound-cli computer --domain mydomain.local --laps True -o computers_with_laps.txt
        ```

8. **Enumerate Users**

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

## Edition Support Details

- `--edition legacy` (default): full feature set (Neo4j backend).
- `--edition ce`: CE client with support for `auth` (/api/v2/login) y `upload` (flow de file-upload v2). El resto de comandos imprimirán un mensaje hasta estar conectados a CE.

## Changelog

- 0.2.0
  - Add `--edition` and `--verbose` global flags
  - Add CE configuration `set-ce` and CE client skeleton
  - Add CE `auth` (JWT via `/api/v2/login`) and `upload` (file-upload `/start`, `/{job_id}`, `/{job_id}/end`)
  - Integrate `rich` for debug/verbose output
  - Dependencies: add `requests`, `rich`

## License

This project is licensed under the MIT License.

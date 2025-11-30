# bloodhound-cli

**bloodhound-cli** is a Python command-line tool designed to query and manage data from **BloodHound** with support for both Legacy (Neo4j) and Community Edition (CE) backends.

## 🏗️ **Modular Architecture**

The CLI now features a clean, modular architecture that eliminates code duplication and follows best practices:

```
src/bloodhound_cli/
├── core/
│   ├── base.py          # Abstract base class with common interface
│   ├── legacy.py        # Neo4j implementation
│   ├── ce.py           # HTTP API implementation  
│   └── factory.py      # Factory pattern for client creation
├── main.py             # CLI entry point
└── tests/              # Comprehensive test suite
```

## ✨ **Key Features**

### 🔄 **Dual Backend Support**
- **Legacy (Neo4j)**: Full feature set with direct Neo4j queries
- **Community Edition (CE)**: HTTP API integration with BloodHound CE

### 🎯 **Unified Interface**
- Same commands work with both backends
- Automatic client selection based on `--edition` flag
- No code duplication - queries centralized in base classes

### 🧪 **Comprehensive Testing**
- Unit tests with mocks for isolated testing
- Integration tests with real BloodHound CE and GOAD data
- Docker-based test environment with realistic data

### 🔧 **Advanced Query Support**
- User enumeration with domain filtering
- Computer enumeration with LAPS filtering
- Admin and high-value user detection
- Password policy analysis
- Session and access path queries

## 🚀 **Installation**

> The CLI and development tooling require Python **3.9 or newer**.

### Recommended: pipx (isolated environment)
```bash
pipx install bloodhound-cli
```

### Alternative: pip
```bash
pip install bloodhound-cli
```

### Development: from source
```bash
git clone https://github.com/ADScanPro/bloodhound-cli.git
cd bloodhound-cli
uv pip install -e .[dev]
```

> The `.[dev]` extra installs linting and testing tooling (`ruff`, `pylint`, `pytest`). Use `uv` for all dependency management to keep environments reproducible.
> Version control the generated `uv.lock` so anyone cloning the repo can run `uv pip sync` and get the exact same dependency set.

## 📖 **Usage**

### **Basic Commands**

#### List Users
```bash
# Legacy (Neo4j)
bloodhound-cli --edition legacy user -d mydomain.local

# Community Edition (CE)  
bloodhound-cli --edition ce user -d mydomain.local
```

#### Show Version
```bash
bloodhound-cli version
# or
bloodhound-cli --version
```

#### List Group Memberships For A User
```bash
# Resolve recursive memberships (default)
bloodhound-cli --edition ce group -d mydomain.local -u alice

# Only direct memberships
bloodhound-cli group -d mydomain.local -u alice --direct-only
```

#### List Computers
```bash
# All computers
bloodhound-cli --edition ce computer -d mydomain.local

# Filter by LAPS
bloodhound-cli --edition ce computer -d mydomain.local --laps true
```

#### Admin Users
```bash
bloodhound-cli --edition ce admin -d mydomain.local
```

#### High Value Users
```bash
bloodhound-cli --edition ce highvalue -d mydomain.local
```

### **Connection Configuration**

#### Legacy (Neo4j)
```bash
bloodhound-cli --edition legacy user -d mydomain.local \
  --uri bolt://localhost:7687 \
  --user neo4j \
  --password mypassword
```

#### Community Edition (CE)
```bash
bloodhound-cli --edition ce user -d mydomain.local \
  --base-url http://localhost:8080 \
  --username admin \
  --ce-password Bloodhound123!
```

### **Debug and Verbose Output**
```bash
bloodhound-cli --edition ce --debug --verbose user -d mydomain.local
```

## 🧪 **Testing**

### **Unit Tests**
```bash
pytest tests/unit/ -v
```

### **Integration Tests**
```bash
# Requires BloodHound CE running
pytest tests/integration/ -v
```

### **Full Test Suite with GOAD Data**
```bash
# Setup test environment with GOAD data
./scripts/setup-complete.sh
./scripts/test-with-goad-domains.sh
```

## 🏛️ **Architecture Benefits**

### ✅ **No Code Duplication**
- Queries defined once in base classes
- Legacy and CE implementations inherit common interface
- Changes propagate automatically to both backends

### ✅ **Easy Extension**
- Add new queries by implementing abstract methods
- Factory pattern handles client creation
- Clean separation of concerns

### ✅ **Comprehensive Testing**
- Unit tests with mocks for fast feedback
- Integration tests with real data
- Docker-based test environment

### ✅ **Maintainable Code**
- Clear separation between CLI, core logic, and implementations
- Type hints and documentation
- Follows Python best practices

## 🔧 **Development**

### **Project Structure**
```
bloodhound-cli/
├── src/bloodhound_cli/
│   ├── core/           # Core business logic
│   ├── main.py         # CLI entry point
│   └── __init__.py
├── tests/              # Test suite
├── scripts/            # Automation scripts
└── test-data/          # Test data (GOAD)
```

### **Adding New Queries**
1. Add method to `BloodHoundClient` base class
2. Implement in both `BloodHoundLegacyClient` and `BloodHoundCEClient`
3. Add CLI command in `main.py`
4. Create tests in `tests/`

### **Testing Strategy**
- **Unit Tests**: Mock external dependencies
- **Integration Tests**: Real BloodHound CE with GOAD data
- **CI/CD**: Automated testing with Docker

## 📊 **Supported Domains (GOAD Test Data)**

The project includes comprehensive test data from GOAD (Game of Active Directory):

- **north.sevenkingdoms.local**: House Stark domain
- **essos.local**: Daenerys Targaryen domain  
- **sevenkingdoms.local**: King's Landing domain

## ⚠️ **Legacy Edition Status**

The legacy Neo4j edition is kept for archival purposes only and no longer receives active development. We strongly recommend using the BloodHound Community Edition (CE) client, which is the maintained and tested path in this CLI.

## 🎯 **Roadmap**

- [ ] Complete all Legacy queries for CE
- [ ] Add more advanced query capabilities
- [ ] Enhanced error handling and logging
- [ ] Performance optimizations
- [ ] Additional test coverage

## 📄 **License**

This project is licensed under the MIT License.

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📞 **Support**

For issues and questions:
- Create an issue on GitHub
- Check the test suite for usage examples
- Review the integration tests for setup guidance

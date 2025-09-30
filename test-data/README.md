# GOAD Test Data Structure

## 📁 Estructura de Directorios

```
test-data/
├── goad/                    # Datos GOAD extraídos
│   ├── ZA/                  # Domain ZA (Zombie Apocalypse)
│   │   ├── users.json
│   │   ├── computers.json
│   │   ├── groups.json
│   │   ├── domains.json
│   │   ├── ous.json
│   │   ├── gpos.json
│   │   └── ...
│   ├── TB/                  # Domain TB (The Big One)
│   │   ├── users.json
│   │   ├── computers.json
│   │   ├── groups.json
│   │   └── ...
│   └── AD/                  # Domain AD (Attack Domain)
│       ├── users.json
│       ├── computers.json
│       ├── groups.json
│       └── ...
└── README.md               # Este archivo
```

## 🎯 Cómo Configurar los Datos GOAD

### Opción 1: Script Automático (Recomendado)
```bash
# 1. Coloca tus ZIPs de GOAD en el directorio raíz del proyecto
#    - ZA_domain.zip (o similar)
#    - TB_domain.zip (o similar)  
#    - AD_domain.zip (o similar)

# 2. Ejecuta el script de setup
./scripts/setup-goad-data.sh
```

### Opción 2: Configuración Manual
```bash
# 1. Crear directorios
mkdir -p test-data/goad/{ZA,TB,AD}

# 2. Extraer cada ZIP a su directorio correspondiente
unzip ZA_domain.zip -d test-data/goad/ZA/
unzip TB_domain.zip -d test-data/goad/TB/
unzip AD_domain.zip -d test-data/goad/AD/
```

### Opción 3: Variables de Entorno
```bash
# Configurar rutas específicas
export GOAD_ZA_ZIP="/path/to/ZA_domain.zip"
export GOAD_TB_ZIP="/path/to/TB_domain.zip"
export GOAD_AD_ZIP="/path/to/AD_domain.zip"

# Ejecutar setup
./scripts/setup-goad-data.sh
```

## 📊 Dominios GOAD

### ZA (Zombie Apocalypse)
- **Descripción**: Dominio principal con estructura compleja
- **Archivos**: users.json, computers.json, groups.json, etc.
- **Uso**: Tests principales de funcionalidad

### TB (The Big One)
- **Descripción**: Dominio secundario con relaciones cruzadas
- **Archivos**: users.json, computers.json, groups.json, etc.
- **Uso**: Tests de relaciones entre dominios

### AD (Attack Domain)
- **Descripción**: Dominio de ataque con ACLs específicas
- **Archivos**: users.json, computers.json, groups.json, etc.
- **Uso**: Tests de ACLs y permisos

## 🧪 Uso en Tests

### Tests Unitarios
```bash
# Tests con mocks (no necesitan datos reales)
pytest tests/unit/ -v
```

### Tests de Integración
```bash
# Tests con datos GOAD reales
./scripts/setup-complete.sh
```

### Tests Específicos por Dominio
```bash
# Test solo con dominio ZA
export GOAD_DOMAIN="ZA"
pytest tests/integration/ -v

# Test solo con dominio TB
export GOAD_DOMAIN="TB"
pytest tests/integration/ -v
```

## 🔧 Comandos Útiles

### Verificar Estructura
```bash
# Ver estructura de datos
tree test-data/goad/

# Contar archivos por dominio
find test-data/goad/ZA -name "*.json" | wc -l
find test-data/goad/TB -name "*.json" | wc -l
find test-data/goad/AD -name "*.json" | wc -l
```

### Cargar Datos en BloodHound
```bash
# Cargar dominio ZA
bloodhound-cli upload test-data/goad/ZA/

# Cargar dominio TB
bloodhound-cli upload test-data/goad/TB/

# Cargar dominio AD
bloodhound-cli upload test-data/goad/AD/
```

### Limpiar Datos
```bash
# Limpiar datos extraídos
rm -rf test-data/goad/

# Limpiar BloodHound
bloodhound-cli stop
bloodhound-cli start
```

## 📋 Archivos Esperados por Dominio

Cada dominio debe contener:
- `users.json` - Usuarios del dominio
- `computers.json` - Computadoras del dominio
- `groups.json` - Grupos del dominio
- `domains.json` - Información del dominio
- `ous.json` - Unidades organizativas
- `gpos.json` - Políticas de grupo
- `sessions.json` - Sesiones activas
- `acls.json` - Listas de control de acceso

## ✅ Verificación

Para verificar que los datos están correctamente configurados:

```bash
# Verificar estructura
./scripts/setup-goad-data.sh

# Verificar BloodHound
bloodhound-cli status

# Verificar datos cargados
curl http://localhost:8080/api/v2/statistics
```

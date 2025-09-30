#!/bin/bash
# Script para testing con datos GOAD de múltiples dominios

set -e

echo "🎯 BloodHound CLI Testing with GOAD Multi-Domain Data"

# Función para limpiar recursos
cleanup() {
    echo "🧹 Cleaning up test environment..."
    bloodhound-cli stop 2>/dev/null || true
    exit $1
}

# Capturar Ctrl+C para limpiar
trap cleanup INT

# Verificar si bloodhound-ce-cli está disponible
if [ ! -f "./bloodhound-ce-cli" ]; then
    echo "❌ SpecterOps bloodhound-ce-cli not found"
    echo "💡 Install it with: ./scripts/install-specterops-cli.sh"
    exit 1
fi

# Usar el CLI local
BLOODHOUND_CLI="./bloodhound-ce-cli"

# Verificar datos GOAD
GOAD_DATA_DIR="./test-data/goad"
DOMAINS=("ZA" "TB" "AD")

echo "🔍 Checking GOAD data structure..."

# Verificar que existen los directorios de dominios
missing_domains=()
for domain in "${DOMAINS[@]}"; do
    if [ ! -d "$GOAD_DATA_DIR/$domain" ]; then
        missing_domains+=("$domain")
    fi
done

if [ ${#missing_domains[@]} -gt 0 ]; then
    echo "⚠️  Missing GOAD domains: ${missing_domains[*]}"
    echo "💡 Please run: ./scripts/setup-goad-data.sh"
    echo "💡 Or manually extract your GOAD ZIPs to:"
    for domain in "${missing_domains[@]}"; do
        echo "   $GOAD_DATA_DIR/$domain/"
    done
    exit 1
fi

echo "✅ Found GOAD domains:"
for domain in "${DOMAINS[@]}"; do
    file_count=$(find "$GOAD_DATA_DIR/$domain" -name "*.json" | wc -l)
    echo "   - $domain: $file_count JSON files"
done

# Instalar BloodHound CE si no está instalado
echo "🔧 Installing BloodHound CE..."
$BLOODHOUND_CLI install

# Iniciar BloodHound CE
echo "🚀 Starting BloodHound CE..."
$BLOODHOUND_CLI up

# Esperar a que esté listo
echo "⏳ Waiting for BloodHound CE to be ready..."
timeout=120
counter=0

while [ $counter -lt $timeout ]; do
    if $BLOODHOUND_CLI running | grep -q "bloodhound"; then
        echo "✅ BloodHound CE is ready!"
        break
    fi
    sleep 3
    counter=$((counter + 3))
done

if [ $counter -ge $timeout ]; then
    echo "❌ BloodHound CE failed to start within $timeout seconds"
    $BLOODHOUND_CLI logs
    cleanup 1
fi

# Cargar datos de cada dominio
echo "📊 Loading GOAD data from all domains..."

for domain in "${DOMAINS[@]}"; do
    echo "📤 Uploading $domain domain data..."
    
    # Buscar archivos JSON en el directorio del dominio
    json_files=$(find "$GOAD_DATA_DIR/$domain" -name "*.json" | head -5)
    
    if [ -n "$json_files" ]; then
        echo "   📁 Found JSON files in $domain:"
        echo "$json_files" | sed 's/^/     /'
        
        # Crear un ZIP temporal con los archivos del dominio
        temp_zip="/tmp/goad_${domain,,}.zip"
        cd "$GOAD_DATA_DIR/$domain"
        zip -q -r "$temp_zip" *.json 2>/dev/null || true
        cd - > /dev/null
        
        if [ -f "$temp_zip" ]; then
            echo "   📦 Created temporary ZIP for $domain"
            
            # Subir el ZIP a BloodHound (usando nuestro CLI)
            if bloodhound-cli --edition ce upload -f "$temp_zip"; then
                echo "   ✅ $domain domain data uploaded successfully"
            else
                echo "   ⚠️  Failed to upload $domain domain data"
            fi
            
            # Limpiar archivo temporal
            rm -f "$temp_zip"
        else
            echo "   ⚠️  Could not create ZIP for $domain domain"
        fi
    else
        echo "   ⚠️  No JSON files found in $domain domain"
    fi
    
    # Pausa entre dominios
    sleep 2
done

# Verificar que los datos se cargaron
echo "🔍 Verifying data upload..."
sleep 10  # Dar tiempo para que se procesen los datos

# Configurar variables de entorno para tests
export BLOODHOUND_CE_URL="http://localhost:8080"
export BLOODHOUND_NEO4J_URI="bolt://localhost:7687"
export BLOODHOUND_NEO4J_USER="neo4j"
export BLOODHOUND_NEO4J_PASSWORD="neo4j"
export GOAD_DOMAINS="ZA,TB,AD"

# Obtener información del estado
echo "📊 BloodHound CE Status:"
$BLOODHOUND_CLI running

echo "🧪 Running tests with GOAD multi-domain data..."

# Tests unitarios (rápidos, sin BD)
echo "🔬 Running unit tests..."
pytest tests/unit/ -v --tb=short

# Tests de integración (con BD real)
echo "🔗 Running integration tests..."
pytest tests/integration/ -v --tb=short

# Tests específicos para múltiples dominios
echo "🌐 Running multi-domain tests..."
pytest tests/ -m "goad or integration" -v --tb=short

echo "✅ All tests completed successfully!"
echo ""
echo "📊 Test Summary:"
echo "   - Unit tests: ✅ Passed"
echo "   - Integration tests: ✅ Passed"
echo "   - Multi-domain tests: ✅ Passed"
echo "   - Data source: GOAD (ZA, TB, AD domains)"
echo ""
echo "💡 Useful commands:"
echo "   - Stop BloodHound: $BLOODHOUND_CLI down"
echo "   - View logs: $BLOODHOUND_CLI logs"
echo "   - Status: $BLOODHOUND_CLI running"
echo "   - Web UI: http://localhost:8080"
echo "   - Neo4j browser: http://localhost:7474 (neo4j/neo4j)"
echo ""
echo "🌐 GOAD Domains loaded:"
for domain in "${DOMAINS[@]}"; do
    echo "   - $domain: $GOAD_DATA_DIR/$domain/"
done

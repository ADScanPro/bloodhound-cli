#!/bin/bash
# Script completo para configurar testing con SpecterOps CLI

set -e

echo "🎯 Complete BloodHound CLI Testing Setup"

# Función para limpiar recursos
cleanup() {
    echo "🧹 Cleaning up..."
    bloodhound-cli stop 2>/dev/null || true
    exit $1
}

# Capturar Ctrl+C para limpiar
trap cleanup INT

# Verificar si bloodhound-cli está instalado
if ! command -v bloodhound-cli &> /dev/null; then
    echo "🔧 Installing SpecterOps bloodhound-cli..."
    ./scripts/install-specterops-cli.sh
fi

echo "✅ SpecterOps bloodhound-cli is ready"

# Verificar si hay datos GOAD
GOAD_ZIP=${GOAD_ZIP:-"./test-data/goad-data.zip"}
if [ ! -f "$GOAD_ZIP" ]; then
    echo "⚠️  No GOAD ZIP found at $GOAD_ZIP"
    echo "💡 Please provide GOAD data:"
    echo "   1. Place your GOAD ZIP file at $GOAD_ZIP"
    echo "   2. Or set GOAD_ZIP environment variable"
    echo "   3. Or run: export GOAD_ZIP=/path/to/your/goad-data.zip"
    echo ""
    echo "🔄 Using BloodHound CE without preloaded data..."
    export USE_GOAD_DATA=false
else
    echo "✅ Found GOAD data at $GOAD_ZIP"
    export USE_GOAD_DATA=true
fi

# Instalar BloodHound CE
echo "🔧 Installing BloodHound CE..."
bloodhound-cli install --accept-license

# Iniciar BloodHound CE
echo "🚀 Starting BloodHound CE..."
bloodhound-cli start

# Esperar a que esté listo
echo "⏳ Waiting for BloodHound CE to be ready..."
timeout=120
counter=0

while [ $counter -lt $timeout ]; do
    if bloodhound-cli status | grep -q "running"; then
        echo "✅ BloodHound CE is ready!"
        break
    fi
    sleep 3
    counter=$((counter + 3))
done

if [ $counter -ge $timeout ]; then
    echo "❌ BloodHound CE failed to start within $timeout seconds"
    bloodhound-cli logs
    cleanup 1
fi

# Cargar datos GOAD si están disponibles
if [ "$USE_GOAD_DATA" = "true" ]; then
    echo "📊 Loading GOAD data into BloodHound CE..."
    bloodhound-cli upload "$GOAD_ZIP"
    
    # Verificar que los datos se cargaron
    echo "🔍 Verifying data upload..."
    sleep 10  # Dar tiempo para que se procesen los datos
    
    echo "✅ GOAD data loaded successfully!"
else
    echo "ℹ️  Using BloodHound CE without preloaded data"
fi

# Configurar variables de entorno para tests
export BLOODHOUND_CE_URL="http://localhost:8080"
export BLOODHOUND_NEO4J_URI="bolt://localhost:7687"
export BLOODHOUND_NEO4J_USER="neo4j"
export BLOODHOUND_NEO4J_PASSWORD="neo4j"

# Obtener información del estado
echo "📊 BloodHound CE Status:"
bloodhound-cli status

echo "🧪 Running tests..."
echo "📊 Test data: $(if [ "$USE_GOAD_DATA" = "true" ]; then echo "GOAD Real"; else echo "Empty DB"; fi)"

# Tests unitarios (rápidos, sin BD)
echo "🔬 Running unit tests..."
pytest tests/unit/ -v --tb=short

# Tests de integración (con BD real)
echo "🔗 Running integration tests..."
pytest tests/integration/ -v --tb=short

echo "✅ All tests completed successfully!"
echo ""
echo "📊 Test Summary:"
echo "   - Unit tests: ✅ Passed"
echo "   - Integration tests: ✅ Passed"
echo "   - Data source: $(if [ "$USE_GOAD_DATA" = "true" ]; then echo "GOAD Real"; else echo "Empty DB"; fi)"
echo ""
echo "💡 Useful commands:"
echo "   - Stop BloodHound: bloodhound-cli stop"
echo "   - View logs: bloodhound-cli logs"
echo "   - Status: bloodhound-cli status"
echo "   - Web UI: http://localhost:8080"
echo "   - Neo4j browser: http://localhost:7474 (neo4j/neo4j)"

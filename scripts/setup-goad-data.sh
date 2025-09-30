#!/bin/bash
# Script para configurar datos GOAD con tres dominios

set -e

echo "🎯 Setting up GOAD data with three domains"

# Estructura de directorios para GOAD
GOAD_DATA_DIR="./test-data/goad"
DOMAINS=("ZA" "TB" "AD")

# Crear directorio de datos
mkdir -p "$GOAD_DATA_DIR"

echo "📁 GOAD data directory structure:"
echo "   $GOAD_DATA_DIR/"
echo "   ├── ZA/                    # Domain ZA (Zombie Apocalypse)"
echo "   ├── TB/                    # Domain TB (The Big One)"
echo "   └── AD/                    # Domain AD (Attack Domain)"
echo ""

# Verificar si ya existen los ZIPs
echo "🔍 Looking for GOAD ZIP files..."

# Buscar ZIPs con nombres específicos
ZIP_FILES=$(find . -maxdepth 1 -name "goad-*.zip" 2>/dev/null || true)

if [ -z "$ZIP_FILES" ]; then
    echo "⚠️  No GOAD ZIP files found with expected names"
    echo ""
    echo "💡 Please place your GOAD ZIP files in the project root with these names:"
    echo "   - goad-za.zip (Domain ZA - Zombie Apocalypse)"
    echo "   - goad-tb.zip (Domain TB - The Big One)"
    echo "   - goad-ad.zip (Domain AD - Attack Domain)"
    echo ""
    echo "📋 Expected files:"
    echo "   ./goad-za.zip"
    echo "   ./goad-tb.zip"
    echo "   ./goad-ad.zip"
    echo ""
    echo "🔄 You can also set environment variables:"
    echo "   export GOAD_ZA_ZIP=/path/to/goad-za.zip"
    echo "   export GOAD_TB_ZIP=/path/to/goad-tb.zip"
    echo "   export GOAD_AD_ZIP=/path/to/goad-ad.zip"
    exit 1
fi

echo "✅ Found GOAD ZIP files:"
echo "$ZIP_FILES"
echo ""

# Función para procesar cada dominio
process_domain() {
    local domain=$1
    local zip_file=$2
    
    echo "📦 Processing $domain domain..."
    
    # Crear directorio del dominio
    domain_dir="$GOAD_DATA_DIR/$domain"
    mkdir -p "$domain_dir"
    
    # Extraer ZIP al directorio del dominio
    echo "   📥 Extracting $zip_file to $domain_dir..."
    if unzip -q "$zip_file" -d "$domain_dir"; then
        echo "   ✅ $domain domain extracted successfully"
        
        # Verificar que se extrajeron archivos
        file_count=$(find "$domain_dir" -name "*.json" | wc -l)
        echo "   📊 Found $file_count JSON files in $domain"
        
        # Mostrar estructura
        echo "   📁 $domain domain structure:"
        find "$domain_dir" -maxdepth 2 -type f -name "*.json" | head -5 | sed 's/^/     /'
        if [ $file_count -gt 5 ]; then
            echo "     ... and $((file_count - 5)) more files"
        fi
    else
        echo "   ❌ Failed to extract $zip_file"
        return 1
    fi
}

# Procesar cada dominio
echo "🔄 Processing GOAD domains..."

# Buscar ZIPs específicos por dominio
for domain in "${DOMAINS[@]}"; do
    # Buscar ZIP con nombre específico
    domain_zip="goad-${domain,,}.zip"
    
    if [ -f "$domain_zip" ]; then
        process_domain "$domain" "$domain_zip"
    else
        echo "⚠️  No ZIP file found for $domain domain"
        echo "   Looking for: $domain_zip"
    fi
done

# Verificar estructura final
echo ""
echo "📊 Final GOAD data structure:"
tree "$GOAD_DATA_DIR" 2>/dev/null || find "$GOAD_DATA_DIR" -type f | head -10

echo ""
echo "✅ GOAD data setup completed!"
echo ""
echo "💡 Next steps:"
echo "   1. Run tests: ./scripts/setup-complete.sh"
echo "   2. Or start BloodHound: bloodhound-cli install && bloodhound-cli start"
echo "   3. Upload data: bloodhound-cli upload $GOAD_DATA_DIR/ZA/ (for each domain)"
echo ""
echo "📁 Data locations:"
echo "   - ZA domain: $GOAD_DATA_DIR/ZA/"
echo "   - TB domain: $GOAD_DATA_DIR/TB/"
echo "   - AD domain: $GOAD_DATA_DIR/AD/"

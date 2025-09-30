#!/bin/bash
# Script para instalar bloodhound-cli oficial de SpecterOps

set -e

echo "🔧 Installing SpecterOps bloodhound-cli..."

# Variables de configuración
INSTALL_DIR=${INSTALL_DIR:-"/usr/local/bin"}
BLOODHOUND_CLI_URL="https://github.com/SpecterOps/bloodhound-cli/releases/latest/download/bloodhound-cli-linux-amd64.tar.gz"
TEMP_DIR=$(mktemp -d)

# Función para limpiar recursos
cleanup() {
    echo "🧹 Cleaning up temporary files..."
    rm -rf "$TEMP_DIR"
    exit $1
}

# Capturar Ctrl+C para limpiar
trap cleanup INT

# Verificar si ya está instalado
if command -v bloodhound-cli &> /dev/null; then
    echo "✅ bloodhound-cli is already installed"
    bloodhound-cli version
    exit 0
fi

# Verificar dependencias
echo "🔍 Checking dependencies..."

# Verificar curl
if ! command -v curl &> /dev/null; then
    echo "❌ curl is required but not installed"
    echo "💡 Install with: sudo apt-get install curl"
    exit 1
fi

# Verificar tar
if ! command -v tar &> /dev/null; then
    echo "❌ tar is required but not installed"
    echo "💡 Install with: sudo apt-get install tar"
    exit 1
fi

echo "✅ Dependencies check passed"

# Descargar el binario
echo "📥 Downloading bloodhound-cli from SpecterOps..."
cd "$TEMP_DIR"

if ! curl -L -o bloodhound-cli.tar.gz "$BLOODHOUND_CLI_URL"; then
    echo "❌ Failed to download bloodhound-cli"
    cleanup 1
fi

echo "✅ Download completed"

# Extraer el archivo
echo "📦 Extracting bloodhound-cli..."
if ! tar -xzf bloodhound-cli.tar.gz; then
    echo "❌ Failed to extract bloodhound-cli"
    cleanup 1
fi

echo "✅ Extraction completed"

# Verificar que el binario existe
if [ ! -f "bloodhound-cli" ]; then
    echo "❌ bloodhound-cli binary not found in archive"
    cleanup 1
fi

# Hacer el binario ejecutable
chmod +x bloodhound-cli

# Instalar en el directorio del sistema
echo "📁 Installing bloodhound-cli to $INSTALL_DIR..."

# Verificar permisos de escritura
if [ ! -w "$INSTALL_DIR" ]; then
    echo "🔐 Need sudo permissions to install to $INSTALL_DIR"
    if ! sudo cp bloodhound-cli "$INSTALL_DIR/"; then
        echo "❌ Failed to install bloodhound-cli to $INSTALL_DIR"
        cleanup 1
    fi
else
    if ! cp bloodhound-cli "$INSTALL_DIR/"; then
        echo "❌ Failed to install bloodhound-cli to $INSTALL_DIR"
        cleanup 1
    fi
fi

echo "✅ bloodhound-cli installed successfully"

# Verificar la instalación
if command -v bloodhound-cli &> /dev/null; then
    echo "🎉 Installation successful!"
    bloodhound-cli version
else
    echo "❌ Installation failed - bloodhound-cli not found in PATH"
    echo "💡 Try adding $INSTALL_DIR to your PATH"
    echo "💡 Or run: export PATH=\$PATH:$INSTALL_DIR"
    cleanup 1
fi

# Limpiar archivos temporales
cleanup 0

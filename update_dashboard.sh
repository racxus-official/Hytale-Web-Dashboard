#!/bin/bash
# Script para atualizar o Hytale Web Dashboard

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Atualizando Hytale Web Dashboard ==="
echo "Data: $(date)"
echo ""

# Para o dashboard se estiver rodando
if [ -f "stop-dashboard.sh" ]; then
    ./stop-dashboard.sh
    sleep 2
fi

# Backup da configuração
if [ -f "config.json" ]; then
    echo "💾 Fazendo backup da configuração..."
    cp config.json config.json.backup.$(date +%Y%m%d_%H%M%S)
fi

# Atualiza dependências
if [ -f "requirements.txt" ]; then
    echo "📦 Atualizando dependências Python..."
    source venv/bin/activate
    pip install --upgrade -r requirements.txt
fi

# Atualiza scripts
echo "🔄 Atualizando scripts..."
# Aqui você pode adicionar comandos para baixar atualizações
# Ex: git pull, wget de arquivos atualizados, etc.

echo "✅ Atualização completa!"
echo ""
echo "Para iniciar o dashboard:"
echo "./start-dashboard.sh"
echo ""
echo "Para acessar: http://seu-ip:5000"
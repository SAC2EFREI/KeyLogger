#!/bin/bash
echo "🚀 Démarrage du système complet de surveillance..."

# Nettoyage
echo "🧹 Nettoyage des processus existants..."
pkill -f "python3 receiver_server" 2>/dev/null
pkill -f "streamlit" 2>/dev/null
sudo fuser -k 8888/tcp 2>/dev/null
sleep 2

# Vérifier l'environnement Streamlit
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "📦 Activation de l'environnement virtuel streamlit_env..."
    source ~/streamlit_env/bin/activate
    # Si streamlit n'est pas installé, l'installer
    pip install streamlit pandas plotly cryptography requests psutil
fi

# Démarrer le serveur amélioré
echo "🔧 Démarrage du serveur de réception amélioré..."
python3 receiver.py &
SERVER_PID=$!
sleep 3

# Vérifier le serveur
if netstat -tulpn 2>/dev/null | grep 8888 > /dev/null; then
    echo "✅ Serveur en écoute sur le port 8888"
else
    echo "❌ Le serveur n'a pas pu démarrer"
    exit 1
fi

# Démarrer l'interface temps réel
echo "🌐 Démarrage du dashboard temps réel..."
echo "📢 Ouvrez http://localhost:8501 dans votre navigateur"
# Utiliser l'environnement virtuel streamlit_env
source ~/streamlit_env/bin/activate
streamlit run streamlit_interface.py
# Nettoyage
echo "⏹ Arrêt du système..."
kill $SERVER_PID 2>/dev/null
pkill -f "python3 receiver_server" 2>/dev/null
echo "✅ Système arrêté"
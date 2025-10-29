#!/bin/bash

echo "================================================"
echo "FIRMA CHATBOT - KURULUM"
echo "================================================"
echo ""
echo "Python paketleri yükleniyor..."
echo ""

pip3 install flask flask-cors bcrypt --quiet

if [ $? -eq 0 ]; then
    echo ""
    echo "[BAŞARILI] Tüm paketler yüklendi!"
    echo ""
    echo "Şimdi veritabanını oluşturmak için ./setup_database.sh çalıştırın"
    echo ""
else
    echo ""
    echo "[HATA] Paket yüklemede hata oluştu!"
    echo "Python3 yüklü olduğundan emin olun."
    echo ""
fi

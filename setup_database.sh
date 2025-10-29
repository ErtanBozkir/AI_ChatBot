#!/bin/bash

echo "================================================"
echo "VERİTABANI OLUŞTURULUYOR"
echo "================================================"
echo ""

python3 test_setup.py

if [ $? -eq 0 ]; then
    echo ""
    echo "[BAŞARILI] Veritabanı hazır!"
    echo ""
    echo "Test kullanıcısı: ahmet.yilmaz"
    echo "Şifre: 12345"
    echo ""
    echo "Şimdi ./start.sh ile sunucuyu başlatın!"
    echo ""
else
    echo ""
    echo "[HATA] Veritabanı oluşturulamadı!"
    echo ""
fi

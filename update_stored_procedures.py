#!/usr/bin/env python3
"""
Stored Procedure'ları SQL Server'a yükler
"""
import sys
sys.path.append('/Users/ertanbozkir/Documents/GitHub/AI_ChatBot/backend')

from database import DatabaseManager
import os

db = DatabaseManager()

print("=" * 60)
print("STORED PROCEDURE GÜNCELLEME")
print("=" * 60)

# Stored procedure dosyaları
sp_files = [
    '/Users/ertanbozkir/Documents/GitHub/AI_ChatBot/database/SP_KullaniciGiris.sql',
    '/Users/ertanbozkir/Documents/GitHub/AI_ChatBot/database/SP_SoruCevap.sql',
    '/Users/ertanbozkir/Documents/GitHub/AI_ChatBot/database/SP_SohbetGecmisiGetir.sql'
]

for sp_file in sp_files:
    sp_name = os.path.basename(sp_file)
    print(f"\n📄 {sp_name} yükleniyor...")

    try:
        with open(sp_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # SQL'i çalıştır
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # GO komutlarını ayır ve her birini ayrı çalıştır
            batches = sql_content.split('GO')
            for batch in batches:
                batch = batch.strip()
                if batch:
                    cursor.execute(batch)

            conn.commit()

        print(f"   ✅ {sp_name} başarıyla yüklendi!")

    except Exception as e:
        print(f"   ❌ HATA: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
print("İŞLEM TAMAMLANDI")
print("=" * 60)

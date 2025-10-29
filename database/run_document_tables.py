"""
Doküman tablolarını oluşturan script
"""

import sys
import os
import pyodbc

# Backend klasörünü path'e ekle
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from config import Config

def run_sql_script(sql_file_path):
    """SQL script dosyasını çalıştırır"""
    print(f"SQL Script çalıştırılıyor: {sql_file_path}")

    try:
        # SQL dosyasını oku
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_script = file.read()

        # Database adını değiştir
        sql_script = sql_script.replace('USE TESTDB;', f'USE {Config.DB_NAME};')

        # Connection string
        config = Config()
        conn_str = config.get_connection_string

        # Bağlantı kur
        print(f"Veritabanına bağlanılıyor: {Config.DB_SERVER}/{Config.DB_NAME}")
        conn = pyodbc.connect(conn_str)
        conn.autocommit = True
        cursor = conn.cursor()

        # Script'i GO ile böl ve tek tek çalıştır
        commands = sql_script.split('GO')

        for i, command in enumerate(commands, 1):
            command = command.strip()
            if command:
                try:
                    cursor.execute(command)
                    print(f"✓ Komut {i}/{len(commands)} başarılı")
                except Exception as e:
                    print(f"✗ Komut {i} hatası: {str(e)}")

        cursor.close()
        conn.close()

        print("\n✓ SQL script başarıyla çalıştırıldı!")
        return True

    except Exception as e:
        print(f"\n✗ Hata: {str(e)}")
        return False

if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    sql_file = os.path.join(script_dir, '03_create_document_tables.sql')

    print("=" * 60)
    print("DOKÜMAN TABLOLARI OLUŞTURMA")
    print("=" * 60)

    if run_sql_script(sql_file):
        print("\n✓ Tüm tablolar başarıyla oluşturuldu!")
    else:
        print("\n✗ Tablolar oluşturulurken hata oluştu!")
        sys.exit(1)

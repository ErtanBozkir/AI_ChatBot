@echo off
echo ================================================
echo VERITABANI OLUSTURULUYOR
echo ================================================
echo.

python test_setup.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [BASARILI] Veritabani hazir!
    echo.
    echo Test kullanicisi: ahmet.yilmaz
    echo Sifre: 12345
    echo.
    echo Simdi start.bat ile sunucuyu baslatin!
    echo.
) else (
    echo.
    echo [HATA] Veritabani olusturulamadi!
    echo.
)

pause

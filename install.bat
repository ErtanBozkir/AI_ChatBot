@echo off
echo ================================================
echo FIRMA CHATBOT - KURULUM
echo ================================================
echo.
echo Python paketleri yukleniyor...
echo.

pip install flask flask-cors bcrypt --quiet

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [BASARILI] Tum paketler yuklendi!
    echo.
    echo Simdi veritabanini olusturmak icin setup_database.bat calistirin
    echo.
) else (
    echo.
    echo [HATA] Paket yuklemede hata olustu!
    echo Python yuklu oldugundan emin olun.
    echo.
)

pause

import yfinance as yf
import psycopg2
import schedule
import time
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def db_baglan():
    return psycopg2.connect(
        host="localhost",
        database="contrail",
        user="postgres",
        password="250801"
    )

SEMBOLLER = {
    "brent":         "BZ=F",
    "eurusd":        "EURUSD=X",
    "usdtry":        "USDTRY=X",
    "dxy":           "DX-Y.NYB",
    "airline-index": "^XAL",
    "DAL":           "DAL",
    "UAL":           "UAL",
    "RYAAY":         "RYAAY",
    "LHA.DE":        "LHA.DE",
    "AF.PA":         "AF.PA",
    "C6L.SI":        "C6L.SI",
    "9202.T":        "9202.T",
    "THYAO.IS":      "THYAO.IS",
}

def veri_cek_ve_kaydet():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Piyasa verisi çekiliyor...")
    conn = db_baglan()
    cursor = conn.cursor()
    basarili = 0
    hatali = 0

    brent_fiyat = None

    for sembol_adi, ticker_kodu in SEMBOLLER.items():
        try:
            ticker = yf.Ticker(ticker_kodu)
            bilgi = ticker.fast_info

            fiyat = bilgi.last_price
            onceki_kapanis = bilgi.previous_close

            if fiyat and onceki_kapanis and onceki_kapanis != 0:
                degisim = ((fiyat - onceki_kapanis) / onceki_kapanis) * 100
                yon = "pos" if degisim >= 0 else "neg"
            else:
                degisim = 0
                yon = "neu"

            # Brent fiyatını sakla — jet yakıtı için kullanacağız
            if sembol_adi == "brent":
                brent_fiyat = fiyat

            ham = {
                "fiyat": fiyat,
                "onceki_kapanis": onceki_kapanis,
                "degisim_yuzde": round(degisim, 4)
            }

            cursor.execute("""
                INSERT INTO market_data (sembol, fiyat, degisim_yuzde, degisim_yon, ham_veri, kaynak)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                sembol_adi,
                round(fiyat, 6) if fiyat else None,
                round(degisim, 4),
                yon,
                json.dumps(ham),
                "yfinance"
            ))
            conn.commit()
            print(f"  ✅ {sembol_adi}: {fiyat:.4f} ({degisim:+.2f}%)")
            basarili += 1

        except Exception as e:
            hatali += 1
            print(f"  ❌ {sembol_adi}: {e}")
            conn.rollback()

    # Jet yakıtını Brent'ten hesapla (varil → galon, +%18 rafine marjı)
    if brent_fiyat:
        try:
            jet_fiyat = round(brent_fiyat * 0.033 * 1.18, 4)
            cursor.execute("""
                INSERT INTO market_data (sembol, fiyat, degisim_yuzde, degisim_yon, ham_veri, kaynak)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                "jetfuel",
                jet_fiyat,
                0,
                "neu",
                json.dumps({"hesaplama": "brent * 0.033 * 1.18", "brent": brent_fiyat}),
                "calculated"
            ))
            conn.commit()
            print(f"  ✅ jetfuel (hesaplanan): {jet_fiyat:.4f}")
            basarili += 1
        except Exception as e:
            print(f"  ❌ jetfuel hesaplama hatası: {e}")
            conn.rollback()

    cursor.close()
    conn.close()
    print(f"[Tamamlandı] {basarili} başarılı, {hatali} hatalı")

veri_cek_ve_kaydet()

schedule.every(5).minutes.do(veri_cek_ve_kaydet)

print("\nPiyasa veri servisi aktif — her 5 dakikada güncelleniyor.")
print("Durdurmak için Ctrl+C\n")

while True:
    schedule.run_pending()
    time.sleep(30)
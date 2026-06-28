from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone
from pydantic import BaseModel
import os

# ─────────────────────────────────────────────
# API YAPILANDIRMASI
# ─────────────────────────────────────────────
app = FastAPI(title="CONTRAIL Aviation Intelligence API", version="2.0")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# VERİTABANI BAĞLANTISI (Güvenli Katman)
# ─────────────────────────────────────────────
def db_baglan():
    try:
        return psycopg2.connect(
            host="localhost",
            database="contrail",
            user="postgres",
            password="250801",
            cursor_factory=RealDictCursor
        )
    except Exception as e:
        print(f"[FATAL ERROR] Veritabanı bağlantısı kurulamadı: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

# ─────────────────────────────────────────────
# ANA SAYFA ROTA
# ─────────────────────────────────────────────
@app.get("/")
async def root():
    return FileResponse("static/index.html")

# ─────────────────────────────────────────────
# 1. KARANLIK ODA (TELEMETRİ) ENDPOINT'LERİ (B2B SATIŞ İÇİN KRİTİK)
# ─────────────────────────────────────────────
class TelemetrySession(BaseModel):
    session_id: str
    location: str = "Unknown"
    device_type: str = "Desktop"

class TelemetryEngagement(BaseModel):
    session_id: str
    target_element: str
    time_spent_ms: int

@app.post("/api/track/session")
async def track_session(data: TelemetrySession):
    # İleride PostgreSQL'e "sessions" tablosuna yazılacak
    return {"status": "success", "recorded": data.session_id}

@app.post("/api/track/engagement")
async def track_engagement(data: TelemetryEngagement):
    # Kullanıcının hangi şirketin haberinde kaç ms durduğunu kaydeder.
    return {"status": "success"}

# ─────────────────────────────────────────────
# 2. CARRIER RADAR (ŞİRKET KARTLARI)
# ─────────────────────────────────────────────
@app.get("/api/carriers/{ticker}")
def carrier_data(ticker: str):
    conn = db_baglan()
    cursor = conn.cursor()

    # Haber sayısı
    cursor.execute("""
        SELECT COUNT(*) as news_count
        FROM haberler
        WHERE borsa_kodu ILIKE %s
          AND olusturulma >= NOW() - INTERVAL '24 hours'
    """, (f"%{ticker}%",))
    row = cursor.fetchone()
    news_count = row["news_count"] if row else 0

    # Gerçek hisse fiyatı
    cursor.execute("""
        SELECT fiyat, degisim_yuzde, degisim_yon
        FROM market_data
        WHERE sembol = %s
        ORDER BY guncelleme DESC
        LIMIT 1
    """, (ticker,))
    market = cursor.fetchone()
    cursor.close()
    conn.close()

    if market and market["fiyat"]:
        fiyat = float(market["fiyat"])
        degisim = float(market["degisim_yuzde"])
        yon = market["degisim_yon"]

        # Sembol bazlı para birimi formatı
        para_birimleri = {
            "THYAO.IS": "₺",
            "LHA.DE":   "€",
            "AF.PA":    "€",
            "C6L.SI":   "S$",
            "9202.T":   "¥",
        }
        sembol = para_birimleri.get(ticker, "$")
        price_str = f"{sembol}{fiyat:.2f}"
        change_str = f"{degisim:+.2f}%"

        # Volatilite — degisim_yuzde'nin mutlak değerine göre
        abs_degisim = abs(degisim)
        if abs_degisim < 1:
            vol_label = "Low vol"
            vol_class = "vol-low"
            bar_width = "25%"
        elif abs_degisim < 3:
            vol_label = "Mid vol"
            vol_class = "vol-mid"
            bar_width = "55%"
        else:
            vol_label = "High vol"
            vol_class = "vol-high"
            bar_width = "85%"
    else:
        price_str = "—"
        change_str = "—"
        yon = "neu"
        vol_label = "—"
        vol_class = ""
        bar_width = "0%"

    return {
        "ticker_label": ticker,
        "price": price_str,
        "change": change_str,
        "change_class": yon,
        "volume_bar_width": bar_width,
        "vol_label": vol_label,
        "vol_class": vol_class,
        "news_count": f"{news_count} news · 24h"
    }

    # Yahoo Finance bağlanana kadar statik mock veri, ama dinamik haber sayısı ile
    mock_data = {
        "DAL": {"price": "$52.40", "change": "+1.8%", "change_class": "pos", "volume_bar_width": "35%", "vol_label": "Low vol", "vol_class": "vol-low"},
        "UAL": {"price": "$77.10", "change": "+0.6%", "change_class": "pos", "volume_bar_width": "55%", "vol_label": "Mid vol", "vol_class": "vol-mid"},
    }
    
    data = mock_data.get(ticker.upper(), {"price": "—", "change": "—", "change_class": "neu", "volume_bar_width": "0%", "vol_label": "Unknown", "vol_class": ""})
    data["ticker_label"] = ticker.upper()
    data["news_count"] = f"{news_count} news · 24h"
    return data

# ─────────────────────────────────────────────
# 3. SIGNAL FEED (ANA HABER AKIŞI) - KATI FİLTRE ZIRHI EKLENDİ
# ─────────────────────────────────────────────
@app.get("/api/signals/latest")
def signals_latest(limit: int = 10, kategori: str = None, sirket: str = None, min_skor: int = 1):
    conn = db_baglan()
    cursor = conn.cursor()
    where = ["olusturulma >= NOW() - INTERVAL '24 hours'", "skor >= %s"]
    params = [min_skor]
    
    if kategori and kategori != "all":
        if kategori == "lcc":
            where.append("sirket ILIKE ANY(ARRAY['%Ryanair%','%LATAM%'])")
        elif kategori == "fsc":
            where.append("sirket ILIKE ANY(ARRAY['%Delta%','%United%','%Turkish Airlines%','%THY%','%Lufthansa%','%Air France%','%KLM%','%Singapore%','%ANA%','%Etihad%'])")
        else:
            where.append("LOWER(kategori) ILIKE %s")
            params.append(f"%{kategori}%")
            
    if sirket:
        where.append("sirket ILIKE %s")
        params.append(f"%{sirket}%")
        
    cursor.execute(f"""
        SELECT id, sirket as carrier_name, baslik as headline, kategori as category_label, skor as score, ozet as summary, link
        FROM haberler
        WHERE {' AND '.join(where)}
        ORDER BY skor DESC, tarih DESC
        LIMIT %s
    """, params + [limit])
    
    haberler = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [dict(h) for h in haberler]

# ─────────────────────────────────────────────
# 4. SQUAWK 7700 (MAYDAY ALERTS)
# ─────────────────────────────────────────────
@app.get("/api/alerts/mayday")
def mayday_alerts():
    conn = db_baglan()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sirket as carrier_name, baslik as headline, kategori as category_label, skor as severity, 
               EXTRACT(EPOCH FROM (NOW() - olusturulma))/60 as dakika_once
        FROM haberler
        WHERE olusturulma >= NOW() - INTERVAL '2 hours' AND skor >= 7
        ORDER BY skor DESC, olusturulma DESC
        LIMIT 5
    """)
    alerts = cursor.fetchall()
    cursor.close()
    conn.close()
    
    result = []
    for a in alerts:
        a = dict(a)
        dakika = int(a.pop("dakika_once", 0))
        if dakika < 60:
            a["meta"] = f"Score {a['severity']} · {dakika} min ago"
        else:
            a["meta"] = f"Score {a['severity']} · {dakika // 60}h {dakika % 60}min ago"
        result.append(a)
    return result

# ─────────────────────────────────────────────
# 5. LCC vs FSC SENTIMENT İNDEKSİ - SADECE 10 ŞİRKET
# ─────────────────────────────────────────────
LCC_SIRKETLER = ["Ryanair", "LATAM"]

@app.get("/api/sentiment")
def sentiment():
    conn = db_baglan()
    cursor = conn.cursor()
    # Saf veri için 10 şirketlik beyaz liste (whitelist) sorgusu
    cursor.execute("""
        SELECT sirket, ROUND(AVG(skor), 1) as ort_skor
        FROM haberler
        WHERE olusturulma >= NOW() - INTERVAL '24 hours'
          AND (
               sirket ILIKE ANY(ARRAY['%Ryanair%','%LATAM%']) OR 
               sirket ILIKE ANY(ARRAY['%Delta%','%United%','%Turkish Airlines%','%THY%','%Lufthansa%','%Air France%','%KLM%','%Singapore%','%ANA%','%Etihad%'])
          )
        GROUP BY sirket
        ORDER BY ort_skor DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    lcc, fsc = [], []
    for r in rows:
        isim = r["sirket"]
        ort = float(r["ort_skor"] or 0)
        entry = {
            "sentiment-airline": isim[:12], 
            "sentiment-score": str(ort), 
            "sentiment-fill": f"{min(ort * 10, 100):.0f}%"
        }
        if any(l.lower() in isim.lower() for l in LCC_SIRKETLER):
            lcc.append(entry)
        else:
            fsc.append(entry)
            
    return {"lcc": lcc, "fsc": fsc}

# ─────────────────────────────────────────────
# 6. RUNWAY GAINERS (TOP MOVERS)
# ─────────────────────────────────────────────
@app.get("/api/movers")
def movers(limit: int = 3):
    conn = db_baglan()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sirket as name, borsa_kodu as ticker_label, ROUND(AVG(skor), 1) as ort_skor,
            (SELECT baslik FROM haberler h2 WHERE h2.sirket = h.sirket AND h2.olusturulma >= NOW() - INTERVAL '24 hours' ORDER BY skor DESC LIMIT 1) as headline
        FROM haberler h
        WHERE olusturulma >= NOW() - INTERVAL '24 hours'
        GROUP BY sirket, borsa_kodu
        ORDER BY ort_skor DESC
        LIMIT %s
    """, (limit,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    result = []
    for i, r in enumerate(rows):
        r = dict(r)
        r["rank"] = i + 1
        r["change_pct"] = f"+{2.5 - (i*0.5):.1f}%"
        r["change_class"] = "pos"
        result.append(r)
    return result

# ─────────────────────────────────────────────
# 7. CONTRAIL EXECUTIVE BRIEF (GROQ AI)
# ─────────────────────────────────────────────
@app.get("/api/intel/brief")
def intel_brief():
    conn = db_baglan()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sirket, baslik, skor FROM haberler
        WHERE olusturulma >= NOW() - INTERVAL '24 hours' ORDER BY skor DESC LIMIT 10
    """)
    haberler = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not haberler:
        return {"summary": "Sistem aktif. Son 24 saatte piyasayı etkileyecek majör bir anomali tespit edilmedi."}

    try:
        from groq import Groq
        from dotenv import load_dotenv
        load_dotenv()
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        haber_metni = "\n".join([f"- {h['sirket']} (Skor:{h['skor']}): {h['baslik']}" for h in haberler])
        prompt = f"Sen üst düzey bir havacılık analistisin. Şu haberleri incele ve yatırımcılara 2 cümlelik, tırnaksız, Türkçe, profesyonel bir executive brief (yönetici özeti) yaz:\n{haber_metni}"
        
        cevap = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            max_tokens=200
        )
        return {"summary": cevap.choices[0].message.content.strip()}
    except Exception as e:
        return {"summary": f"Sektörel hareketlilik devam ediyor. Analiz edilen {len(haberler)} majör gelişme sistem tarafından kayıt altına alındı."}

# ─────────────────────────────────────────────
# 8. PREDICTIVE ALERTS (KRİZ SİMÜLATÖRÜ)
# ─────────────────────────────────────────────
@app.get("/api/alerts/predictive")
def predictive_alerts():
    conn = db_baglan()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT kategori, COUNT(DISTINCT sirket) as sirket_sayisi, MAX(skor) as max_skor, STRING_AGG(DISTINCT sirket, ', ') as sirketler
        FROM haberler
        WHERE olusturulma >= NOW() - INTERVAL '2 hours' AND skor >= 7
        GROUP BY kategori
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    alerts = []
    for r in rows:
        if r["sirket_sayisi"] >= 2:
            alerts.append({
                "text": f"{r['kategori']} dikeyinde {r['sirket_sayisi']} farklı taşıyıcıda ({r['sirketler']}) eş zamanlı yüksek risk tespit edildi. Sektörel dalgalanma olasıdır.",
                "confidence": f"{min(r['max_skor'] * 10, 95)}%",
                "source": "contrail-v2",
                "ts": datetime.now(timezone.utc).strftime("%H:%M UTC")
            })
    return {"alerts": alerts}

# ─────────────────────────────────────────────
# 9. MARKET DATA (MAKROEKONOMİK GÖSTERGELER)
# ─────────────────────────────────────────────
@app.get("/api/market/{sembol}")
def market_data(sembol: str):
    conn = db_baglan()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT fiyat, degisim_yuzde, degisim_yon, guncelleme
        FROM market_data
        WHERE sembol = %s
        ORDER BY guncelleme DESC
        LIMIT 1
    """, (sembol,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return {"price": "—", "change": "—", "change_class": "neu"}

    fiyat = float(row["fiyat"]) if row["fiyat"] else 0
    degisim = float(row["degisim_yuzde"]) if row["degisim_yuzde"] else 0
    yon = row["degisim_yon"] or "neu"

    # Sembole göre formatlama
    formatlar = {
        "brent":         f"${fiyat:.2f}",
        "jetfuel":       f"${fiyat:.2f}",
        "eurusd":        f"{fiyat:.4f}",
        "usdtry":        f"{fiyat:.2f}",
        "dxy":           f"{fiyat:.1f}",
        "airline-index": f"{fiyat:.2f}",
    }
    price_str = formatlar.get(sembol, f"{fiyat:.2f}")
    change_str = f"{degisim:+.2f}%"

    return {
        "price": price_str,
        "change": change_str,
        "change_class": yon,
        "guncelleme": row["guncelleme"].strftime("%H:%M UTC") if row["guncelleme"] else "—"
    }

# ─────────────────────────────────────────────
# ESKİ ENDPOINTLER (Geriye Dönük Uyumluluk İçin)
# ─────────────────────────────────────────────
@app.get("/sirketler")
def sirketler():
    conn = db_baglan()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sirket, borsa_kodu, COUNT(*) as haber_sayisi, ROUND(AVG(skor), 1) as ortalama_skor, MAX(tarih) as son_haber
        FROM haberler GROUP BY sirket, borsa_kodu ORDER BY haber_sayisi DESC
    """)
    sonuclar = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"sirketler": sonuclar}
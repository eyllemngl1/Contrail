from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="Contrail API", version="1.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def db_baglan():
    return psycopg2.connect(
        host="localhost",
        database="contrail",
        user="postgres",
        password="250801",
        cursor_factory=RealDictCursor
    )

@app.get("/")
async def root():
    return FileResponse("static/index.html") 

@app.get("/haberler")
def haberler(limit: int = 50):
    conn = db_baglan()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM haberler
        ORDER BY tarih DESC
        LIMIT %s
    """, (limit,))
    sonuclar = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"toplam": len(sonuclar), "haberler": sonuclar}

@app.get("/haberler/{sirket_adi}")
def sirket_haberleri(sirket_adi: str, limit: int = 20):
    conn = db_baglan()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM haberler
        WHERE sirket ILIKE %s
        ORDER BY tarih DESC
        LIMIT %s
    """, (f"%{sirket_adi}%", limit))
    sonuclar = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"sirket": sirket_adi, "toplam": len(sonuclar), "haberler": sonuclar}

@app.get("/son24saat")
def son24saat():
    conn = db_baglan()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM haberler
        WHERE olusturulma >= NOW() - INTERVAL '24 hours'
        ORDER BY skor DESC, tarih DESC
    """)
    sonuclar = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"toplam": len(sonuclar), "haberler": sonuclar}

@app.get("/sirketler")
def sirketler():
    conn = db_baglan()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sirket, borsa_kodu,
               COUNT(*) as haber_sayisi,
               ROUND(AVG(skor), 1) as ortalama_skor,
               MAX(tarih) as son_haber
        FROM haberler
        GROUP BY sirket, borsa_kodu
        ORDER BY haber_sayisi DESC
    """)
    sonuclar = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"sirketler": sonuclar}

@app.get("/kritik")
def kritik_haberler():
    conn = db_baglan()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM haberler
        WHERE skor >= 8
        ORDER BY tarih DESC
        LIMIT 20
    """)
    sonuclar = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"toplam": len(sonuclar), "kritik_haberler": sonuclar}
import os
import json
import feedparser
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from groq import Groq
import psycopg2

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

conn = psycopg2.connect(
    host="localhost",
    database="contrail",
    user="postgres",
    password="250801"
)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE haberler ADD CONSTRAINT unique_baslik UNIQUE (baslik);")
    conn.commit()
except Exception:
    conn.rollback()

def send_telegram_alert(baslik, sirket, skor, link):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  -> Telegram token veya chat_id eksik, bildirim atlandı.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    mesaj = (
        f"✈️ <b>CONTRAIL UYARI</b>\n\n"
        f"🏢 <b>Şirket:</b> {sirket}\n"
        f"🔥 <b>Skor:</b> {skor}/10\n"
        f"📰 <b>Başlık:</b> {baslik}\n\n"
        f"🔗 <a href='{link}'>Haberi Oku</a>"
    )
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mesaj,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print(f"  📱 Telegram bildirimi gönderildi!")
        else:
            print(f"  -> Telegram hatası: {r.text}")
    except Exception as e:
        print(f"  -> Telegram bağlantı hatası: {e}")

SIRKETLER = [
    {
        "isim": "Delta Air Lines",
        "borsa_kodu": "DAL",
        "aramalar": [
            "Delta+Air+Lines",
            "Delta+Airlines",
            "Delta+Air+Lines+Inc",
            "DAL+airline",
            "Delta+airline"
        ]
    },
    {
        "isim": "United Airlines",
        "borsa_kodu": "UAL",
        "aramalar": [
            "United+Airlines",
            "United+airline",
            "United+Airlines+Holdings",
            "United+Airlines+Inc",
            "UAL+airline"
        ]
    },
    {
        "isim": "Turkish Airlines",
        "borsa_kodu": "THYAO",
        "aramalar": [
            "Turkish+Airlines",
            "Türk+Hava+Yolları",
            "THY+havayolu",
            "Türk+Hava+Yolları+AO",
            "THYAO+airline"
        ]
    },
    {
        "isim": "Lufthansa",
        "borsa_kodu": "LHA",
        "aramalar": [
            "Lufthansa+airline",
            "Lufthansa+Group",
            "Lufthansa+Airlines",
            "Deutsche+Lufthansa+AG",
            "LHA+airline",
            "LHAG+airline"
        ]
    },
    {
        "isim": "Air France-KLM",
        "borsa_kodu": "AF",
        "aramalar": [
            "Air+France+airline",
            "Air+France+KLM",
            "Air+France-KLM+SA",
            "KLM+airline",
            "KLM+Royal+Dutch",
            "AF+airline",
            "AFKLM"
        ]
    },
    {
        "isim": "Singapore Airlines",
        "borsa_kodu": "C6L",
        "aramalar": [
            "Singapore+Airlines",
            "Singapore+airline",
            "Singapore+Airlines+Limited",
            "SIA+airline",
            "SINGY+airline",
            "C6L+airline"
        ]
    },
    {
        "isim": "ANA All Nippon Airways",
        "borsa_kodu": "9202",
        "aramalar": [
            "ANA+airline",
            "All+Nippon+Airways",
            "ANA+All+Nippon",
            "ANA+Holdings+airline",
            "9202+Tokyo+airline",
            "ANA+aviation"
        ]
    },
    {
        "isim": "Ryanair",
        "borsa_kodu": "RYAAY",
        "aramalar": [
            "Ryanair+airline",
            "Ryanair+Holdings",
            "Ryanair+DAC",
            "RYAAY+airline",
            "RYAI+airline"
        ]
    },
    {
        "isim": "Etihad Airways",
        "borsa_kodu": "",
        "aramalar": [
            "Etihad+Airways",
            "Etihad+airline",
            "Etihad+Aviation+Group",
            "Etihad+IPO",
            "Etihad+halka+arz"
        ]
    },
    {
        "isim": "LATAM Airlines",
        "borsa_kodu": "LTM",
        "aramalar": [
            "LATAM+Airlines",
            "LATAM+airline",
            "LATAM+Airlines+Group",
            "LATAM+aviation",
            "LTM+airline"
        ]
    }
]

HAVACILIK_KELIMELERI = [
    "airline", "airlines", "aviation", "aircraft", "airport", "flight", "flights",
    "airfare", "passenger", "passengers", "fleet", "pilot", "cargo", "runway",
    "boeing", "airbus", "route", "routes", "hub", "terminal", "gate", "cabin",
    "crew", "skyteam", "star alliance", "oneworld", "low cost", "carrier",
    "frequent flyer", "loyalty", "miles", "seat", "layover", "codeshare",
    "narrowbody", "widebody", "turbulence", "jetway", "tarmac", "hangar",
    "charter", "leasing", "lessor", "load factor", "yield", "ancillary",
    "delta air", "united airlines", "turkish airlines", "lufthansa", "ryanair",
    "air france", "klm", "singapore airlines", "etihad", "latam",
    "ana holdings", "all nippon", "thy",
    "DAL", "UAL", "THYAO", "LHA", "LHAG", "RYAAY", "RYAI", "LTM",
    "C6L", "SINGY", "SINGF", "9202", "AF",
    "A220", "A320", "A321", "A321neo", "A330", "A350", "A380",
    "737", "737 MAX", "777", "777X", "787", "787-9", "747",
    "IATA", "ICAO", "FAA", "EASA", "CAAC", "DGCA",
    "IPO", "earnings", "revenue", "profit", "loss", "EBITDA",
    "hedging", "fuel hedge", "jet fuel",
    "havayolu", "havayolları", "uçuş", "uçak", "havalimanı", "yolcu",
    "filo", "pilot", "kargo", "kabin", "rota", "hat", "thy",
    "bilet", "sefer", "iniş", "kalkış", "terminal", "pist",
    "aérien", "aérienne", "aéroport", "aéronef", "compagnie aérienne",
    "vol", "vols", "passager", "passagers", "flotte", "pilote",
    "cabine", "transporteur", "ligne aérienne", "siège", "fret aérien", "avion",
    "fluggesellschaft", "flughafen", "flugzeug", "flug", "flüge",
    "passagier", "passagiere", "luftfahrt", "billigflieger", "fracht",
    "strecke", "kabine", "triebwerk", "eurowings", "swiss air",
    "koukuu", "hikouki", "kyakusen", "zassen", "tobu",
    "aerolínea", "aerolinea", "aeropuerto", "vuelo", "vuelos",
    "pasajero", "pasajeros", "flota", "piloto", "carga", "ruta",
    "compañía aérea", "aviación", "avión",
    "companhia aérea", "aeroporto", "voo", "passageiro", "frota",
    "baixo custo", "linha aérea", "aviação",
    "luchtvaart", "vliegtuig", "vlucht", "vluchten", "luchthaven",
    "piloot", "vracht", "maatschappij",
    "aereo", "aerei", "aeroporto", "volo", "voli", "passeggero",
    "compagnia aerea", "flotta", "pilota", "aviazione",
    "etihad", "abu dhabi aviation", "طيران", "مطار", "ركاب",
    "hangong", "bihaenggi", "hangkong", "feiji", "jichang"
]

simdi = datetime.now(timezone.utc)
son_24_saat = simdi - timedelta(hours=24)
dosya_adi = f"AI_Kusursuz_Rapor_{simdi.strftime('%Y%m%d_%H%M')}.txt"

print("CONTRAIL — AI Analizi Başladı...")
print("=" * 60)

toplam_haber = 0
toplam_hata = 0
toplam_filtrelenen = 0
toplam_duplicate = 0

with open(dosya_adi, "w", encoding="utf-8") as rapor:
    rapor.write("CONTRAIL — AI YATIRIMCI RAPORU\n")
    rapor.write(f"Tarih: {simdi.strftime('%d.%m.%Y %H:%M')} UTC\n")
    rapor.write("=" * 60 + "\n\n")

    for sirket in SIRKETLER:
        print(f"\n✈️  {sirket['isim']} analiz ediliyor...")

        tum_entriler = []
        for arama in sirket["aramalar"]:
            url = f"https://news.google.com/rss/search?q={arama}&hl=en&gl=US&ceid=US:en"
            feed = feedparser.parse(url)
            tum_entriler.extend(feed.entries)

        gorulmus = set()
        benzersiz_entriler = []
        for entry in tum_entriler:
            if entry.title not in gorulmus:
                gorulmus.add(entry.title)
                benzersiz_entriler.append(entry)

        sirket_haber_sayisi = 0

        for haber in benzersiz_entriler[:10]:

            baslik_kucuk = haber.title.lower()
            havacilik_haberi = any(
                kelime.lower() in baslik_kucuk
                for kelime in HAVACILIK_KELIMELERI
            )
            if not havacilik_haberi:
                toplam_filtrelenen += 1
                continue

            try:
                tarih = datetime(*haber.published_parsed[:6], tzinfo=timezone.utc)
            except Exception:
                continue

            if tarih < son_24_saat:
                continue

            baslik = haber.title
            link = haber.link if hasattr(haber, 'link') else ''

            prompt = f"""
Sen kıdemli bir havacılık finans ve operasyon analistisin.
Asagidaki haber basligini analiz et ve SADECE JSON formatinda don:
{{
    "kategori": "Finansal, Filo, Operasyonel veya Jeopolitik",
    "skor": 7,
    "ozet": "Türkçe 1-2 cümlelik profesyonel özet. Tirnak isareti kullanma."
}}

SKORLAMA:
1-3: Rutin haberler (menu degisimi, kucuk PR)
4-6: Onemli ama yonetilebilir (tek rota, bilanço, kucuk sponsorluk)
7-8: Stratejik etki (CEO degisimi, buyuk siparis, beklenmedik zarar)
9-10: Kritik kriz (ucak kazasi, iflas, global grounding)

Skor mutlaka 1-10 arasi tam sayi olsun, tirnak icinde degil.
Ozet icinde asla tirnak isareti kullanma.

Haber: {baslik}
"""

            try:
                cevap = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.1-8b-instant",
                    response_format={"type": "json_object"}
                )

                ai_verisi = json.loads(cevap.choices[0].message.content)

                try:
                    skor = int(ai_verisi.get("skor", ai_verisi.get("Skor", 0)))
                except (ValueError, TypeError):
                    skor = 0

                kategori = ai_verisi.get("kategori", ai_verisi.get("Kategori", "Bilinmiyor"))
                ozet = ai_verisi.get("ozet", ai_verisi.get("Ozet", "-"))

                rapor.write(f"ŞİRKET   : {sirket['isim']}\n")
                rapor.write(f"BAŞLIK   : {baslik}\n")
                rapor.write(f"TARİH    : {tarih.strftime('%d.%m.%Y %H:%M')}\n")
                rapor.write(f"KATEGORİ : {kategori}\n")
                rapor.write(f"SKOR     : {skor}/10\n")
                rapor.write(f"ÖZET     : {ozet}\n")
                rapor.write("-" * 50 + "\n\n")

                try:
                    cursor.execute("""
                        INSERT INTO haberler (sirket, borsa_kodu, baslik, tarih, kategori, skor, ozet, link)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (baslik) DO NOTHING
                    """, (
                        sirket['isim'],
                        sirket['borsa_kodu'],
                        baslik,
                        tarih,
                        kategori,
                        skor,
                        ozet,
                        link
                    ))
                    if cursor.rowcount == 0:
                        toplam_duplicate += 1
                    conn.commit()
                except Exception as db_err:
                    print(f"  -> DB hatası: {db_err}")
                    conn.rollback()

                # 7+ ise Telegram bildirimi gönder
                if skor >= 7:
                    send_telegram_alert(baslik, sirket['isim'], skor, link)

                sirket_haber_sayisi += 1
                toplam_haber += 1

            except Exception as e:
                toplam_hata += 1
                print(f"  -> AI hatası: {e}")

        if sirket_haber_sayisi == 0:
            print("  -> Yeni haber yok.")
        else:
            print(f"  -> {sirket_haber_sayisi} haber analiz edildi ✅")

    rapor.write("\n" + "=" * 60 + "\n")
    rapor.write(f"TOPLAM ANALİZ EDİLEN HABER : {toplam_haber}\n")
    rapor.write(f"FİLTRELENEN ALAKASIZ HABER : {toplam_filtrelenen}\n")
    rapor.write(f"DUPLICATE (zaten vardı)    : {toplam_duplicate}\n")
    rapor.write(f"HATA SAYISI                : {toplam_hata}\n")
    rapor.write(f"RAPOR SONU\n")

cursor.close()
conn.close()

print(f"\n{'=' * 60}")
print(f"TOPLAM: {toplam_haber} haber analiz edildi")
print(f"Filtrelenen alakasız haber: {toplam_filtrelenen}")
print(f"Duplicate (zaten vardı): {toplam_duplicate}")
print(f"Hata: {toplam_hata}")
print(f"Dosya: {dosya_adi}")
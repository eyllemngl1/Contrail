import os
import json
import feedparser
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from groq import Groq
import psycopg2

load_dotenv()

conn = psycopg2.connect(
    host="localhost",
    database="contrail",
    user="postgres",
    password="250801"
)
cursor = conn.cursor()

api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

# Unique constraint yoksa ekle
try:
    cursor.execute("ALTER TABLE haberler ADD CONSTRAINT unique_baslik UNIQUE (baslik);")
    conn.commit()
except Exception:
    conn.rollback()

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
    # İngilizce — genel
    "airline", "airlines", "aviation", "aircraft", "airport", "flight", "flights",
    "airfare", "passenger", "passengers", "fleet", "pilot", "cargo", "runway",
    "boeing", "airbus", "route", "routes", "hub", "terminal", "gate", "cabin",
    "crew", "skyteam", "star alliance", "oneworld", "low cost", "carrier",
    "frequent flyer", "loyalty", "miles", "seat", "layover", "codeshare",
    "narrowbody", "widebody", "turbulence", "jetway", "tarmac", "hangar",
    "charter", "leasing", "lessor", "load factor", "yield", "ancillary",
    # Şirket isimleri — İngilizce
    "delta air", "united airlines", "turkish airlines", "lufthansa", "ryanair",
    "air france", "klm", "singapore airlines", "etihad", "latam",
    "ana holdings", "all nippon", "thy",
    # Borsa kodları
    "DAL", "UAL", "THYAO", "LHA", "LHAG", "RYAAY", "RYAI", "LTM",
    "C6L", "SINGY", "SINGF", "9202", "AF",
    # Uçak modelleri
    "A220", "A320", "A321", "A321neo", "A330", "A350", "A380",
    "737", "737 MAX", "777", "777X", "787", "787-9", "747",
    # Kurumlar ve düzenleyiciler
    "IATA", "ICAO", "FAA", "EASA", "CAAC", "DGCA",
    # Finansal terimler (havacılık bağlamında)
    "IPO", "earnings", "revenue", "profit", "loss", "EBITDA",
    "hedging", "fuel hedge", "jet fuel",
    # Türkçe
    "havayolu", "havayolları", "uçuş", "uçak", "havalimanı", "yolcu",
    "filo", "pilot", "kargo", "kabin", "rota", "hat", "thy",
    "bilet", "sefer", "iniş", "kalkış", "terminal", "pist",
    # Fransızca (Air France-KLM için)
    "aérien", "aérienne", "aéroport", "aéronef", "compagnie aérienne",
    "vol", "vols", "passager", "passagers", "flotte", "pilote",
    "cabine", "transporteur", "ligne aérienne", "siège", "fret aérien",
    "low cost", "aviation", "avion",
    # Almanca (Lufthansa için)
    "fluggesellschaft", "flughafen", "flugzeug", "flug", "flüge",
    "passagier", "passagiere", "luftfahrt", "billigflieger", "fracht",
    "strecke", "kabine", "triebwerk", "flotte", "pilot",
    "lufthansa", "eurowings", "swiss air",
    # Japonca romaji (ANA için)
    "koukuu", "hikouki", "kyakusen", "zassen", "tobu",
    # İspanyolca (LATAM için)
    "aerolínea", "aerolinea", "aeropuerto", "vuelo", "vuelos",
    "pasajero", "pasajeros", "flota", "piloto", "carga", "ruta",
    "compañía aérea", "aviación", "avión",
    # Portekizce (LATAM Brezilya için)
    "companhia aérea", "aeroporto", "voo", "passageiro", "frota",
    "baixo custo", "linha aérea", "aviação",
    # Hollandaca (KLM için)
    "luchtvaart", "vliegtuig", "vlucht", "vluchten", "luchthaven",
    "piloot", "vracht", "maatschappij",
    # İtalyanca
    "aereo", "aerei", "aeroporto", "volo", "voli", "passeggero",
    "compagnia aerea", "flotta", "pilota", "aviazione",
    # Arapça (Etihad için)
    "etihad", "abu dhabi aviation", "طيران", "مطار", "ركاب",
    # Korece romaji (ANA/Singapore için)
    "hangong", "bihaenggi", "hangong",
    # Çince romaji (bölgesel haberler için)
    "hangkong", "feiji", "jichang"
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

            prompt = f"""
Su havacilik haberini analiz et: {baslik}
Bana kesinlikle SADECE asagidaki JSON formatinda cevap ver:
{{
    "Kategori": "Filo, Finansal, Operasyonel veya Jeopolitik",
    "Skor": 7,
    "Ozet": "Tek cumlelik Turkce ozet. Tirnak isareti kullanma."
}}
Skor alani mutlaka 1 ile 10 arasinda tam sayi olsun, tirnak icinde degil.
Ozet icinde asla tirnak isareti kullanma.
"""

            try:
                cevap = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.1-8b-instant",
                    response_format={"type": "json_object"}
                )

                ai_verisi = json.loads(cevap.choices[0].message.content)

                try:
                    skor = int(ai_verisi.get("Skor", 0))
                except (ValueError, TypeError):
                    skor = 0

                rapor.write(f"ŞİRKET   : {sirket['isim']}\n")
                rapor.write(f"BAŞLIK   : {baslik}\n")
                rapor.write(f"TARİH    : {tarih.strftime('%d.%m.%Y %H:%M')}\n")
                rapor.write(f"KATEGORİ : {ai_verisi.get('Kategori', 'Bilinmiyor')}\n")
                rapor.write(f"SKOR     : {skor}/10\n")
                rapor.write(f"ÖZET     : {ai_verisi.get('Ozet', '-')}\n")
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
                        ai_verisi.get('Kategori', 'Bilinmiyor'),
                        skor,
                        ai_verisi.get('Ozet', '-'),
                        haber.link if hasattr(haber, 'link') else ''
                    ))
                    if cursor.rowcount == 0:
                        toplam_duplicate += 1
                    conn.commit()
                except Exception as db_err:
                    print(f"  -> DB hatası: {db_err}")
                    conn.rollback()

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
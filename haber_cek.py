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

def send_telegram_alert(haber_basligi, sirket, skor, link):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    mesaj = (
        f"🚨 <b>KRİTİK HAVACILIK HABERİ</b> 🚨\n\n"
        f"🏢 <b>Şirket:</b> {sirket}\n"
        f"🔥 <b>Skor:</b> {skor}/10\n"
        f"📰 <b>Başlık:</b> {haber_basligi}\n\n"
        f"🔗 <a href='{link}'>Haberi Oku</a>"
    )
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mesaj, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram bildirimi gönderilemedi: {e}")
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
    if int(skor) >= 8:
        send_telegram_alert(baslik, sirket, skor, link)
    conn.commit()
except Exception:
    conn.rollback()

def send_telegram_alert(baslik, sirket, skor, link):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    mesaj = (
        f"🚨 <b>KRİTİK HAVACILIK HABERİ</b> 🚨\n\n"
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
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram hatası: {e}")

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
    "cabine", "transporteur", "ligne aérienne", "siège", "fret aérien",
    "avion",
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
    "hangong", "bihaenggi",
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
            link = haber.link if hasattr(haber, 'link') else ''

            pprompt = f"""
    Sen kıdemli bir havacılık finans ve operasyon analistisin. 
    Aşağıdaki havacılık haberini okuyup analiz et.
    Bana SADECE JSON formatında şu bilgileri dön (başka hiçbir açıklama yazma):
    {{
        "kategori": "Finans, Operasyon, Kaza/Kriz, Müşteri Deneyimi veya Diğer",
        "skor": 1 ile 10 arası tamsayı,
        "ozet": "Türkçe 2-3 cümlelik net ve profesyonel özet"
    }}

    SKORLAMA KRİTERLERİ (Bu kurallara KESİNLİKLE uyacaksın):
    1-3 Puan (Düşük): Rutin ve sıradan gelişmeler (Örn: Uçak içi menü değişimi, tekil uçuş rötarları, basit PR kampanyaları).
    4-6 Puan (Orta): Şirket için olumlu/olumsuz ama yönetilebilir durumlar (Örn: Tek bir yeni rota açılışı, beklenen çeyreklik bilanço sonuçları, küçük sponsorluklar).
    7-8 Puan (Yüksek): Şirketin finansal yapısını veya operasyonunu ciddi etkileyecek stratejik gelişmeler (Örn: Üst düzey yönetim değişiklikleri/CEO istifası, bölgesel grevler, büyük uçak siparişleri, beklenmedik zarar açıklamaları).
    9-10 Puan (Kritik): Şirketin veya sektörün kaderini değiştirecek acil krizler (Örn: Ölümcül uçak kazaları, iflas süreçleri, küresel uçuş durdurma kararları (grounding), tüm sistemi çökerten siber saldırılar).

    Haber Metni: {haber_metni}
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
                        link
                    ))
                    if cursor.rowcount == 0:
                        toplam_duplicate += 1
                    conn.commit()
                except Exception as db_err:
                    print(f"  -> DB hatası: {db_err}")
                    conn.rollback()

                # Skor 4+ ise Telegram bildirimi gönder
                if skor >= 4:
                    send_telegram_alert(baslik, sirket['isim'], skor, link)
                    print(f"  🚨 KRİTİK HABER — Telegram bildirimi gönderildi!")

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
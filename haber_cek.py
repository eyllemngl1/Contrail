import feedparser
from datetime import datetime, timezone, timedelta

# 10 şirketin hepsi
SIRKETLER = [
    {"isim": "Delta Air Lines",      "arama": "Delta+Air+Lines"},
    {"isim": "United Airlines",      "arama": "United+Airlines"},
    {"isim": "Turkish Airlines",     "arama": "Turkish+Airlines"},
    {"isim": "Lufthansa",            "arama": "Lufthansa"},
    {"isim": "Air France KLM",       "arama": "Air+France+KLM"},
    {"isim": "Singapore Airlines",   "arama": "Singapore+Airlines"},
    {"isim": "ANA Holdings",         "arama": "ANA+Holdings"},
    {"isim": "Ryanair",              "arama": "Ryanair"},
    {"isim": "Etihad Airways",       "arama": "Etihad+Airways"},
    {"isim": "LATAM Airlines",       "arama": "LATAM+Airlines"}
]

# Son 24 saat filtresi
simdi = datetime.now(timezone.utc)
son_24_saat = simdi - timedelta(hours=24)

print("CONTRAIL — Haber Motoru Başladı")
print(f"Tarih: {simdi.strftime('%d.%m.%Y %H:%M')} UTC")
print("=" * 60)

tum_haberler = []

for sirket in SIRKETLER:
    url = f"https://news.google.com/rss/search?q={sirket['arama']}&hl=en&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    
    sirket_haberleri = []
    
    for haber in feed.entries:
        try:
            tarih = datetime(*haber.published_parsed[:6], tzinfo=timezone.utc)
            if tarih >= son_24_saat:
                sirket_haberleri.append({
                    "sirket": sirket["isim"],
                    "baslik": haber.title,
                    "tarih": tarih.strftime("%d.%m.%Y %H:%M"),
                    "kaynak": haber.source.title if hasattr(haber, "source") else "Bilinmiyor",
                    "link": haber.link
                })
        except:
            continue
    
    tum_haberler.extend(sirket_haberleri)
    print(f"✓ {sirket['isim']}: {len(sirket_haberleri)} haber bulundu")

# Tarihe göre sırala (en yeni önce)
tum_haberler.sort(key=lambda x: x["tarih"], reverse=True)

# Dosyaya kaydet
dosya_adi = f"haberler_{simdi.strftime('%Y%m%d_%H%M')}.txt"

with open(dosya_adi, "w", encoding="utf-8") as f:
    f.write(f"CONTRAIL — Haber Raporu\n")
    f.write(f"Oluşturulma: {simdi.strftime('%d.%m.%Y %H:%M')} UTC\n")
    f.write(f"Toplam haber: {len(tum_haberler)}\n")
    f.write("=" * 60 + "\n\n")
    
    for haber in tum_haberler:
        f.write(f"ŞİRKET : {haber['sirket']}\n")
        f.write(f"BAŞLIK : {haber['baslik']}\n")
        f.write(f"TARİH  : {haber['tarih']}\n")
        f.write(f"KAYNAK : {haber['kaynak']}\n")
        f.write(f"LINK   : {haber['link']}\n")
        f.write("-" * 60 + "\n\n")

print(f"\n{'=' * 60}")
print(f"TOPLAM: {len(tum_haberler)} haber son 24 saatte")
print(f"Dosya kaydedildi: {dosya_adi}")
print("=" * 60)
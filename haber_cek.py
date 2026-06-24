import os
import feedparser
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from groq import Groq

# Gizli şifremizi okuyup yapay zekayı uyandırıyoruz
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

SIRKETLER = [
    {"isim": "Delta Air Lines",      "arama": "Delta+Air+Lines"},
    {"isim": "Turkish Airlines",     "arama": "Turkish+Airlines"},
    {"isim": "Lufthansa",            "arama": "Lufthansa"}
] # Şimdilik sistemi yormamak için 3 şirketle test ediyoruz

simdi = datetime.now(timezone.utc)
son_24_saat = simdi - timedelta(hours=24)

print("CONTRAIL — AI Destekli Haber Motoru Başladı")
print("=" * 60)

for sirket in SIRKETLER:
    url = f"https://news.google.com/rss/search?q={sirket['arama']}&hl=en&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    
    print(f"\n✈️ ŞİRKET: {sirket['isim']}")
    
    # Her şirket için sadece en yeni 1 haberi test için alıyoruz
    for haber in feed.entries[:1]:
        tarih = datetime(*haber.published_parsed[:6], tzinfo=timezone.utc)
        
        if tarih >= son_24_saat:
            baslik = haber.title
            print(f"Orijinal Başlık: {baslik}")
            print("Yapay Zeka Analiz Ediyor...")
            
            # Groq AI'a analiz talimatı veriyoruz
            prompt = f"""
            Şu havacılık haberini analiz et: "{baslik}"
            Bana tam olarak şu formatta cevap ver:
            Kategori: (Filo, Finansal, Operasyonel veya Jeopolitik)
            Skor: (1 ile 10 arası bir önem skoru)
            Özet: (Tek cümlelik Türkçe özet)
            """
            
            cevap = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant", 
            )
            
            print("-" * 40)
            print(cevap.choices[0].message.content)
            print("=" * 60)
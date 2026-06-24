import feedparser

kaynaklar = [
    {
        "isim": "Delta Air Lines",
        "url": "https://news.google.com/rss/search?q=Delta+Air+Lines&hl=en&gl=US&ceid=US:en"
    },
    {
        "isim": "Turkish Airlines",
        "url": "https://news.google.com/rss/search?q=Turkish+Airlines&hl=en&gl=US&ceid=US:en"
    },
    {
        "isim": "Lufthansa",
        "url": "https://news.google.com/rss/search?q=Lufthansa&hl=en&gl=US&ceid=US:en"
    }
]

for kaynak in kaynaklar:
    print(f"\n{'='*50}")
    print(f"ŞİRKET: {kaynak['isim']}")
    print(f"{'='*50}")
    
    feed = feedparser.parse(kaynak["url"])
    
    for haber in feed.entries[:3]:
        print(f"\nBAŞLIK : {haber.title}")
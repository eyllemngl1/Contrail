import os
from dotenv import load_dotenv
from groq import Groq

# .env dosyasındaki gizli şifremizi okuyoruz
load_dotenv()

# Şifreyi değişkene atıyoruz
api_key = os.getenv("GROQ_API_KEY")

# Yapay zekayı (Groq) şifremizle uyandırıyoruz
client = Groq(api_key=api_key)

print("Contrail AI Motoru Test Ediliyor...")
print("-" * 50)

# Yapay zekaya ilk sorumuzu soruyoruz
cevap = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Bana havacılıkla ilgili çok kısa, bir cümlelik ilginç bir bilgi ver.",
        }
    ],
    model="llama-3.1-8b-instant"
)

print("AI CEVABI:")
print(cevap.choices[0].message.content)
print("-" * 50)
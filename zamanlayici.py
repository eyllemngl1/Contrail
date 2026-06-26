import schedule
import time
import subprocess
import sys
from datetime import datetime

def haberleri_cek():
    print(f"\n{'='*60}")
    print(f"OTOMATİK ÇALIŞMA: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*60}")
    subprocess.run([sys.executable, "haber_cek.py"])

# Her 2 saatte bir çalış
schedule.every(2).hours.do(haberleri_cek)

# Başlarken bir kere çalıştır
haberleri_cek()

print("\nZamanlayıcı aktif — her 2 saatte bir çalışacak.")
print("Durdurmak için Ctrl+C bas.\n")

while True:
    schedule.run_pending()
    time.sleep(60)
# 1. Python tabanlı hafif imaj
FROM python:3.11-slim

# 2. Çalışma dizini
WORKDIR /app

# 3. Flet için gerekli Linux kütüphanelerini kuruyoruz
RUN apt-get update && apt-get install -y \
    libgtk-3-0 \
    libgstcodecparsers-1.0-0 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# 4. Kütüphaneleri yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Tüm dosyaları kopyala
COPY . .

# 6. Uygulamanın portu
EXPOSE 8080

# 7. Uygulamayı çalıştır
CMD ["python", "main.py"]
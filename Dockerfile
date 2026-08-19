FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

# ایجاد پوشه داده
RUN mkdir -p data

CMD ["python", "bot.py"]

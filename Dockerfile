# 1. Базовий Python образ
FROM python:3.11-slim

# 2. Робоча директорія
WORKDIR /app

# 3. Копіюємо всі файли
COPY . .

# 4. Встановлюємо залежності
RUN pip install --no-cache-dir -r requirements.txt

# 5. Команда запуску
CMD ["python", "bot.py"]

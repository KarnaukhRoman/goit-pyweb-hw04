FROM python:3.12
LABEL authors="Roman Karnaukh"

ENV APP_HOME /app

# Встановимо робочу директорію всередині контейнера
WORKDIR $APP_HOME

# Копіюємо всі файли проекту в контейнер
COPY . .

# Встановлюємо необхідні пакети
RUN pip install --no-cache-dir pathlib

# Відкриваємо порти
EXPOSE 3000
EXPOSE 5000

# Запускаємо наш додаток
ENTRYPOINT ["python", "main.py"]

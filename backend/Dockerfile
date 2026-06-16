# Use the official Microsoft Playwright image (includes all browser dependencies)
FROM mcr.microsoft.com/playwright/python:v1.43.0-jammy

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your code
COPY . .

# Force Python to print logs immediately instead of hiding them
ENV PYTHONUNBUFFERED=1

# Tell Docker to use Render's native default port
EXPOSE 10000

CMD python -m uvicorn main:app --host 0.0.0.0 --port 10000
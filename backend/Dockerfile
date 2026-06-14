# Use the official Microsoft Playwright image (includes all browser dependencies)
FROM mcr.microsoft.com/playwright/python:v1.43.0-jammy

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your code
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Command to run the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
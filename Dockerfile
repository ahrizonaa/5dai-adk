FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=7020
ENV ENVIRONMENT=production

# Expose port
EXPOSE 7020

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7020"]

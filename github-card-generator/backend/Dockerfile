FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy requirements and install deps
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copy source
COPY . .

# Create directory for cards
RUN mkdir -p static/cards

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

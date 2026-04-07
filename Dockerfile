FROM python:3.11-slim

ARG BUILD_VERSION=unknown

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY VERSION .

RUN mkdir -p /data

ENV BUILD_VERSION=${BUILD_VERSION}

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

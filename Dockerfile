FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY tests/ ./tests/
RUN mkdir -p data/raw data/processed logs reports

CMD ["python", "src/pipeline.py"]

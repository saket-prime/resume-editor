FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends libreoffice-writer fonts-crosextra-carlito fonts-crosextra-caladea fonts-liberation fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["sh", "-c", "streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT:-8501} --server.headless=true"]

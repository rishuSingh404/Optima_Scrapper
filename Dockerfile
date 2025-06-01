# Dockerfile

FROM python:3.10-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        chromium-browser \
        chromium-chromedriver \
        fonts-liberation \
        libnss3 \
        libxkbfile1 \
        libxrender1 \
        libxcomposite1 \
        libxcursor1 \
        libxi6 \
        libxtst6 \
        libglu1-mesa \
        libdbus-glib-1-2 \
        libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium-browser
ENV CHROME_PATH=/usr/bin/chromium-browser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scraper_module.py .
COPY streamlit_app.py .

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]

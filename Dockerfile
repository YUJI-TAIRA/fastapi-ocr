FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Tesseract-OCRと日本語の学習データをインストール
RUN apt-get update && \
    apt-get install -y tesseract-ocr tesseract-ocr-jpn libgl1 libglib2.0-0 libsm6 libxext6 libxrender1

# poetryのインストール先の指定
ENV POETRY_HOME=/opt/poetry

# poetryインストール
RUN pip install poetry && \
    poetry config virtualenvs.create false

COPY pyproject.toml* poetry.lock* ./

RUN if [ -f pyproject.toml ]; then poetry install; fi

ENTRYPOINT ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--reload"]
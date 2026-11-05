FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends openssl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 10001 --create-home reviewer \
    && mkdir /fixture-tls && chown reviewer:reviewer /fixture-tls
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt pytest==9.2.0
COPY service/ service/
COPY tools/reviewer_fixture.py tools/reviewer_fixture.py
USER reviewer
ENV PYTHONPATH=/app PYTHONUNBUFFERED=1
CMD ["python", "tools/reviewer_fixture.py"]

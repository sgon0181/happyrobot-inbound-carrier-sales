# The Carrier Sales Service: Python 3.12 slim, runtime packages only, run as a non-root user.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home service
COPY service/ /app/service/
USER 10001
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
# Settings load when the app is created, so a missing secret stops startup with its name.
CMD ["uvicorn", "--factory", "service.main:create", "--host", "0.0.0.0", "--port", "8080"]

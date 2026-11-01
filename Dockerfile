FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home carrier
COPY service/ /app/service/
USER 10001
ENV PYTHONUNBUFFERED=1
EXPOSE 8767
CMD ["python", "-m", "service.api.app"]

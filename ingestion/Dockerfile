FROM python:3.11-slim
WORKDIR /app
COPY ingest.py .
RUN pip install pymongo
CMD ["python", "ingest.py"]

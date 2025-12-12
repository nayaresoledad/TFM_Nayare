FROM python:3.13-slim
WORKDIR /app
COPY server.py ./
RUN pip install --no-cache-dir fastapi uvicorn psycopg2-binary
EXPOSE 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]

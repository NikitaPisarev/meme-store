FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

RUN chmod +x run_app.sh

ENTRYPOINT ["./run_app.sh"]

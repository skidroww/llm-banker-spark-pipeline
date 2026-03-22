# llm-banker-spark-pipeline/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Spark 구동을 위한 Java(OpenJDK) 설치
RUN apt-get update && \
    apt-get install -y default-jre && \
    apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 포트폴리오용 꿀팁: 컨테이너가 켜진 후 60초마다 주기적으로 Spark 스크립트를 실행하게 만듭니다. (배치 파이프라인 시뮬레이션)
CMD ["sh", "-c", "while true; do python spark_processor.py; sleep 60; done"]
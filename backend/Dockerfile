# Backend Flask API
FROM python:3.11-slim

WORKDIR /app

# 패키지 설치 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY src/ .

EXPOSE 8080

# 실행 명령어
CMD ["python", "app.py"]

# CI 테스트 

# Python Flask
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


# ============================================
# Node.js 사용 시 (주석 해제 후 위 내용 주석 처리)
# ============================================
# FROM node:18-alpine
# 
# WORKDIR /app
# 
# # 패키지 설치
# COPY package*.json ./
# RUN npm install
# 
# # 소스 복사
# COPY src/ .
# 
# EXPOSE 8080
# 
# CMD ["node", "index.js"]


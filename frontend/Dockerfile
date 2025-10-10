# Frontend Node.js Express
FROM node:18-alpine

WORKDIR /app

# 패키지 설치
COPY package*.json ./
RUN npm install

# 소스 복사
COPY src/ ./

EXPOSE 3000

# 실행 명령어
CMD ["node", "server.js"]

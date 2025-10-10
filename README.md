# 주식 모니터링 대시보드

주식 시장 모니터링과 자동 스케일링을 위한 GitOps 기반 Kubernetes 애플리케이션

## 구조

```
k8s-gitops-autoscaling-app/
├── frontend/                   # 프론트엔드 (Node.js + Express)
├── backend/                    # 백엔드 (Python + Flask)
├── k8s/                        # Kubernetes 매니페스트
├── monitoring/                 # 모니터링 (Prometheus + Grafana)
└── .github/workflows/          # CI/CD 파이프라인
```

## 주요 기능

- 트래픽 시뮬레이션 (장 시작/종료/야간 모드)
- 자동 스케일링 (HPA)
- 실시간 모니터링
- GitOps CI/CD 파이프라인

## 기술 스택

- Frontend: Node.js + Express
- Backend: Python + Flask
- Infrastructure: Kubernetes + Docker
- CI/CD: GitHub Actions + ArgoCD
- Monitoring: Prometheus + Grafana

## 사용법

### 1. 로컬 개발
```bash
# 백엔드 실행
cd backend
pip install -r requirements.txt
python src/app.py

# 프론트엔드 실행
cd frontend
npm install
npm start
```

### 2. Docker 실행
```bash
# 백엔드
docker build -t backend ./backend
docker run -p 8080:8080 backend

# 프론트엔드
docker build -t frontend ./frontend
docker run -p 3000:3000 frontend
```

### 3. Kubernetes 배포
```bash
# 모든 서비스 배포
kubectl apply -f k8s/

# 상태 확인
kubectl get pods
kubectl get services
kubectl get hpa
```

## 🔄 CI/CD 파이프라인

### 자동화된 배포 플로우
1. **코드 푸시** → GitHub
2. **GitHub Actions** → Docker 이미지 빌드 & 푸시
3. **Git 커밋** → deployment.yml 이미지 태그 업데이트
4. **ArgoCD** → Git 변경 감지 & 자동 배포
5. **HPA** → 트래픽에 따른 자동 스케일링

### 경로 기반 트리거
- `frontend/` 변경 → 프론트엔드만 빌드 & 배포
- `backend/` 변경 → 백엔드만 빌드 & 배포
- `shared/` 변경 → 둘 다 빌드 & 배포

## 📈 모니터링

### Prometheus + Grafana
- CPU/메모리 사용률
- Pod 수 변화
- 트래픽 레벨
- 응답 시간

### HPA 메트릭
- CPU 사용률
- 메모리 사용률
- 커스텀 메트릭 (향후 확장)

## 🎯 트래픽 시뮬레이션 테스트

### 시나리오 1: 장 시작
```bash
# UI에서 "장 시작 시뮬레이션" 버튼 클릭
# 또는 API 호출
curl -X POST http://localhost:8080/api/simulate-traffic \
  -H "Content-Type: application/json" \
  -d '{"scenario": "market_open", "traffic_level": "high"}'
```

### 시나리오 2: 야간 모드
```bash
curl -X POST http://localhost:8080/api/simulate-traffic \
  -H "Content-Type: application/json" \
  -d '{"scenario": "night_mode", "traffic_level": "low"}'
```

## 🔧 설정

### 환경 변수
```bash
# 백엔드
FLASK_ENV=production

# 프론트엔드
NODE_ENV=production
```

### Docker 이미지
- **백엔드**: `dorrry/k8s-gitops-app-backend:latest`
- **프론트엔드**: `dorrry/k8s-gitops-app-frontend:latest`

## 📝 TODO

- [ ] 주식 API 연동 (Alpha Vantage, Yahoo Finance)
- [ ] WebSocket 실시간 데이터 스트리밍
- [ ] 데이터베이스 연동 (PostgreSQL, Redis)
- [ ] 알림 시스템 (Slack, Email)
- [ ] 보안 강화 (JWT, OAuth)
- [ ] 성능 최적화 (캐싱, CDN)

## 🤝 기여

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

**알차 주식 모니터링 대시보드** - 실시간 시장 모니터링과 자동 스케일링으로 안정적인 서비스 제공 🚀
Kubernetes HPA 기반 자동 스케일링 웹앱 - GitOps CI/CD 파이프라인 구축

# 모니터링 설정 가이드

## Prometheus + Grafana 설치

### 1. Prometheus 설치

```bash
# Prometheus 배포
kubectl apply -f monitoring/prometheus/prometheus-deployment.yml

# 확인
kubectl get pods -n monitoring
kubectl get svc -n monitoring

# 접속
# http://100.73.36.36:30090
```

### 2. Grafana 설치

```bash
# Grafana 배포
kubectl apply -f monitoring/grafana/grafana-deployment.yml

# 확인
kubectl get pods -n monitoring
kubectl get svc -n monitoring

# 접속
# http://100.73.36.36:30300
# ID: admin / PW: admin
```

### 3. Grafana 대시보드 설정

1. **Prometheus 데이터소스 추가**
   - Configuration → Data Sources → Add data source
   - Type: Prometheus
   - URL: `http://prometheus.monitoring.svc.cluster.local:9090`
   - Save & Test

2. **Kubernetes 대시보드 Import**
   - Dashboards → Import
   - Dashboard ID: 315 (Kubernetes cluster monitoring)
   - Dashboard ID: 6417 (Kubernetes Pods)
   - Dashboard ID: 3662 (Prometheus 2.0 Stats)

### 4. HPA 메트릭 확인

- CPU 사용률
- Memory 사용률
- Pod 개수 변화
- Network I/O

## 파일 구조

```
monitoring/
├── README.md
├── prometheus/
│   └── prometheus-deployment.yml
└── grafana/
    └── grafana-deployment.yml
```

## 접속 정보

- **Prometheus**: http://100.73.36.36:30090
- **Grafana**: http://100.73.36.36:30300
  - ID: admin
  - PW: admin


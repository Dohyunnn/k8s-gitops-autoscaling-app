# 모니터링 설정 가이드

## Prometheus + Grafana 설치 순서

### 0. 사전 준비
- `kubectl config current-context`로 작업할 클러스터가 맞는지 확인한다다.
- NodePort `30090`(Prometheus), `30300`(Grafana)가 방화벽/보안그룹에서 열려 있는지 확인한다.

### 1. Prometheus 배포
```bash
# Prometheus, Namespace, RBAC, ConfigMap, Service 생성
kubectl apply -f monitoring/prometheus/prometheus-deployment.yml

# 상태 확인
kubectl get pods -n monitoring
kubectl get svc -n monitoring
```

> Manifest 내부에서 `monitoring` 네임스페이스를 먼저 생성하므로 별도 명령은 필요 없다.

Prometheus UI
```
http://<node-ip>:30090
```

### 2. Grafana 배포
```bash
# Grafana Deployment/Service 및 기본 데이터소스 구성
kubectl apply -f monitoring/grafana/grafana-deployment.yml

# 상태 확인
kubectl get pods -n monitoring
kubectl get svc -n monitoring
```

Grafana UI
```
http://<node-ip>:30300
ID: admin
PW: admin
```

> `monitoring/grafana/grafana-deployment.yml`에 정의된 Secret을 수정하면 기본 관리자 계정을 쉽게 바꿀 수 있다.

### 3. Grafana 대시보드 설정

1. **데이터소스 확인**
   - 로그인 후 *Configuration → Data Sources* 메뉴에서 `Prometheus`가 자동 등록돼 있는지 확인한다.
   - 문제가 있을 경우 URL은 `http://prometheus.monitoring.svc.cluster.local:9090`을 사용한다.

2. **추천 대시보드 Import**
   - *Dashboards → Import* 메뉴에서 다음 ID를 입력한다.
     - `315` : Kubernetes cluster monitoring (via Prometheus)
     - `6417`: Kubernetes workload metrics
     - `3662`: Prometheus 2.0 statistics

### 4. HPA 및 애플리케이션 메트릭
- Pod AutoScaling 상태: `kube_pod_container_resource_requests`, `kube_horizontalpodautoscaler_status_current_replicas` 등
- 애플리케이션 사용자 정의 메트릭은 각 서비스의 `/metrics` 엔드포인트에 `prometheus.io/scrape="true"` 주석을 추가해 수집할 수 있다.

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

- **Prometheus**: NodePort `30090`
- **Grafana**: NodePort `30300` (기본 계정 `admin` / `admin`)

# k8s-gitops-autoscaling-app

Kubernetes GitOps 기반 자동 스케일링 웹 애플리케이션

## 프로젝트 개요
- **목적**: Kubernetes HPA를 활용한 자동 스케일링 웹앱 구현
- **기술 스택**: Kubernetes, Docker, GitHub Actions, ArgoCD, Prometheus, Grafana
- **CI/CD**: GitOps 방식 (GitHub Actions + ArgoCD)

## 프로젝트 구조
```
k8s-gitops-autoscaling-app/
├── .github/workflows/      # CI/CD 파이프라인
├── k8s/                    # Kubernetes 배포 파일
├── monitoring/             # Prometheus + Grafana 
├── src/                    # 웹앱 소스코드
├── docs/                   # 문서
├── Dockerfile              # Docker 이미지 빌드
└── requirements.txt        # Python 패키지
```


## 접속 정보
- **웹앱**: http://100.73.36.36:30080
- **Grafana**: http://100.73.36.36:30300
- **Prometheus**: http://100.73.36.36:30090

## SSH 접속
- **Master**: `ssh dohyeon@100.73.36.36 -p 10030`
- **Worker1**: `ssh dohyeon@100.73.36.36 -p 10031`
- **Worker2**: `ssh dohyeon@100.73.36.36 -p 10032`

## 문서
- `TODO.md` - 작업 목록
- `TEAM_GUIDE.md` - 팀원 작업 가이드
- `docs/ARCHITECTURE.md` - 아키텍처 문서
- `docs/PRESENTATION.md` - 발표 시연 가이드

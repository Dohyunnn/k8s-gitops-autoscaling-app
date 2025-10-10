# Kubernetes GitOps 자동 스케일링 애플리케이션

VirtualBox로 구축된 Kubernetes 클러스터에서 Ansible을 통한 자동화 및 ArgoCD GitOps 기반 자동 배포 및 HPA를 구현한 주식 모니터링 대시보드

## 프로젝트 구조

```
k8s-gitops-autoscaling-app/
├── frontend/                   # 프론트엔드 (Node.js + Express)
├── backend/                    # 백엔드 (Python + Flask)
├── k8s/                        # Kubernetes 매니페스트
│   ├── argocd-application.yml  # ArgoCD Application 정의
│   ├── backend-deployment.yml  # 백엔드 배포 설정
│   ├── frontend-deployment.yml # 프론트엔드 배포 설정
│   ├── backend-hpa.yml         # 백엔드 HPA 설정
│   ├── frontend-hpa.yml        # 프론트엔드 HPA 설정
│   └── argocd-image-updater-* # ArgoCD Image Updater 설정
├── ansible/                    # Ansible 자동화 스크립트
│   ├── playbook.yml           # 메인 플레이북
│   ├── site.yml               # 사이트 플레이북
│   ├── inventory.ini          # 인벤토리 파일
│   ├── ansible.cfg            # Ansible 설정
│   ├── requirements.yml       # 의존성 관리
│   ├── tasks/                 # 태스크 파일들
│   │   ├── argocd.yml         # ArgoCD 설치 태스크
│   │   ├── hpa.yml            # HPA 설정 태스크
│   │   └── monitoring.yml     # 모니터링 설정 태스크
│   └── roles/                 # Ansible 역할
│       ├── common/             # 공통 설정
│       ├── master/             # 마스터 노드 설정
│       ├── worker/             # 워커 노드 설정
│       └── argocd/             # ArgoCD 설치
└── README.md
```

## 주요 기능

- **GitOps 자동 배포**: ArgoCD를 통한 Git 기반 자동 배포
- **자동 이미지 업데이트**: ArgoCD Image Updater를 통한 Docker Hub 이미지 자동 감지 및 업데이트
- **자동 스케일링**: HPA를 통한 CPU/메모리 기반 자동 스케일링
- **트래픽 시뮬레이션**: 주식 시장 시나리오 기반 트래픽 테스트
- **Ansible 자동화**: Kubernetes 클러스터 자동 구축 및 설정

## 기술 스택

- **Frontend**: Node.js + Express
- **Backend**: Python + Flask
- **Infrastructure**: Kubernetes + Docker
- **GitOps**: ArgoCD + ArgoCD Image Updater
- **자동화**: Ansible
- **모니터링**: Kubernetes Metrics Server + HPA



##  GitOps 파이프라인

### 자동화된 배포 플로우

1. **코드 푸시** → GitHub 저장소
2. **GitHub Actions** → Docker 이미지 빌드 & Docker Hub 푸시
3. **ArgoCD Image Updater** → 새 이미지 태그 감지
4. **ArgoCD** → Git 변경사항 감지 & 자동 배포
5. **HPA** → 트래픽에 따른 자동 스케일링

### ArgoCD 설정

- **자동 동기화**: `prune: true`, `selfHeal: true`
- **이미지 업데이트**: 2분마다 Docker Hub 확인
- **재시도 정책**: 최대 5회, 백오프 5초~3분

## HPA (Horizontal Pod Autoscaler) 설정

### 백엔드 HPA
- **최소 파드**: 2개
- **최대 파드**: 10개
- **CPU 임계값**: 70%
- **메모리 임계값**: 80%

### 프론트엔드 HPA
- **최소 파드**: 2개
- **최대 파드**: 8개
- **CPU 임계값**: 70%
- **메모리 임계값**: 80%





# Ansible로 Kubernetes GitOps 자동화 관리

이 디렉토리는 Kubernetes 클러스터에 ArgoCD, 모니터링, HPA를 자동으로 배포하는 Ansible Playbook을 포함합니다.

## 📁 디렉토리 구조

```
ansible/
├── playbook.yml              # 메인 플레이북
├── inventory.yml             # 호스트 인벤토리 (YAML 형식)
├── inventory.ini             # 호스트 인벤토리 (INI 형식, 레거시)
├── requirements.yml          # Ansible Galaxy 의존성
├── ansible.cfg              # Ansible 설정
├── group_vars/              # 그룹 변수
│   └── all.yml             # 모든 호스트에 적용되는 변수
├── roles/                   # Ansible 롤
│   ├── common/             # 공통 설정
│   ├── master/             # 마스터 노드 설정
│   └── worker/             # 워커 노드 설정
└── tasks/                   # 개별 태스크
    ├── argocd.yml          # ArgoCD 설치
    ├── monitoring.yml      # Prometheus & Grafana 설치
    └── hpa.yml             # Metrics Server & HPA 설정
```

## 🚀 빠른 시작

### 1. 사전 준비

```bash
# Ansible 설치 확인
ansible --version

# Python3 및 pip 설치 확인
python3 --version
pip3 --version

# kubectl 설치 확인
kubectl version --client
```

### 2. Ansible 컬렉션 설치

```bash
cd ansible

# 필요한 컬렉션 설치
ansible-galaxy collection install -r requirements.yml

# 설치 확인
ansible-galaxy collection list | grep kubernetes
```

### 3. 인벤토리 수정

본인의 환경에 맞게 `inventory.yml` 수정:

```bash
vim inventory.yml
```

### 4. Playbook 실행

```bash
# 전체 실행
ansible-playbook -i inventory.yml playbook.yml

# 특정 태그만 실행
ansible-playbook -i inventory.yml playbook.yml --tags argocd
ansible-playbook -i inventory.yml playbook.yml --tags monitoring
ansible-playbook -i inventory.yml playbook.yml --tags hpa
```

## 📝 사용 가능한 태그

| 태그 | 설명 | 포함 작업 |
|------|------|----------|
| `argocd` | ArgoCD 설치 | ArgoCD, Image Updater |
| `monitoring` | 모니터링 스택 설치 | Prometheus, Grafana |
| `hpa` | 자동 스케일링 설정 | Metrics Server, HPA |
| `gitops` | GitOps 관련 (argocd와 동일) | ArgoCD, Image Updater |
| `autoscaling` | 오토스케일링 (hpa와 동일) | Metrics Server, HPA |

### 예제

```bash
# ArgoCD만 설치
ansible-playbook -i inventory.yml playbook.yml --tags argocd

# 모니터링과 HPA만 설치
ansible-playbook -i inventory.yml playbook.yml --tags monitoring,hpa

# 전체 GitOps 스택 설치
ansible-playbook -i inventory.yml playbook.yml
```

## 🔧 설정 변수

### group_vars/all.yml

```yaml
# Kubernetes 버전
k8s_version: "1.31"

# 네트워크 설정
pod_network_cidr: "10.244.0.0/16"
control_plane_endpoint: "192.168.200.30:6443"

# 컨테이너 런타임
container_runtime: "containerd"
```

### 환경별 설정

개발 환경과 프로덕션 환경을 분리하려면:

```bash
# 개발 환경
ansible-playbook -i inventory-dev.yml playbook.yml

# 프로덕션 환경
ansible-playbook -i inventory-prod.yml playbook.yml
```

## 🧪 테스트

### Syntax Check

```bash
# Playbook 문법 검사
ansible-playbook -i inventory.yml playbook.yml --syntax-check

# Dry-run 모드 (실제 변경 없이 테스트)
ansible-playbook -i inventory.yml playbook.yml --check
```

### 연결 테스트

```bash
# 모든 호스트 연결 테스트
ansible all -i inventory.yml -m ping

# 마스터 노드만 테스트
ansible masters -i inventory.yml -m ping

# 워커 노드만 테스트
ansible workers -i inventory.yml -m ping
```

## 📊 실행 예시

```bash
$ ansible-playbook -i inventory.yml playbook.yml --tags argocd

PLAY [Deploy ArgoCD] ***********************************************************

TASK [Create argocd namespace] *************************************************
changed: [master1]

TASK [Install ArgoCD] **********************************************************
changed: [master1]

TASK [Wait for ArgoCD server to be ready] **************************************
ok: [master1]

TASK [Display ArgoCD admin password] *******************************************
ok: [master1] => {
    "msg": "ArgoCD admin password: xxxxxxxxxxx"
}

PLAY RECAP *********************************************************************
master1                    : ok=10   changed=5    unreachable=0    failed=0
```

## 🔍 트러블슈팅

### 1. 권한 오류

```bash
# become 권한 문제
ansible-playbook -i inventory.yml playbook.yml --ask-become-pass

# SSH 키 문제
ansible-playbook -i inventory.yml playbook.yml --private-key ~/.ssh/id_rsa
```

### 2. Python 모듈 누락

```bash
# 필요한 Python 패키지 설치
pip3 install kubernetes
pip3 install openshift
pip3 install pyyaml
```

### 3. kubectl 설정 문제

```bash
# kubeconfig 경로 확인
export KUBECONFIG=/home/dohyeon/.kube/config

# 또는 playbook에서 지정
ansible-playbook -i inventory.yml playbook.yml \
  -e "kubeconfig=/home/dohyeon/.kube/config"
```

## 🎯 다음 단계

1. **ArgoCD 설정 완료**: [../ARGOCD_SETUP.md](../ARGOCD_SETUP.md) 참고
2. **Secret 생성**: Docker Hub, GitHub 인증 정보 설정
3. **Application 생성**: ArgoCD Application 배포
4. **테스트**: End-to-End 자동 배포 테스트

## 📚 참고 자료

- [Ansible Documentation](https://docs.ansible.com/)
- [Ansible Kubernetes Collection](https://galaxy.ansible.com/kubernetes/core)
- [ArgoCD Installation](https://argo-cd.readthedocs.io/en/stable/getting_started/)


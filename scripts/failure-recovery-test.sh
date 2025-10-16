#!/bin/bash

# 장애 복구 시간 측정 + CPU 사용률 요약

set -euo pipefail

get_cpu_request_m() {
  local app=$1
  local raw
  raw=$(kubectl get deployment "${app}-deployment" \
        -o jsonpath='{.spec.template.spec.containers[0].resources.requests.cpu}' 2>/dev/null || echo "")
  if [[ -z "${raw}" ]]; then
    echo 1000
    return
  fi

  if [[ "${raw}" == *m ]]; then
    echo "${raw%m}"
  else
    # 값이 1, 2 처럼 코어 단위일 때 1000*m 으로 변환
    echo $(( raw * 1000 ))
  fi
}

print_cpu_usage() {
  local app=$1
  local req_m
  req_m=$(get_cpu_request_m "${app}")

  echo "${app^} CPU 사용률 (요청 ${req_m}m = 100%)"

  # metrics-server 결과가 없을 수 있으므로 2>/dev/null 적용
  if ! kubectl top pods -l "app=${app}" --no-headers 2>/dev/null | awk -v req="${req_m}" '
    BEGIN {
      count = 0;
      sum = 0;
    }
    {
      cpu_col = $2;
      usage = cpu_col;
      gsub("m","",usage);
      if (cpu_col ~ /m$/) {
        usage_m = usage + 0;
      } else if (cpu_col ~ /n$/) {
        next; # ns 단위는 무시
      } else {
        usage_m = (usage + 0) * 1000;
      }
      printf "  %s\t%sm\t%.1f%%\n", $1, cpu_col, usage_m/req*100;
      sum += usage_m;
      count += 1;
    }
    END {
      if (count > 0) {
        printf "  평균\t\t%.1f%%\n", sum/count/req*100;
      } else {
        print "  (데이터 없음)";
      }
    }
  '; then
    echo "  (metrics 데이터 없음)"
  fi
}

print_counts() {
  echo "Backend Pods:"
  kubectl get pods -l app=backend -o wide --no-headers | awk '{print $7}' | sort | uniq -c | awk '{print $2 " backend=" $1}'
  
  echo "Frontend Pods:"
  kubectl get pods -l app=frontend -o wide --no-headers | awk '{print $7}' | sort | uniq -c | awk '{print $2 " frontend=" $1}'
}

echo "=== 장애 복구 시간 측정 ==="

echo "[Before] 노드별 Pod 개수"
print_counts
print_cpu_usage backend
print_cpu_usage frontend
echo

start_time=$(date +%s)

kubectl drain k8s-worker1 --ignore-daemonsets --delete-emptydir-data --force >/dev/null 2>&1
kubectl wait --for=condition=Ready pods --all --timeout=300s >/dev/null 2>&1

end_time=$(date +%s)
recovery_time=$((end_time - start_time))

kubectl uncordon k8s-worker1 >/dev/null 2>&1

echo "[After]  노드별 Pod 개수"
print_counts
print_cpu_usage backend
print_cpu_usage frontend
echo

echo "장애 복구 시간: ${recovery_time}초초"

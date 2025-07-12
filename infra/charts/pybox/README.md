# PyBox Helm Chart 배포 가이드

## 개요

이 Helm 차트는 FastAPI 기반의 PyBox 애플리케이션을 Kubernetes 클러스터에 배포하기 위한 것입니다.

## 전제 조건

- Kubernetes 클러스터 (1.19+)
- Helm 3.0+
- Docker 이미지가 빌드되어 있어야 함

## 디렉토리 구조

```
infra/helm/
├── Chart.yaml              # 차트 메타데이터
├── values.yaml             # 기본 설정값
├── templates/
│   ├── _helpers.tpl        # 헬퍼 템플릿
│   ├── configmap.yaml      # 애플리케이션 설정
│   ├── deployment.yaml     # 애플리케이션 배포
│   ├── service.yaml        # 서비스 노출
│   ├── serviceaccount.yaml # 서비스 계정
│   ├── ingress.yaml        # 외부 접근 (선택사항)
│   ├── hpa.yaml           # 자동 스케일링 (선택사항)
│   └── NOTES.txt          # 배포 후 안내사항
└── .helmignore            # Helm 패키징 시 제외할 파일
```

## 1. Docker 이미지 빌드

먼저 애플리케이션의 Docker 이미지를 빌드해야 합니다:

```bash
# 프로젝트 루트에서 실행
docker build -t pybox:latest .

# 또는 특정 태그로 빌드
docker build -t pybox:0.1.0 .
```

## 2. 기본 배포

### 로컬 개발 환경 배포

```bash
# Helm 차트 디렉토리로 이동
cd infra/helm

# 차트 유효성 검사
helm lint .

# 드라이 런 (실제 배포하지 않고 확인)
helm install pybox-dev . --dry-run --debug

# 실제 배포
helm install pybox-dev .
```

### 프로덕션 환경 배포

```bash
# 프로덕션용 values 파일 생성 후
helm install pybox-prod . -f values-prod.yaml
```

## 3. 설정 옵션

### 3.1 기본 애플리케이션 설정

```yaml
replicaCount: 2 # 파드 복제본 수

image:
  repository: pybox
  tag: "latest"
  pullPolicy: IfNotPresent

server:
  host: 0.0.0.0
  port: 8000
  allowed_ips:
    - 0.0.0.0/32
    - 0.0.0.1/32
```

### 3.2 서비스 설정

```yaml
service:
  type: ClusterIP # ClusterIP, NodePort, LoadBalancer
  port: 80
  targetPort: 8000
```

### 3.3 Ingress 설정 (외부 접근)

```yaml
ingress:
  enabled: true
  className: "nginx"
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: pybox.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: pybox-tls
      hosts:
        - pybox.yourdomain.com
```

### 3.4 자동 스케일링 설정

```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
  targetMemoryUtilizationPercentage: 80
```

### 3.5 리소스 제한

```yaml
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi
```

## 4. 배포 후 확인

### 4.1 배포 상태 확인

```bash
# 파드 상태 확인
kubectl get pods -l app.kubernetes.io/name=pybox

# 서비스 확인
kubectl get svc -l app.kubernetes.io/name=pybox

# 배포 상태 확인
kubectl get deployment -l app.kubernetes.io/name=pybox
```

### 4.2 애플리케이션 테스트

```bash
# 포트 포워딩을 통한 로컬 접근
kubectl port-forward svc/pybox-dev 8080:80

# 헬스 체크
curl http://localhost:8080/.health-check

# Echo 엔드포인트 테스트
curl "http://localhost:8080/echo?q=hello"
```

## 5. 업그레이드

### 5.1 이미지 업데이트

```bash
# 새로운 이미지 태그로 업그레이드
helm upgrade pybox-dev . --set image.tag=0.2.0

# values 파일을 이용한 업그레이드
helm upgrade pybox-dev . -f values-updated.yaml
```

### 5.2 설정 변경

```bash
# 복제본 수 변경
helm upgrade pybox-dev . --set replicaCount=5

# Ingress 활성화
helm upgrade pybox-dev . --set ingress.enabled=true
```

## 6. 롤백

```bash
# 이전 버전으로 롤백
helm rollback pybox-dev

# 특정 리비전으로 롤백
helm rollback pybox-dev 2

# 롤백 히스토리 확인
helm history pybox-dev
```

## 7. 삭제

```bash
# Helm 릴리스 삭제
helm uninstall pybox-dev

# 네임스페이스별 삭제 (필요한 경우)
helm uninstall pybox-dev -n production
```

## 8. 모니터링 및 로깅

### 8.1 로그 확인

```bash
# 파드 로그 확인
kubectl logs -f deployment/pybox-dev

# 특정 파드 로그 확인
kubectl logs -f <pod-name>
```

### 8.2 메트릭 확인

```bash
# 파드 리소스 사용량
kubectl top pods -l app.kubernetes.io/name=pybox

# 노드 리소스 사용량
kubectl top nodes
```

## 9. 트러블슈팅

### 9.1 일반적인 문제들

1. **이미지 풀 에러**: imagePullPolicy와 이미지 태그 확인
2. **헬스 체크 실패**: 포트 및 경로 설정 확인
3. **ConfigMap 마운트 실패**: 볼륨 마운트 경로 확인

### 9.2 디버깅 명령어

```bash
# 파드 상세 정보
kubectl describe pod <pod-name>

# 이벤트 확인
kubectl get events --sort-by=.metadata.creationTimestamp

# 서비스 엔드포인트 확인
kubectl get endpoints
```

## 10. 보안 고려사항

- ServiceAccount 사용으로 최소 권한 원칙 적용
- securityContext 설정으로 컨테이너 보안 강화
- NetworkPolicy 적용 고려 (별도 설정 필요)
- Secret을 통한 민감한 정보 관리

이 가이드를 통해 PyBox 애플리케이션을 안전하고 효율적으로 Kubernetes 환경에 배포할 수 있습니다.

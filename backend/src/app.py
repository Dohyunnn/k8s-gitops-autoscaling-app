# 주식 모니터링 백엔드 API
# 한국투자증권 KIS API를 사용한  Flask 서버
from flask import Flask, request, jsonify, g, Response
import socket
import time
import threading
import random
import requests
import os
from datetime import datetime, timedelta
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)


@app.before_request
def start_timer():
    """요청 시작 시각을 기록하여 응답 지연을 산출"""
    if request.path == '/metrics':
        return
    g.request_start_time = time.time()


@app.after_request
def record_request_metrics(response):
    """요청 건수 및 응답 시간을 Prometheus 메트릭으로 저장"""
    if request.path != '/metrics':
        elapsed = time.time() - getattr(g, 'request_start_time', time.time())
        endpoint = request.endpoint or request.path or 'unknown'
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(elapsed)
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code
        ).inc()
    return response


@app.route('/metrics')
def metrics():
    """Prometheus가 스크랩할 메트릭 엔드포인트"""
    SIMULATION_ACTIVE_GAUGE.set(1 if traffic_simulation_active else 0)
    EMERGENCY_MODE_GAUGE.set(1 if emergency_mode else 0)
    CURRENT_TRAFFIC_LEVEL_GAUGE.set(
        TRAFFIC_LEVEL_MAPPING.get(current_traffic_level, 0)
    )
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


# 전역 변수 - 트래픽 시뮬레이션 상태 관리
traffic_simulation_active = False      # 긴급/수동 시뮬레이션 활성화 여부
current_traffic_level = 'off'          # 현재 트래픽 레벨 (off/low/medium/high)
simulation_thread = None               # 시뮬레이션 스레드
simulation_stop_event = None           # 시뮬레이션 종료 이벤트
SIMULATION_ENABLED = os.getenv('SIMULATION_ENABLED', 'true').lower() == 'true'
emergency_mode = False                 # 긴급 상황 모드 여부
auto_mode_enabled = False              # 자동 모드 (비활성화 기본값)

# 기본 트래픽(OFF 상태) 유지를 위한 스레드 관리
baseline_thread = None
baseline_thread_lock = threading.Lock()
baseline_stop_event = threading.Event()

# 주식 데이터 관리 - 국내 주식 12개 (KIS API용)
stock_symbols = {
    '005380': '현대차',
    '000270': '기아',
    '005930': '삼성전자',
    '000660': 'SK하이닉스',
    '373220': 'LG에너지솔루션',
    '035420': 'NAVER',
    '012450': '한화에어로스페이스',
    '034020': '두산에너빌리티',
    '105560': 'KB금융',
    '042660': '한화오션',
    '032830': '삼성생명',
    '035720': '카카오'
}
previous_prices = {}  # 이전 가격 저장

# Prometheus 메트릭
REQUEST_COUNT = Counter(
    'backend_http_requests_total',
    'Total number of HTTP requests processed by the backend service',
    ['method', 'endpoint', 'status']
)
REQUEST_LATENCY = Histogram(
    'backend_http_request_latency_seconds',
    'Latency of HTTP requests processed by the backend service',
    ['endpoint']
)
SIMULATION_ACTIVE_GAUGE = Gauge(
    'backend_traffic_simulation_active',
    'Whether traffic simulation is active (1=active, 0=inactive)'
)
EMERGENCY_MODE_GAUGE = Gauge(
    'backend_traffic_emergency_mode',
    'Whether emergency mode is active (1=active, 0=inactive)'
)
CURRENT_TRAFFIC_LEVEL_GAUGE = Gauge(
    'backend_current_traffic_level',
    'Current traffic level encoded as 0=off, 1=low, 2=medium, 3=high'
)

TRAFFIC_LEVEL_MAPPING = {
    'off': 0,
    'low': 1,
    'medium': 2,
    'high': 3
}

# KIS API 클라이언트
class KISAPIClient:
    def __init__(self):
        self.app_key = os.getenv('KIS_APP_KEY')
        self.app_secret = os.getenv('KIS_APP_SECRET')
        self.access_token = None
        self.token_expires_at = None
    
    def get_access_token(self):
        """토큰 발급 및 자동 갱신"""
        # 토큰이 유효한지 확인
        if self.access_token and self.token_expires_at and self.token_expires_at > datetime.now():
            return self.access_token
        
        # 새 토큰 발급
        url = "https://openapi.koreainvestment.com:9443/oauth2/tokenP"
        data = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "Accept": "application/json"
        }
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            if not self.access_token:
                print(f"KIS API 토큰 응답에 access_token이 없습니다: {token_data}")
                return None
            
            # 24시간 후 만료
            self.token_expires_at = datetime.now() + timedelta(hours=24)
            
            print(f"KIS API 토큰 발급 성공: {self.access_token[:20]}...")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            print(f"KIS API 토큰 발급 실패: {e}")
            return None
    
    def get_stock_price(self, symbol):
        """주식 가격 조회"""
        token = self.get_access_token()
        if not token:
            return None
        
        url = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = {
            "Authorization": f"Bearer {token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "FHKST01010100",
            "custtype": os.getenv('KIS_CUST_TYPE', 'P'),
            "Content-Type": "application/json; charset=UTF-8",
            "Accept": "application/json"
        }
        
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": symbol
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            print(f"KIS API 응답 ({symbol}): {data}")  # 디버깅용
            
            if data.get('rt_cd') not in ('0', '00'):
                print(f"KIS API 오류 응답 ({symbol}): {data}")
                return None
            
            if 'output' in data:
                stock_info = data['output']
                # 현재가는 stck_prpr 필드에 있음
                price = stock_info.get('stck_prpr', None)
                if price:
                    return float(price)
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"KIS API 주식 가격 조회 실패 ({symbol}): {e}")
            return None

# KIS API 클라이언트 인스턴스
kis_client = KISAPIClient()

# 트래픽 프로파일 구성 - 각각 CPU 사용량을 유도하는 반복 횟수/휴식 간격
TRAFFIC_PROFILES = {
    'low': {'iterations': 35, 'range_limit': 450, 'sleep': 0.5},      # 약 10~15%
    'medium': {'iterations': 160, 'range_limit': 900, 'sleep': 0.12},  # 약 50~70%
    'high': {'iterations': 320, 'range_limit': 1600, 'sleep': 0.04},   # 약 80~95%
}
BASELINE_PROFILE = {'iterations': 70, 'range_limit': 520, 'sleep': 0.35}  # OFF 상태 약 20%

def _run_baseline_traffic(stop_event: threading.Event):
    """OFF 상태에서도 약간의 트래픽을 유지하여 기본 부하를 줌"""
    profile = BASELINE_PROFILE
    while not stop_event.is_set():
        for _ in range(profile['iterations']):
            sum(range(profile['range_limit']))
        time.sleep(profile['sleep'])

def ensure_baseline_running():
    """기본 트래픽 스레드를 한 번만 기동"""
    global baseline_thread
    with baseline_thread_lock:
        if baseline_thread and baseline_thread.is_alive():
            return
        if baseline_stop_event.is_set():
            baseline_stop_event.clear()
        baseline_thread = threading.Thread(
            target=_run_baseline_traffic,
            args=(baseline_stop_event,),
            daemon=True
        )
        baseline_thread.start()

def _run_traffic_simulation(level: str, stop_event: threading.Event):
    """긴급/수동 시뮬레이션 구간별 CPU 부하 생성"""
    profile = TRAFFIC_PROFILES.get(level)
    if not profile:
        return
    while not stop_event.is_set():
        for _ in range(profile['iterations']):
            sum(range(profile['range_limit']))
        time.sleep(profile['sleep'])

def stop_active_simulation():
    """현재 진행 중인 시뮬레이션을 종료하고 OFF 상태로 복귀"""
    global simulation_thread, simulation_stop_event, traffic_simulation_active, current_traffic_level, emergency_mode

    traffic_simulation_active = False
    emergency_mode = False

    if simulation_stop_event:
        simulation_stop_event.set()

    if simulation_thread and simulation_thread.is_alive():
        simulation_thread.join(timeout=1.0)

    simulation_thread = None
    simulation_stop_event = None
    current_traffic_level = 'off'

def start_simulation(level: str, emergency: bool = False):
    """지정된 트래픽 레벨로 새로운 시뮬레이션 시작"""
    global simulation_thread, simulation_stop_event, traffic_simulation_active, current_traffic_level, emergency_mode

    if level not in TRAFFIC_PROFILES:
        raise ValueError(f"Unsupported traffic level: {level}")

    stop_active_simulation()

    simulation_stop_event = threading.Event()
    current_traffic_level = level
    emergency_mode = emergency
    traffic_simulation_active = True
    
    if SIMULATION_ENABLED:
        ensure_baseline_running()

    simulation_thread = threading.Thread(
        target=_run_traffic_simulation,
        args=(level, simulation_stop_event),
        daemon=True
    )
    simulation_thread.start()


if SIMULATION_ENABLED:
    ensure_baseline_running()

# 긴급 상황별 트래픽 레벨 (3단계 + OFF 상태)
emergency_traffic_levels = {
    'system_error': 'low',          # 시스템 오류: 낮은 트래픽 (Pod 2개 유지)
    'massive_trading': 'medium',    # 대량 거래: 중간 트래픽 (Pod 6-10개)
    'emergency_news': 'high'        # 긴급 뉴스: 높은 트래픽 (Pod 12-15개)
}
# 기본 상태: 시뮬레이션 OFF 시 정상 운영 트래픽 (Pod 2-3개)

# 메인 페이지 - 서버 상태 표시
@app.route('/')
def home():

    return f'<h1>주식 모니터링 백엔드</h1><p>서버: {socket.gethostname()}</p><p>상태: 정상</p>'


# 헬스체크 엔드포인트 - Kubernetes liveness/readiness probe용
@app.route('/api/health')
def health():
    
    return {
        'status': 'ok',
        'service': 'backend',
        'hostname': socket.gethostname(),
        'timestamp': datetime.now().isoformat(),
        'traffic_simulation': traffic_simulation_active,
        'traffic_level': current_traffic_level
    }


# 트래픽 시뮬레이션 시작 API -프론트엔드에서 호출하여 HPA 테스트용 트래픽 생성
@app.route('/api/simulate-traffic', methods=['POST'])
def simulate_traffic_endpoint():
    if not SIMULATION_ENABLED:
        return jsonify({
            'success': False,
            'message': '트래픽 시뮬레이션이 비활성화된 상태입니다 (SIMULATION_ENABLED=false).'
        }), 503

    data = request.get_json(silent=True) or {}
    scenario = data.get('scenario', 'manual_trigger')
    traffic_level = (data.get('traffic_level') or '').lower()

    if traffic_level in ('off', 'normal', ''):
        stop_active_simulation()
        ensure_baseline_running()
        return jsonify({
            'success': True,
            'message': '트래픽 시뮬레이션이 OFF 상태로 전환되었습니다.',
            'scenario': scenario,
            'traffic_level': current_traffic_level,
            'timestamp': datetime.now().isoformat()
        })

    if traffic_level not in TRAFFIC_PROFILES:
        return jsonify({
            'success': False,
            'message': f'지원하지 않는 트래픽 레벨입니다: {traffic_level}',
            'timestamp': datetime.now().isoformat()
        }), 400

    ensure_baseline_running()
    start_simulation(traffic_level, emergency=False)

    return jsonify({
        'success': True,
        'message': f'트래픽 시뮬레이션 시작: {scenario}',
        'scenario': scenario,
        'traffic_level': traffic_level,
        'timestamp': datetime.now().isoformat()
    })

# 트래픽 시뮬레이션 중지 API
@app.route('/api/stop-simulation', methods=['POST'])
def stop_simulation():
    if not SIMULATION_ENABLED:
        return jsonify({
            'success': True,
            'message': '트래픽 시뮬레이션이 비활성화된 상태입니다.',
            'timestamp': datetime.now().isoformat()
        })

    stop_active_simulation()
    ensure_baseline_running()

    return jsonify({
        'success': True,
        'message': '트래픽 시뮬레이션 중지됨',
        'timestamp': datetime.now().isoformat()
    })

# 긴급 상황 시뮬레이션 API
@app.route('/api/emergency-simulation', methods=['POST'])
def emergency_simulation():
    if not SIMULATION_ENABLED:
        return jsonify({
            'success': False,
            'message': '긴급 시뮬레이션 기능이 비활성화된 상태입니다 (SIMULATION_ENABLED=false).',
            'timestamp': datetime.now().isoformat()
        }), 503

    data = request.get_json(silent=True) or {}
    emergency_type = data.get('emergency_type', 'emergency_news')

    if emergency_type not in emergency_traffic_levels:
        return jsonify({
            'success': False,
            'message': '알 수 없는 긴급 상황 타입',
            'timestamp': datetime.now().isoformat()
        }), 400

    traffic_level = emergency_traffic_levels[emergency_type]
    ensure_baseline_running()
    start_simulation(traffic_level, emergency=True)

    emergency_messages = {
        'emergency_news': '긴급 뉴스 발생 - 높은 트래픽 시뮬레이션',
        'massive_trading': '대량 거래 체결 - 중간 트래픽 시뮬레이션',
        'system_error': '시스템 오류 발생 - 낮은 트래픽 시뮬레이션'
    }

    return jsonify({
        'success': True,
        'message': emergency_messages.get(emergency_type, '긴급 상황 시뮬레이션 시작'),
        'emergency_type': emergency_type,
        'traffic_level': traffic_level,
        'timestamp': datetime.now().isoformat()
    })

# 자동 모드 토글 API
@app.route('/api/toggle-auto-mode', methods=['POST'])
def toggle_auto_mode():
    if not SIMULATION_ENABLED:
        return jsonify({
            'success': False,
            'message': '자동 모드 토글이 비활성화된 상태입니다 (SIMULATION_ENABLED=false).',
            'timestamp': datetime.now().isoformat()
        }), 503

    global auto_mode_enabled

    auto_mode_enabled = False

    return jsonify({
        'success': False,
        'message': '자동 모드는 현재 지원되지 않습니다. 수동 버튼을 사용해주세요.',
        'auto_mode_enabled': auto_mode_enabled,
        'timestamp': datetime.now().isoformat()
    }), 400

# 트래픽 시뮬레이션 상태 조회 API
@app.route('/api/simulation-status', methods=['GET'])
def get_simulation_status():
    baseline_running = baseline_thread is not None and baseline_thread.is_alive() and not baseline_stop_event.is_set()

    return jsonify({
        'active': traffic_simulation_active,
        'traffic_level': current_traffic_level,
        'emergency_mode': emergency_mode,
        'auto_mode_enabled': False,
        'baseline_active': baseline_running,
        'current_time': datetime.now().strftime('%H:%M:%S'),
        'timestamp': datetime.now().isoformat()
    })



# 주식 가격 조회 함수 (KIS API + 폴백)
def get_real_stock_price(symbol):
    """KIS API를 사용하여 실제 주식 가격 조회"""
    try:
        # KIS API로 주식 가격 조회 시도
        price = kis_client.get_stock_price(symbol)
        if price:
            return price
        
        # KIS API 실패 시 폴백: 모의 데이터 사용
        print(f"KIS API 실패, 모의 데이터 사용: {symbol}")
        fallback_prices = {
            '005380': 252000,   # 현대차
            '000270': 98000,    # 기아
            '005930': 57900,    # 삼성전자
            '000660': 135000,   # SK하이닉스
            '373220': 420000,   # LG에너지솔루션
            '035420': 210000,   # NAVER
            '012450': 180000,   # 한화에어로스페이스
            '034020': 18500,    # 두산에너빌리티
            '105560': 68000,    # KB금융
            '042660': 35000,    # 한화오션
            '032830': 98000,    # 삼성생명
            '035720': 45000     # 카카오
        }
        base_price = fallback_prices.get(symbol, 50000.0)
        return base_price + random.uniform(-base_price * 0.02, base_price * 0.02)
            
    except Exception as e:
        print(f"주식 가격 조회 오류 ({symbol}): {e}")
        # 오류 시 기본 모의 데이터 반환
        base_prices = {
            '005380': 252000,
            '000270': 98000,
            '005930': 57900,
            '000660': 135000,
            '373220': 420000,
            '035420': 210000,
            '012450': 180000,
            '034020': 18500,
            '105560': 68000,
            '042660': 35000,
            '032830': 98000,
            '035720': 45000
        }
        base_price = base_prices.get(symbol, 50000.0)
        return base_price + random.uniform(-base_price * 0.02, base_price * 0.02)

def calculate_price_change(symbol, current_price):
    """가격 변동률 계산"""
    global previous_prices
    
    if symbol in previous_prices:
        previous_price = previous_prices[symbol]
        change_percent = ((current_price - previous_price) / previous_price) * 100
    else:
        change_percent = 0.0
    
    previous_prices[symbol] = current_price
    return change_percent

def adjust_traffic_by_price_change(symbol, price_change):
    """가격 변동률에 따른 트래픽 조절 (자동 모드일 때만 작동)"""
    global auto_mode_enabled

    # 자동 모드가 아니거나 긴급 모드일 때는 가격 변동 무시
    if not (auto_mode_enabled and SIMULATION_ENABLED) or emergency_mode:
        return
    
    abs_change = abs(price_change)
    
    # 가격 변동률에 따른 트래픽 레벨 결정
    if abs_change >= 10:  # 10% 이상 변동
        new_traffic_level = 'high'
    elif abs_change >= 5:  # 5~10% 변동
        new_traffic_level = 'medium'
    else:  # 5% 미만 변동
        return  # 시간 기반 자동 모드 유지
    
    # 트래픽 레벨이 변경된 경우에만 시뮬레이션 재시작
    if new_traffic_level != current_traffic_level:
        start_simulation(new_traffic_level, emergency=False)
        print(f"[가격 변동 감지 - 자동 모드] {symbol}: {price_change:+.2f}% → 트래픽 레벨: {new_traffic_level}")

# 실제 주식 데이터 API
@app.route('/api/stock-data')
def get_stock_data():
    """실제 주식 가격 데이터 조회"""
    stocks = []
    
    for symbol, name in stock_symbols.items():
        try:
            current_price = get_real_stock_price(symbol)
            price_change = calculate_price_change(symbol, current_price)
            
            # 가격 변동률에 따른 트래픽 조절 (자동 모드일 때만)
            adjust_traffic_by_price_change(symbol, price_change)
            
            stocks.append({
                'symbol': symbol,
                'name': name,
                'price': round(current_price, 2),
                'change': round(price_change, 2),
                'change_percent': round(price_change, 2)
            })
            
        except Exception as e:
            print(f"주식 데이터 처리 오류 ({symbol}): {e}")
            stocks.append({
                'symbol': symbol,
                'name': name,
                'price': 0.0,
                'change': 0.0,
                'change_percent': 0.0,
                'error': str(e)
            })
    
    return jsonify({
        'stocks': stocks,
        'timestamp': datetime.now().isoformat(),
        'market_status': 'open' if 9 <= datetime.now().hour < 15 else 'closed',
        'traffic_level': current_traffic_level,
        'traffic_simulation': traffic_simulation_active
    })

# 개별 주식 가격 조회 API
@app.route('/api/stock-price/<symbol>')
def get_stock_price(symbol):
    """개별 주식 가격 조회"""
    try:
        if symbol not in stock_symbols:
            return jsonify({'error': 'Unknown symbol'}), 400
        
        current_price = get_real_stock_price(symbol)
        price_change = calculate_price_change(symbol, current_price)
        
        # 가격 변동률에 따른 자동 트래픽 조절 제거됨
        
        return jsonify({
            'symbol': symbol,
            'name': stock_symbols[symbol],
            'price': round(current_price, 2),
            'change': round(price_change, 2),
            'change_percent': round(price_change, 2),
            'timestamp': datetime.now().isoformat(),
            'traffic_level': current_traffic_level
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("주식 모니터링 백엔드 서버 시작 (KIS API 사용)")
    print("API 엔드포인트:")
    print("- GET  /api/health                # 헬스체크")
    print("- POST /api/simulate-traffic      # 트래픽 시뮬레이션")
    print("- GET  /api/stock-data            # 주식 데이터 (KIS API)")
    print("- POST /api/emergency-simulation  # 긴급 상황 시뮬레이션")
    print("- POST /api/stop-simulation       # 시뮬레이션 중지")
    print("- GET  /api/simulation-status     # 시뮬레이션 상태")
    print("한국투자증권 KIS API를 사용한 가벼운 백엔드")
    
    # KIS API 키 확인
    if kis_client.app_key and kis_client.app_secret:
        print(f"\nKIS API 키 설정됨: {kis_client.app_key[:10]}...")
        # 초기 토큰 발급 테스트
        token = kis_client.get_access_token()
        if token:
            print("KIS API 토큰 발급 성공")
        else:
            print("KIS API 토큰 발급 실패 - 모의 데이터 사용")
    else:
        print("\nKIS API 키가 설정되지 않음 - 모의 데이터 사용")
        print("환경변수 KIS_APP_KEY, KIS_APP_SECRET 설정 필요")
    
    # 시뮬레이션은 버튼 클릭 시에만 시작 (자동 시작 안 함)
    print("\n시뮬레이션 대기 중 (버튼 클릭 시 시작)")
    
    app.run(host='0.0.0.0', port=8081, debug=True)

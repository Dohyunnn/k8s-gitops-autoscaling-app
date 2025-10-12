# 주식 모니터링 백엔드 API
# 한국투자증권 KIS API를 사용한  Flask 서버
from flask import Flask, request, jsonify
import socket
import time
import threading
import random
import requests
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# 전역 변수 - 트래픽 시뮬레이션 상태 관리
traffic_simulation_active = False  # 시뮬레이션 활성화 여부
current_traffic_level = 'normal'   # 현재 트래픽 레벨 (high/medium/low/normal)
simulation_thread = None           # 시뮬레이션 스레드
SIMULATION_ENABLED = os.getenv('SIMULATION_ENABLED', 'true').lower() == 'true'
auto_mode_enabled = SIMULATION_ENABLED  # 자동 모드 활성화 여부
emergency_mode = False             # 긴급 상황 모드 여부

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
        
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            
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
            "tr_id": "FHKST01010100"
        }
        
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": symbol
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            if 'output' in data and len(data['output']) > 0:
                stock_info = data['output'][0]
                return float(stock_info['stck_prpr'])  # 현재가
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"KIS API 주식 가격 조회 실패 ({symbol}): {e}")
            return None

# KIS API 클라이언트 인스턴스
kis_client = KISAPIClient()

# 자동 시간 기반 트래픽 레벨 결정
def get_auto_traffic_level():
    """현재 시간에 따른 자동 트래픽 레벨 결정"""
    now = datetime.now()
    hour = now.hour
    
    # 한국 시간 기준 (UTC+9)
    if 9 <= hour < 15:  # 장 시작 시간 (09:00-15:00)
        return 'high'
    elif 15 <= hour < 18:  # 장 종료 시간 (15:00-18:00)
        return 'medium'
    else:  # 야간 시간 (18:00-09:00)
        return 'low'

# 긴급 상황별 트래픽 레벨 (3단계)
emergency_traffic_levels = {
    'system_error': 'minimal',      # 시스템 오류: 최소 트래픽 (Pod 1-2개)
    'massive_trading': 'medium',    # 대량 거래: 중간 트래픽 (Pod 6-10개)
    'emergency_news': 'high'        # 긴급 뉴스: 높은 트래픽 (Pod 12-15개)
}
# 일반 상태(low): 시뮬레이션이 OFF일 때의 기본 상태 (Pod 2-3개)

# 트래픽 시뮬레이션 함수 -HPA 테스트를 위해 CPU 사용률을 인위적으로 증가시킴
def simulate_traffic():
    global traffic_simulation_active, current_traffic_level, auto_mode_enabled, emergency_mode
    
    while traffic_simulation_active:
        # 자동 모드가 활성화되고 긴급 상황이 아닐 때만 시간 기반 트래픽 적용
        if auto_mode_enabled and not emergency_mode:
            current_traffic_level = get_auto_traffic_level()
        
        if current_traffic_level == 'minimal':
            # 최소 트래픽 (시스템 오류) - Pod 1-2개 목표
            for _ in range(5):
                sum(range(50))
            time.sleep(2.0)  # 2초 간격으로 매우 느린 반복
            
        elif current_traffic_level == 'low':
            # 낮은 트래픽 (일반 모드) - Pod 2-4개 목표
            for _ in range(15):
                sum(range(150))
            time.sleep(0.8)  # 800ms 간격
            
        elif current_traffic_level == 'medium':
            # 중간 트래픽 (대량 거래) - Pod 6-10개 목표
            for _ in range(80):
                sum(range(800))
            time.sleep(0.15)  # 150ms 간격
            
        elif current_traffic_level == 'high':
            # 높은 트래픽 (긴급 뉴스) - Pod 12-15개 목표
            for _ in range(150):
                sum(range(2000))
            time.sleep(0.05)  # 50ms 간격으로 매우 빠른 반복
        
        else:
            # 기본 상태: 대기
            time.sleep(1.0)

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

    global traffic_simulation_active, current_traffic_level, simulation_thread
    
    data = request.get_json()
    scenario = data.get('scenario', 'normal')      # 시나리오 (market_open, market_close, night_mode)
    traffic_level = data.get('traffic_level', 'normal')  # 트래픽 레벨 (high, medium, low)
    
    # 기존 시뮬레이션 중지
    traffic_simulation_active = False
    if simulation_thread:
        simulation_thread.join()
    
    # 새 시뮬레이션 시작
    current_traffic_level = traffic_level
    traffic_simulation_active = True
    simulation_thread = threading.Thread(target=simulate_traffic)
    simulation_thread.daemon = True
    simulation_thread.start()
    
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

    global traffic_simulation_active, simulation_thread, emergency_mode
    
    traffic_simulation_active = False
    emergency_mode = False
    if simulation_thread:
        simulation_thread.join()
    
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

    global traffic_simulation_active, current_traffic_level, simulation_thread, emergency_mode, auto_mode_enabled
    
    data = request.get_json()
    emergency_type = data.get('emergency_type', 'emergency_news')
    
    # 긴급 상황별 트래픽 레벨 설정
    if emergency_type in emergency_traffic_levels:
        current_traffic_level = emergency_traffic_levels[emergency_type]
        emergency_mode = True
        auto_mode_enabled = False  # 긴급 상황 시 자동 모드 비활성화
        
        # 기존 시뮬레이션 중지
        traffic_simulation_active = False
        if simulation_thread:
            simulation_thread.join()
        
        # 새 시뮬레이션 시작
        traffic_simulation_active = True
        simulation_thread = threading.Thread(target=simulate_traffic)
        simulation_thread.daemon = True
        simulation_thread.start()
        
        emergency_messages = {
            'emergency_news': '긴급 뉴스 발생 - 높은 트래픽 시뮬레이션',
            'massive_trading': '대량 거래 체결 - 높은 트래픽 시뮬레이션',
            'system_error': '시스템 오류 발생 - 중간 트래픽 시뮬레이션'
        }
        
        return jsonify({
            'success': True,
            'message': emergency_messages.get(emergency_type, '긴급 상황 시뮬레이션 시작'),
            'emergency_type': emergency_type,
            'traffic_level': current_traffic_level,
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({
            'success': False,
            'message': '알 수 없는 긴급 상황 타입',
            'timestamp': datetime.now().isoformat()
        }), 400

# 자동 모드 토글 API
@app.route('/api/toggle-auto-mode', methods=['POST'])
def toggle_auto_mode():
    if not SIMULATION_ENABLED:
        return jsonify({
            'success': False,
            'message': '자동 모드 토글이 비활성화된 상태입니다 (SIMULATION_ENABLED=false).',
            'timestamp': datetime.now().isoformat()
        }), 503

    global auto_mode_enabled, emergency_mode, traffic_simulation_active, simulation_thread
    
    auto_mode_enabled = not auto_mode_enabled
    
    if auto_mode_enabled:
        emergency_mode = False
        # 자동 모드 활성화 시 시뮬레이션 재시작
        traffic_simulation_active = False
        if simulation_thread:
            simulation_thread.join()
        
        traffic_simulation_active = True
        simulation_thread = threading.Thread(target=simulate_traffic)
        simulation_thread.daemon = True
        simulation_thread.start()
    
    return jsonify({
        'success': True,
        'message': f'자동 모드 {"활성화" if auto_mode_enabled else "비활성화"}됨',
        'auto_mode_enabled': auto_mode_enabled,
        'timestamp': datetime.now().isoformat()
    })

# 트래픽 시뮬레이션 상태 조회 API
@app.route('/api/simulation-status', methods=['GET'])
def get_simulation_status():
    return jsonify({
        'active': traffic_simulation_active,
        'traffic_level': current_traffic_level,
        'auto_mode_enabled': auto_mode_enabled and SIMULATION_ENABLED,
        'emergency_mode': emergency_mode,
        'current_time': datetime.now().strftime('%H:%M:%S'),
        'auto_traffic_level': get_auto_traffic_level() if auto_mode_enabled and SIMULATION_ENABLED else None,
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
    global traffic_simulation_active, current_traffic_level, simulation_thread, auto_mode_enabled, emergency_mode
    
    # 자동 모드가 아니거나 긴급 모드일 때는 가격 변동 무시
    if not auto_mode_enabled or emergency_mode:
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
        current_traffic_level = new_traffic_level
        
        # 기존 시뮬레이션 중지
        traffic_simulation_active = False
        if simulation_thread:
            simulation_thread.join(timeout=1)
        
        # 새 시뮬레이션 시작
        traffic_simulation_active = True
        simulation_thread = threading.Thread(target=simulate_traffic)
        simulation_thread.daemon = True
        simulation_thread.start()
        
        print(f"[가격 변동 감지] {symbol}: {price_change:+.2f}% → 트래픽 레벨: {new_traffic_level}")

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
        
        # 가격 변동률에 따른 트래픽 조절
        adjust_traffic_by_price_change(symbol, price_change)
        
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
    print("- POST /api/toggle-auto-mode      # 자동 모드 토글")
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
    
    # 자동 모드로 트래픽 시뮬레이션 시작
    if SIMULATION_ENABLED:
        print("\n자동 트래픽 모드 시작 (시간 기반)")
        traffic_simulation_active = True
        simulation_thread = threading.Thread(target=simulate_traffic)
        simulation_thread.daemon = True
        simulation_thread.start()
    else:
        print("\n자동 트래픽 시뮬레이션이 비활성화되어 시작되지 않습니다 (SIMULATION_ENABLED=false).")
    
    app.run(host='0.0.0.0', port=8081, debug=True)

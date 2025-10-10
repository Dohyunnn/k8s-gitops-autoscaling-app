# 주식 모니터링 백엔드 API
# 트래픽 시뮬레이션과 자동 스케일링 테스트를 위한 Flask 서버
from flask import Flask, request, jsonify
import socket
import time
import threading
import random
import requests
import os
from datetime import datetime

app = Flask(__name__)

# 전역 변수 - 트래픽 시뮬레이션 상태 관리
traffic_simulation_active = False  # 시뮬레이션 활성화 여부
current_traffic_level = 'normal'   # 현재 트래픽 레벨 (high/medium/low/normal)
simulation_thread = None           # 시뮬레이션 스레드

# 주식 데이터 관리
stock_symbols = {
    'AAPL': 'Apple Inc.',
    'GOOGL': 'Alphabet Inc.',
    'TSLA': 'Tesla Inc.',
    '005930.KS': 'Samsung Electronics',
    '005380.KS': 'Hyundai Motor'
}
previous_prices = {}  # 이전 가격 저장
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')  # 환경변수에서 API 키 가져오기

# 트래픽 시뮬레이션 함수 -HPA 테스트를 위해 CPU 사용률을 인위적으로 증가시킴
def simulate_traffic():

    global traffic_simulation_active, current_traffic_level
    
    while traffic_simulation_active:
        if current_traffic_level == 'high':
            # 장 시작 시뮬레이션: 높은 트래픽 (1000+ 요청/분)
            for _ in range(100):
                # CPU 집약적 작업으로 HPA 트리거 유도
                sum(range(1000))
            time.sleep(0.1)  # 100ms 간격으로 빠른 반복
            
        elif current_traffic_level == 'medium':
            # 장 종료 시뮬레이션: 중간 트래픽 (100 요청/분)
            for _ in range(50):
                sum(range(500))
            time.sleep(0.2)  # 200ms 간격
            
        elif current_traffic_level == 'low':
            # 야간 모드: 낮은 트래픽 (10 요청/분)
            for _ in range(10):
                sum(range(100))
            time.sleep(1.0)  # 1초 간격으로 느린 반복
        
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

    global traffic_simulation_active, simulation_thread
    
    traffic_simulation_active = False
    if simulation_thread:
        simulation_thread.join()
    
    return jsonify({
        'success': True,
        'message': '트래픽 시뮬레이션 중지됨',
        'timestamp': datetime.now().isoformat()
    })



# 실제 주식 가격 조회 함수
def get_real_stock_price(symbol):
    """Alpha Vantage API를 사용하여 실제 주식 가격 조회"""
    try:
        if ALPHA_VANTAGE_API_KEY == 'demo':
            # 데모 모드: 랜덤 가격 반환
            base_prices = {
                'AAPL': 150.25,
                'GOOGL': 2800.50,
                'TSLA': 800.00,
                '005930.KS': 75000,
                '005380.KS': 250000
            }
            base_price = base_prices.get(symbol, 100.0)
            return base_price + random.uniform(-base_price * 0.05, base_price * 0.05)
        
        # 실제 API 호출
        url = f"https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'Global Quote' in data:
            price = float(data['Global Quote']['05. price'])
            return price
        else:
            # API 오류 시 데모 데이터 반환
            return get_real_stock_price('AAPL')  # 재귀 호출로 데모 모드 사용
            
    except Exception as e:
        print(f"주식 가격 조회 오류 ({symbol}): {e}")
        # 오류 시 데모 데이터 반환
        base_prices = {
            'AAPL': 150.25,
            'GOOGL': 2800.50,
            'TSLA': 800.00,
            '005930.KS': 75000,
            '005380.KS': 250000
        }
        base_price = base_prices.get(symbol, 100.0)
        return base_price + random.uniform(-base_price * 0.05, base_price * 0.05)

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
    """가격 변동률에 따른 트래픽 조절"""
    global traffic_simulation_active, current_traffic_level, simulation_thread
    
    # 종목별 특성 반영
    if symbol == 'TSLA':  # 테슬라는 변동성이 크므로 더 민감하게
        threshold_high = 8
        threshold_medium = 4
    elif symbol == 'AAPL':  # 애플은 안정적이므로 덜 민감하게
        threshold_high = 10
        threshold_medium = 6
    else:  # 나머지는 표준
        threshold_high = 10
        threshold_medium = 5
    
    abs_change = abs(price_change)
    
    if abs_change > threshold_high:
        new_traffic_level = 'high'
    elif abs_change > threshold_medium:
        new_traffic_level = 'medium'
    else:
        new_traffic_level = 'normal'
    
    # 트래픽 레벨이 변경된 경우에만 시뮬레이션 시작
    if new_traffic_level != current_traffic_level:
        current_traffic_level = new_traffic_level
        traffic_simulation_active = True
        
        if simulation_thread:
            simulation_thread.join()
        
        simulation_thread = threading.Thread(target=simulate_traffic)
        simulation_thread.daemon = True
        simulation_thread.start()
        
        print(f"주식 가격 변동 감지: {symbol} {price_change:.2f}% → 트래픽 {new_traffic_level}")

# 실제 주식 데이터 API
@app.route('/api/stock-data')
def get_stock_data():
    """실제 주식 가격 데이터 조회"""
    stocks = []
    
    for symbol, name in stock_symbols.items():
        try:
            current_price = get_real_stock_price(symbol)
            price_change = calculate_price_change(symbol, current_price)
            
            # 가격 변동률에 따른 트래픽 조절
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
    print("주식 모니터링 백엔드 서버 시작")
    print("API 엔드포인트:")
    print("- GET  /api/health           # 헬스체크")
    print("- POST /api/simulate-traffic  # 트래픽 시뮬레이션")
    print("- GET  /api/stock-data        # 주식 데이터")
    print("- POST /api/stop-simulation   # 시뮬레이션 중지")
    print("HPA 테스트를 위한 트래픽 시뮬레이션 기능 포함")
    
    app.run(host='0.0.0.0', port=8081, debug=True)


# 주식 모니터링 백엔드 API
# 트래픽 시뮬레이션과 자동 스케일링 테스트를 위한 Flask 서버
from flask import Flask, request, jsonify
import socket
import time
import threading
import random
from datetime import datetime

app = Flask(__name__)

# 전역 변수 - 트래픽 시뮬레이션 상태 관리
traffic_simulation_active = False  # 시뮬레이션 활성화 여부
current_traffic_level = 'normal'   # 현재 트래픽 레벨 (high/medium/low/normal)
simulation_thread = None           # 시뮬레이션 스레드

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



# 주식 데이터 API (시뮬레이션) - 실제 주식 API 연동 전까지 테스트용 데이터 제공
@app.route('/api/stock-data')
def get_stock_data():
    
    stocks = [
        {'symbol': 'AAPL', 'price': 150.25 + random.uniform(-5, 5), 'change': random.uniform(-2, 2)},
        {'symbol': 'GOOGL', 'price': 2800.50 + random.uniform(-10, 10), 'change': random.uniform(-3, 3)},
        {'symbol': 'MSFT', 'price': 350.75 + random.uniform(-8, 8), 'change': random.uniform(-2.5, 2.5)},
        {'symbol': 'TSLA', 'price': 800.00 + random.uniform(-20, 20), 'change': random.uniform(-5, 5)},
    ]
    
    return jsonify({
        'stocks': stocks,
        'timestamp': datetime.now().isoformat(),
        'market_status': 'open' if 9 <= datetime.now().hour < 15 else 'closed'  # 한국 시간 기준
    })

if __name__ == '__main__':
    print("주식 모니터링 백엔드 서버 시작")
    print("API 엔드포인트:")
    print("- GET  /api/health           # 헬스체크")
    print("- POST /api/simulate-traffic  # 트래픽 시뮬레이션")
    print("- GET  /api/stock-data        # 주식 데이터")
    print("- POST /api/stop-simulation   # 시뮬레이션 중지")
    print("HPA 테스트를 위한 트래픽 시뮬레이션 기능 포함")
    
    app.run(host='0.0.0.0', port=8081, debug=True)


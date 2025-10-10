// 주식 모니터링 대시보드 프론트엔드 서버
// Express 기반 웹 서버로 트래픽 시뮬레이션 UI 제공
const express = require('express');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 3001;

// JSON 파싱 미들웨어
app.use(express.json());

// 정적 파일 서빙 (HTML, CSS, JS)
app.use(express.static(path.join(__dirname)));

// 메인 페이지 - 주식 모니터링 대시보드
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// 헬스체크 엔드포인트 - Kubernetes liveness/readiness probe용
app.get('/api/health', async (req, res) => {
    try {
        // 백엔드 헬스체크도 함께 확인 (타임아웃 설정)
        const backendUrl = process.env.BACKEND_URL || 'http://backend-service:8081';
        const backendHealth = await axios.get(`${backendUrl}/api/health`, {
            timeout: 5000,  // 5초 타임아웃
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        res.json({
            status: 'ok',
            service: 'frontend',
            backend: backendHealth.data,
            timestamp: new Date().toISOString(),
            uptime: process.uptime()
        });
    } catch (error) {
        console.error('백엔드 헬스체크 오류:', error.message);
        res.json({
            status: 'partial',
            service: 'frontend',
            backend: { 
                status: 'error', 
                message: `백엔드 연결 실패: ${error.message}`,
                code: error.code || 'UNKNOWN'
            },
            timestamp: new Date().toISOString(),
            uptime: process.uptime()
        });
    }
});

// 트래픽 시뮬레이션 API (백엔드로 프록시)
const axios = require('axios');

app.post('/api/simulate-traffic', async (req, res) => {
    console.log('트래픽 시뮬레이션 요청:', req.body);
    
    try {
        // 백엔드 서비스로 프록시
        const backendUrl = process.env.BACKEND_URL || 'http://backend-service:8081';
        const response = await axios.post(`${backendUrl}/api/simulate-traffic`, req.body);
        
        res.json(response.data);
    } catch (error) {
        console.error('백엔드 연결 오류:', error.message);
        res.status(500).json({
            success: false,
            message: '백엔드 서버 연결 실패',
            error: error.message
        });
    }
});

// 주식 데이터 API (백엔드로 프록시)
app.get('/api/stock-data', async (req, res) => {
    try {
        const backendUrl = process.env.BACKEND_URL || 'http://backend-service:8081';
        const response = await axios.get(`${backendUrl}/api/stock-data`, {
            timeout: 10000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        res.json(response.data);
    } catch (error) {
        console.error('주식 데이터 조회 오류:', error.message);
        res.status(500).json({
            error: 'Stock data fetch failed',
            message: '주식 데이터를 가져올 수 없습니다.',
            details: error.message
        });
    }
});

// 개별 주식 가격 조회 API (백엔드로 프록시)
app.get('/api/stock-price/:symbol', async (req, res) => {
    try {
        const { symbol } = req.params;
        const backendUrl = process.env.BACKEND_URL || 'http://backend-service:8081';
        const response = await axios.get(`${backendUrl}/api/stock-price/${symbol}`, {
            timeout: 10000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        res.json(response.data);
    } catch (error) {
        console.error('개별 주식 가격 조회 오류:', error.message);
        res.status(500).json({
            error: 'Stock price fetch failed',
            message: '주식 가격을 가져올 수 없습니다.',
            details: error.message
        });
    }
});

// 트래픽 시뮬레이션 상태 API (백엔드로 프록시)
app.get('/api/simulation-status', async (req, res) => {
    try {
        const backendUrl = process.env.BACKEND_URL || 'http://backend-service:8081';
        const response = await axios.get(`${backendUrl}/api/simulation-status`, {
            timeout: 10000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        res.json(response.data);
    } catch (error) {
        console.error('시뮬레이션 상태 조회 오류:', error.message);
        res.status(500).json({
            error: 'Simulation status fetch failed',
            message: '시뮬레이션 상태를 가져올 수 없습니다.',
            details: error.message
        });
    }
});

// 자동 모드 토글 API (백엔드로 프록시)
app.post('/api/toggle-auto-mode', async (req, res) => {
    try {
        const backendUrl = process.env.BACKEND_URL || 'http://backend-service:8081';
        const response = await axios.post(`${backendUrl}/api/toggle-auto-mode`, {}, {
            timeout: 10000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        res.json(response.data);
    } catch (error) {
        console.error('자동 모드 토글 오류:', error.message);
        res.status(500).json({
            error: 'Auto mode toggle failed',
            message: '자동 모드 토글에 실패했습니다.',
            details: error.message
        });
    }
});

// 긴급 상황 시뮬레이션 API (백엔드로 프록시)
app.post('/api/emergency-simulation', async (req, res) => {
    try {
        const backendUrl = process.env.BACKEND_URL || 'http://backend-service:8081';
        const response = await axios.post(`${backendUrl}/api/emergency-simulation`, req.body, {
            timeout: 10000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        res.json(response.data);
    } catch (error) {
        console.error('긴급 상황 시뮬레이션 오류:', error.message);
        res.status(500).json({
            error: 'Emergency simulation failed',
            message: '긴급 상황 시뮬레이션에 실패했습니다.',
            details: error.message
        });
    }
});

// 트래픽 시뮬레이션 중지 API (백엔드로 프록시)
app.post('/api/stop-simulation', async (req, res) => {
    try {
        const backendUrl = process.env.BACKEND_URL || 'http://backend-service:8081';
        const response = await axios.post(`${backendUrl}/api/stop-simulation`, {}, {
            timeout: 10000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        res.json(response.data);
    } catch (error) {
        console.error('시뮬레이션 중지 오류:', error.message);
        res.status(500).json({
            error: 'Simulation stop failed',
            message: '시뮬레이션 중지에 실패했습니다.',
            details: error.message
        });
    }
});

// 404 에러 처리
app.use((req, res) => {
    res.status(404).json({
        error: 'Not Found',
        message: '요청한 리소스를 찾을 수 없습니다.'
    });
});

// 서버 시작
app.listen(PORT, '0.0.0.0', () => {
    console.log(`프론트엔드 서버가 포트 ${PORT}에서 실행 중입니다.`);
    console.log(`대시보드: http://localhost:${PORT}`);
    console.log(`HPA 테스트용 트래픽 시뮬레이션 UI 제공`);
});

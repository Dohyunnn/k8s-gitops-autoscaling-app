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
        const backendUrl = process.env.BACKEND_URL || 'http://localhost:8081';
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
        const backendUrl = process.env.BACKEND_URL || 'http://localhost:8081';
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

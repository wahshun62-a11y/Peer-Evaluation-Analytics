"""
config.py — 전체 설정값을 한 곳에서 관리합니다.
Why: 하드코딩된 경로/상수를 분산시키면 유지보수가 어려워지므로 중앙 집중 관리합니다.
"""
import os

# 데이터 디렉토리 경로
DATA_DIR = os.environ.get(
    "DATA_DIR",
    r"D:\CodingSpace\동료평가\00. Data"
)

# 프론트엔드 디렉토리 (정적 파일 서빙용)
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

# 조직별 시각화 색상 팔레트
COLORS = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
    '#FFEEAD', '#D4A5A5', '#9B59B6', '#3498DB',
    '#E67E22', '#1ABC9C', '#E74C3C', '#2ECC71',
]

# 분석 가능 연도 범위
AVAILABLE_YEARS = list(range(2025, 2016, -1))

# 개인 지표 Top N% 기준
TOP_PERCENT = 0.10  # 10%

# Betweenness Centrality 샘플링 임계값 (노드 수 초과 시 샘플링)
BETWEENNESS_SAMPLING_THRESHOLD = 500
BETWEENNESS_SAMPLE_SIZE = 100

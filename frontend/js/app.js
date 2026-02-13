/**
 * app.js — 앱 초기화 및 이벤트 조율 (메인 컨트롤러)
 */
document.addEventListener('DOMContentLoaded', () => {

    // ── 상태 관리 ──
    let currentFilters = null;
    let cachedData = {
        network: null,
        orgMetrics: null,
        individualMetrics: null,
        feedbackMetrics: null,
    };

    // ── DOM 참조 ──
    const btnAnalyze = document.getElementById('btn-analyze');
    const btnReset = document.getElementById('btn-reset');
    const placeholder = document.getElementById('placeholder');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const disclaimer = document.getElementById('disclaimer');
    const sidebarSummary = document.getElementById('sidebar-summary');
    const tabNav = document.getElementById('tab-nav');

    // ── 초기화 ──
    initApp();

    async function initApp() {
        const defaultYears = [2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017];
        await Filters.init(defaultYears);
        bindEvents();
    }

    function bindEvents() {
        btnAnalyze.addEventListener('click', runAnalysis);

        // ★ 필터 리셋 버튼
        btnReset.addEventListener('click', () => {
            Filters.reset();
            cachedData = { network: null, orgMetrics: null, individualMetrics: null, feedbackMetrics: null };
            results.style.display = 'none';
            disclaimer.style.display = 'none';
            placeholder.style.display = 'flex';
            sidebarSummary.style.display = 'none';
            if (tabNav) tabNav.style.display = 'none';
        });

        // 탭 네비게이션
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => switchTab(e.target.dataset.tab));
        });

        // 하위 조직 비교 기준 변경
        document.querySelectorAll('input[name="subgroup-level"]').forEach(radio => {
            radio.addEventListener('change', () => {
                if (currentFilters) loadSubgroupMetrics();
            });
        });

        // 개인 지표 탭 변경
        document.querySelectorAll('.metric-tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.metric-tab-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                const metricKey = e.target.dataset.metric;
                if (cachedData.individualMetrics) {
                    MetricsDisplay.renderIndividualTable(metricKey, cachedData.individualMetrics[metricKey]);
                }
            });
        });

        // 사이드바 토글 (모바일)
        document.getElementById('sidebar-toggle').addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('open');
        });
    }

    // ── 분석 실행 ──
    async function runAnalysis() {
        currentFilters = Filters.getCurrentFilters();

        if (!currentFilters.years || currentFilters.years.length === 0) {
            alert('분석할 연도를 1개 이상 선택해주세요.');
            return;
        }

        showLoading(true);
        cachedData = { network: null, orgMetrics: null, individualMetrics: null, feedbackMetrics: null };

        try {
            const [networkData, orgMetrics] = await Promise.all([
                API.getNetwork(currentFilters),
                API.getOrgMetrics(currentFilters),
            ]);

            cachedData.network = networkData;
            cachedData.orgMetrics = orgMetrics;

            // 사이드바 요약
            document.getElementById('summary-nodes').textContent = networkData.summary.node_count.toLocaleString();
            document.getElementById('summary-edges').textContent = networkData.summary.edge_count.toLocaleString();
            document.getElementById('summary-ghosts').textContent = (networkData.summary.ghost_count || 0).toLocaleString();
            sidebarSummary.style.display = 'block';

            // 조직 KPI 렌더링
            MetricsDisplay.renderOrgKPIs(orgMetrics);

            // 하위 조직 비교
            await loadSubgroupMetrics();

            // UI 전환
            placeholder.style.display = 'none';
            disclaimer.style.display = 'flex';
            results.style.display = 'block';
            if (tabNav) tabNav.style.display = 'flex';

            switchTab('tab-org');

        } catch (err) {
            alert(`분석 실행 실패: ${err.message}`);
            console.error(err);
        } finally {
            showLoading(false);
        }
    }

    // ── 탭 전환 ──
    function switchTab(tabId) {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabId);
        });
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === tabId);
        });

        // Lazy Loading
        if (tabId === 'tab-individual' && !cachedData.individualMetrics) {
            loadIndividualMetrics();
        }
        if (tabId === 'tab-feedback' && !cachedData.feedbackMetrics) {
            loadFeedbackMetrics();
        }
        if (tabId === 'tab-network' && cachedData.network) {
            NetworkGraph.render(cachedData.network);
        }
    }

    // ── 데이터 로딩 ──
    async function loadSubgroupMetrics() {
        const groupCol = document.querySelector('input[name="subgroup-level"]:checked').value;
        try {
            const data = await API.getSubgroupMetrics({
                ...currentFilters,
                group_col: groupCol,
            });
            MetricsDisplay.renderSubgroupTable(data);
        } catch (err) {
            console.warn('하위 조직 지표 로드 실패:', err.message);
            MetricsDisplay.renderSubgroupTable([]);
        }
    }

    async function loadIndividualMetrics() {
        try {
            showLoading(true);
            const data = await API.getIndividualMetrics(currentFilters);
            cachedData.individualMetrics = data;
            MetricsDisplay.renderIndividualTable('selection_burden', data.selection_burden);
        } catch (err) {
            console.warn('개인 지표 로드 실패:', err.message);
        } finally {
            showLoading(false);
        }
    }

    async function loadFeedbackMetrics() {
        try {
            showLoading(true);
            const data = await API.getFeedbackMetrics(currentFilters);
            cachedData.feedbackMetrics = data;
            MetricsDisplay.renderFeedbackMetrics(data);
        } catch (err) {
            console.warn('피드백 분석 로드 실패:', err.message);
        } finally {
            showLoading(false);
        }
    }

    // ── 유틸 ──
    function showLoading(show) {
        loading.style.display = show ? 'flex' : 'none';
        btnAnalyze.disabled = show;
    }
});

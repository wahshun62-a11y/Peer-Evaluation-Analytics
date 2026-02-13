/**
 * metrics-display.js — 제도 건전성 지표를 렌더링합니다.
 *
 * ★ 설계 원칙:
 *   1. HR 실무자 중심 3계층 벤치마크:
 *      - 계층 1 (절대 기준): "40% 이하면 건전" 같은 직관적 가이드
 *      - 계층 2 (추세): Sparkline으로 연도별 흐름 시각화 (마우스오버 툴팁)
 *      - 계층 3 (전사 비교): 전사 평균값을 참조로 제공 ("전사 평균 대비 높음/낮음")
 *   2. 설명은 HR 비전공자가 이해할 수 있는 실무적 문장 사용
 */
const MetricsDisplay = (() => {

    // ══════════════════════════════════════════════
    //  조직 수준 KPI 메타데이터 (HR 실무 기준선 포함)
    // ══════════════════════════════════════════════

    const KPI_META = {
        _cross_distribution: {
            label: '평가자 선정 범위 분포',
            icon: '🔀',
            help: '평가자를 어느 범위에서 골랐는지를 보여줍니다. 다른 조직 비율이 높을수록 다양한 시선의 피드백을 받고 있습니다.',
            type: 'distribution',
        },
        cross_org3_ratio: {
            label: 'ORG3 외 선정 비율',
            icon: '🏢',
            help: '평가자와 피평가자의 팀(ORG3)이 다른 비율입니다. 높을수록 팀 장벽을 넘는 평가가 활발합니다.',
            format: 'percent',
            benchmark: { good: 0.20, caution: 0.10, direction: 'higher_is_better', guide: '20% 이상 권장 / 10% 미만 주의' },
        },
        gini_coefficient: {
            label: '평가 요청 편중도',
            icon: '⚖️',
            help: '특정 사람에게 평가 요청이 몰리는 정도입니다. 높을수록 일부 직원에게 피드백 부담이 집중되어 품질이 저하될 수 있습니다.',
            format: 'decimal',
            benchmark: { good: 0.25, caution: 0.40, direction: 'lower_is_better', guide: '0.3 이하 권장 / 0.5 이상 경고' },
        },
        reciprocity: {
            label: '서로 선정한 비율',
            icon: '🤝',
            help: '"A가 B를, B도 A를 평가자로 선정"한 비율입니다. 너무 높으면 친소관계 위주의 담합 가능성이 있습니다.',
            format: 'percent',
            benchmark: { good: 0.40, caution: 0.60, direction: 'lower_is_better', guide: '40% 이하 권장 / 60% 이상 경고' },
        },
        avg_evaluators: {
            label: '1인당 평균 평가자 수',
            icon: '👥',
            help: '한 사람이 평균 몇 명의 평가자를 선정했는지입니다. 너무 적으면 다양성 부족, 너무 많으면 평가 부담 증가.',
            format: 'number',
            benchmark: { min: 3, max: 8, direction: 'range', guide: '3~7명 권장' },
        },
        participation_density: {
            label: '평가 참여 활발도',
            icon: '📊',
            help: '구성원 간 평가 관계가 얼마나 촘촘하게 맺어졌는지 나타내는 지표입니다.',
            format: 'decimal',
            benchmark: null,
        },
    };

    const METRIC_DESCRIPTIONS = {
        selection_burden: {
            title: '⚡ 평가 부담 집중',
            text: '이 사람을 평가자로 선정한 동료가 많습니다. 신뢰받는 인재이지만, 평가량이 과하면 깊이 있는 피드백이 어려워집니다.',
            benchmark: '⚠️ 전사 평균 대비 2배 이상이면 조정 권고',
        },
        cross_org_rate: {
            title: '🔀 다른 조직 평가 비율',
            text: '다른 팀/실 동료로부터 피드백을 받는 비율입니다. 다양한 관점의 성찰을 얻고 있는지 확인하세요.',
            benchmark: '✅ 30% 이상이면 다양성 양호',
        },
        mutual_selection: {
            title: '⚠️ 서로 선정한 비율 (경고 지표)',
            text: '서로를 평가자로 지정한 호혜적 관계입니다. 비율이 과도하게 높으면 "좋은 게 좋은 것" 식의 평가 담합이 우려됩니다.',
            benchmark: '⚠️ 60% 이상이면 담합 주의',
        },
        group_closure: {
            title: '🔒 폐쇄적 평가 그룹',
            text: '평가자들이 서로끼리만 평가하는 닫힌 구조입니다. 외부의 객관적 시선이 차단된 상태일 수 있습니다.',
            benchmark: '⚠️ 0.5 이상이면 그룹 폐쇄성 높음',
        },
    };

    // ══════════════════════════════════════════════
    //  기준선 판정 및 Sparkline 생성
    // ══════════════════════════════════════════════

    function _evaluateStatus(value, benchmark) {
        if (!benchmark || typeof value !== 'number') return null;
        const { good, caution, min, max, direction } = benchmark;
        if (direction === 'higher_is_better') {
            if (value >= good) return 'good';
            if (value >= caution) return 'caution';
            return 'warning';
        }
        if (direction === 'lower_is_better') {
            if (value <= good) return 'good';
            if (value <= caution) return 'caution';
            return 'warning';
        }
        if (direction === 'range') {
            if (value >= min && value <= max) return 'good';
            return 'warning';
        }
        return null;
    }

    function _statusBadge(status) {
        const map = {
            good: { label: '양호', color: '#0D8050', bg: '#E6F4EC' },
            caution: { label: '주의', color: '#B8860B', bg: '#FFF8E1' },
            warning: { label: '경고', color: '#C62828', bg: '#FFEBEE' },
        };
        const s = map[status];
        if (!s) return '';
        return `<span class="kpi-badge" style="background:${s.bg}; color:${s.color}">${s.label}</span>`;
    }

    function _createSparkline(history, years, width = 70, height = 24, color = '#002D80') {
        if (!history || history.length < 2) return '';
        const minVal = Math.min(...history);
        const maxVal = Math.max(...history);
        const range = (maxVal - minVal) || 1;

        const points = history.map((v, i) => {
            const x = (i / (history.length - 1)) * width;
            const y = height - ((v - minVal) / range) * height;
            return `${x},${y}`;
        }).join(' ');

        // 포인트에 툴팁(title) 추가를 위해 circle 요소들도 생성
        const circlePoints = history.map((v, i) => {
            const x = (i / (history.length - 1)) * width;
            const y = height - ((v - minVal) / range) * height;
            const year = years ? years[i] : '';
            return `<circle cx="${x}" cy="${y}" r="2.5" fill="${color}" class="spark-dot">
                        <title>${year}년: ${v.toFixed(4)}</title>
                    </circle>`;
        }).join('');

        return `
            <svg width="${width}" height="${height}" viewBox="-2 -2 ${width + 4} ${height + 4}" class="sparkline-svg">
                <polyline points="${points}" fill="none" stroke="${color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                ${circlePoints}
            </svg>
        `;
    }

    // ══════════════════════════════════════════════
    //  KPI 카드 렌더링 (3계층 벤치마크 적용)
    // ══════════════════════════════════════════════

    function renderOrgKPIs(metrics) {
        const grid = document.getElementById('kpi-grid');
        grid.innerHTML = '';
        const benchmarks = metrics.benchmarks || {};

        Object.entries(KPI_META).forEach(([key, meta]) => {
            const card = document.createElement('div');
            card.className = 'kpi-card';

            if (meta.type === 'distribution') {
                const same = ((metrics.same_team_ratio || 0) * 100).toFixed(1);
                const sameD = ((metrics.same_dept_diff_team_ratio || 0) * 100).toFixed(1);
                const cross = ((metrics.cross_dept_ratio || 0) * 100).toFixed(1);

                card.className = 'kpi-card kpi-card--wide';
                card.innerHTML = `
                    <div class="kpi-label">${meta.icon} ${meta.label}</div>
                    <div class="distribution-bars">
                        <div class="dist-row">
                            <span class="dist-dot" style="background:#4ade80"></span>
                            <span class="dist-label">팀 내 (ORG3 동일)</span>
                            <div class="dist-bar-wrap"><div class="dist-bar" style="width:${same}%; background:#4ade80"></div></div>
                            <span class="dist-value">${same}%</span>
                        </div>
                        <div class="dist-row">
                            <span class="dist-dot" style="background:#fbbf24"></span>
                            <span class="dist-label">부서 내 (ORG2 동일)</span>
                            <div class="dist-bar-wrap"><div class="dist-bar" style="width:${sameD}%; background:#fbbf24"></div></div>
                            <span class="dist-value">${sameD}%</span>
                        </div>
                        <div class="dist-row">
                            <span class="dist-dot" style="background:#f87171"></span>
                            <span class="dist-label">조직 외 (ORG2 상이)</span>
                            <div class="dist-bar-wrap"><div class="dist-bar" style="width:${cross}%; background:#f87171"></div></div>
                            <span class="dist-value">${cross}%</span>
                        </div>
                    </div>
                `;
            } else {
                const value = metrics[key];
                const display = (meta.format === 'percent') ? (value * 100).toFixed(1) + '%' :
                    (meta.format === 'number') ? value.toFixed(1) : value.toFixed(4);

                const status = _evaluateStatus(value, meta.benchmark);
                const badge = _statusBadge(status);

                // 벤치마크 연동 정보 (추세 & 전사 평균)
                const dyn = benchmarks[key] || {};
                const spark = _createSparkline(dyn.history, dyn.years);
                const totalAvg = dyn.total_avg;
                const totalAvgDisplay = totalAvg !== undefined ?
                    ((meta.format === 'percent') ? (totalAvg * 100).toFixed(1) + '%' : totalAvg.toFixed(3)) : '—';

                card.className = `kpi-card ${status ? 'kpi-card--' + status : ''}`;
                card.innerHTML = `
                    <div class="kpi-header">
                        <div class="kpi-label">${meta.icon} ${meta.label} ${badge}</div>
                        <div class="kpi-spark">${spark}</div>
                    </div>
                    <div class="kpi-value">${display}</div>
                    <div class="kpi-benchmark-info">
                        <div class="kpi-ref-item">
                            <span class="ref-label">전사 평균</span>
                            <span class="ref-value">${totalAvgDisplay}</span>
                        </div>
                        ${meta.benchmark ? `
                        <div class="kpi-ref-item">
                            <span class="ref-label">가이드</span>
                            <span class="ref-value">${meta.benchmark.guide}</span>
                        </div>` : ''}
                    </div>
                    <div class="kpi-help">${meta.help}</div>
                `;
            }
            grid.appendChild(card);
        });
    }

    // ══════════════════════════════════════════════
    //  테이블 렌더링 및 정렬 (기존 로직 유지)
    // ══════════════════════════════════════════════

    const _sortStates = {};

    function _buildSortableTable(tableId, columns, rows) {
        if (!_sortStates[tableId]) _sortStates[tableId] = { key: null, asc: true };
        const state = _sortStates[tableId];

        let sortedRows = [...rows];
        if (state.key) {
            sortedRows.sort((a, b) => {
                let va = a[state.key], vb = b[state.key];
                if (typeof va === 'number' && typeof vb === 'number') return state.asc ? va - vb : vb - va;
                va = String(va ?? ''); vb = String(vb ?? '');
                return state.asc ? va.localeCompare(vb, 'ko') : vb.localeCompare(va, 'ko');
            });
        }

        const ths = columns.map(c => {
            const isActive = state.key === c.key;
            const arrow = isActive ? (state.asc ? '▲' : '▼') : '↕';
            return `<th class="${isActive ? 'sort-active' : ''}" data-sort-key="${c.key}">${c.label} <span class="sort-arrow">${arrow}</span></th>`;
        }).join('');

        const trs = sortedRows.map(row => {
            const tds = columns.map(c => {
                let val = row[c.key];
                if (c.format === 'percent' && typeof val === 'number') val = (val * 100).toFixed(1) + '%';
                else if (c.format === 'number' && typeof val === 'number') val = val.toFixed(1);
                else if (typeof val === 'number' && c.key !== 'rank' && c.key !== 'member_count' && c.key !== 'feedback_count') val = val.toFixed(4);
                return `<td>${val ?? '—'}</td>`;
            }).join('');
            return `<tr>${tds}</tr>`;
        }).join('');

        return `<table class="data-table" data-table-id="${tableId}"><thead><tr>${ths}</tr></thead><tbody>${trs}</tbody></table>`;
    }

    function _bindSortEvents(container, tableId, columns, rows, renderFn) {
        const table = container.querySelector(`[data-table-id="${tableId}"]`);
        if (!table) return;
        table.querySelectorAll('th[data-sort-key]').forEach(th => {
            th.addEventListener('click', () => {
                const key = th.getAttribute('data-sort-key');
                const state = _sortStates[tableId];
                if (state.key === key) state.asc = !state.asc;
                else { state.key = key; state.asc = true; }
                renderFn();
            });
        });
    }

    function renderSubgroupTable(data) {
        const container = document.getElementById('subgroup-table');
        if (!data || data.length === 0) {
            container.innerHTML = '<p class="empty-msg">비교할 데이터가 없습니다.</p>';
            return;
        }
        const columns = [
            { key: 'group_name', label: '조직명' },
            { key: 'member_count', label: '인원' },
            { key: 'cross_org1_ratio', label: 'ORG1 외', format: 'percent' },
            { key: 'cross_org2_ratio', label: 'ORG2 외', format: 'percent' },
            { key: 'cross_org3_ratio', label: 'ORG3 외', format: 'percent' },
            { key: 'reciprocity', label: '상호선정률', format: 'percent' },
            { key: 'avg_evaluators', label: '평균 평가자', format: 'number' },
            { key: 'gini_coefficient', label: '부담 편중도' },
        ];
        const render = () => {
            container.innerHTML = _buildSortableTable('subgroup', columns, data);
            _bindSortEvents(container, 'subgroup', columns, data, render);
        };
        render();
    }

    let _individualCache = { metricKey: null, data: null };
    function renderIndividualTable(metricKey, data) {
        _individualCache = { metricKey, data };
        const descEl = document.getElementById('metric-description');
        const desc = METRIC_DESCRIPTIONS[metricKey];
        if (desc) {
            descEl.innerHTML = `
                <div class="metric-desc-title">${desc.title}</div>
                <div class="metric-desc-text">${desc.text}</div>
                <div class="metric-desc-benchmark">${desc.benchmark}</div>
            `;
        }
        _renderIndividualInternal();
    }

    function _renderIndividualInternal() {
        const { data } = _individualCache;
        const container = document.getElementById('individual-table');
        if (!data || data.length === 0) { container.innerHTML = '<p class="empty-msg">데이터가 없습니다.</p>'; return; }

        const columns = [
            { key: 'rank', label: '#' },
            { key: '성명', label: '성명' },
            { key: '사번', label: '사번' },
            { key: 'ORG1_OP', label: 'ORG1' },
            { key: 'ORG2_OP', label: 'ORG2' },
            { key: 'GRADE', label: '직급' },
            { key: 'value', label: '값' },
        ];
        const rankedData = data.map((row, i) => ({ ...row, rank: i + 1 }));
        container.innerHTML = _buildSortableTable('individual', columns, rankedData);
        _bindSortEvents(container, 'individual', columns, rankedData, _renderIndividualInternal);
    }

    function renderFeedbackMetrics(data) {
        const kpiGrid = document.getElementById('feedback-kpi-grid');
        kpiGrid.innerHTML = '';
        if (data.cross_org_feedback_quality) {
            const q = data.cross_org_feedback_quality;
            const diff = q.cross_org_avg_len - q.same_org_avg_len;
            kpiGrid.innerHTML = `
                <div class="kpi-card"><div class="kpi-label">📝 자조직 피드백 길이</div><div class="kpi-value">${q.same_org_avg_len.toFixed(0)}자</div></div>
                <div class="kpi-card"><div class="kpi-label">📝 타조직 피드백 길이</div><div class="kpi-value">${q.cross_org_avg_len.toFixed(0)}자</div></div>
                <div class="kpi-card kpi-card--${diff > 0 ? 'good' : 'warning'}">
                    <div class="kpi-label">📊 협업 시너지(차이)</div>
                    <div class="kpi-value">${diff > 0 ? '+' : ''}${diff.toFixed(0)}자</div>
                </div>
            `;
        }
        _renderFeedbackIndividualInternal(data.individual_feedback);
        _renderCollusionInternal(data.collusion_flags);
    }

    function _renderFeedbackIndividualInternal(data) {
        const container = document.getElementById('feedback-individual-table');
        if (!data) return;
        const columns = [{ key: '성명', label: '성명' }, { key: 'ORG2_OP', label: 'ORG2' }, { key: 'feedback_count', label: '건수' }, { key: 'avg_feedback_len', label: '평균 길이', format: 'number' }, { key: 'constructive_rate', label: '보완점 비율(%)', format: 'number' }];
        const render = () => {
            container.innerHTML = _buildSortableTable('fb-ind', columns, data);
            _bindSortEvents(container, 'fb-ind', columns, data, render);
        };
        render();
    }

    function _renderCollusionInternal(data) {
        const container = document.getElementById('collusion-table');
        if (!data || data.length === 0) { container.innerHTML = '<p class="empty-msg">✅ 감지된 위험 징후가 없습니다.</p>'; return; }
        const columns = [{ key: '성명', label: '성명' }, { key: 'mutual_rate', label: '상호선정률(%)', format: 'number' }, { key: 'flag', label: '사유' }];
        const render = () => {
            container.innerHTML = _buildSortableTable('collusion', columns, data);
            _bindSortEvents(container, 'collusion', columns, data, render);
        };
        render();
    }

    return { renderOrgKPIs, renderSubgroupTable, renderIndividualTable, renderFeedbackMetrics };
})();

/**
 * api.js — 백엔드 API 호출 모듈
 */
const API = (() => {
    const BASE = '';  // 같은 origin

    async function _fetch(url, options = {}) {
        const res = await fetch(url, {
            headers: { 'Content-Type': 'application/json' },
            ...options,
        });
        if (!res.ok) {
            const detail = await res.json().catch(() => ({}));
            throw new Error(detail.detail || `HTTP ${res.status}`);
        }
        return res.json();
    }

    return {
        getFilterOptions: (years, orgs1 = []) =>
            _fetch(`${BASE}/api/filter-options?years=${years.join(',')}&orgs1=${orgs1.join(',')}`),

        getNetwork: (filters) =>
            _fetch(`${BASE}/api/network`, { method: 'POST', body: JSON.stringify(filters) }),

        getOrgMetrics: (filters) =>
            _fetch(`${BASE}/api/metrics/organization`, { method: 'POST', body: JSON.stringify(filters) }),

        getIndividualMetrics: (filters) =>
            _fetch(`${BASE}/api/metrics/individual`, { method: 'POST', body: JSON.stringify(filters) }),

        getSubgroupMetrics: (filters) =>
            _fetch(`${BASE}/api/metrics/subgroup`, { method: 'POST', body: JSON.stringify(filters) }),

        getFeedbackMetrics: (filters) =>
            _fetch(`${BASE}/api/metrics/feedback`, { method: 'POST', body: JSON.stringify(filters) }),
    };
})();

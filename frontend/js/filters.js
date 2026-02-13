/**
 * filters.js — 필터 UI 관리 (칩 기반)
 *
 * ★ 주요 기능:
 *   1. 선택된 필터를 하이라이트 (active 클래스)
 *   2. ORG1 선택 시 ORG2/직군/직급 캐스케이드 갱신
 *   3. 필터 리셋 버튼 지원
 */
const Filters = (() => {

    let _selectedYears = [];
    let _selectedOrgs1 = [];
    let _selectedOrgs2 = [];
    let _selectedJobs = [];
    let _selectedGrades = [];
    let _allOptions = null;

    /**
     * 초기화: 연도 칩 생성 및 필터 옵션 로드
     */
    async function init(defaultYears) {
        const yearContainer = document.getElementById('year-chips');
        yearContainer.innerHTML = '';
        defaultYears.forEach(y => {
            const chip = _createChip(String(y), y === defaultYears[0]);
            chip.addEventListener('click', () => {
                chip.classList.toggle('active');
                _syncSelectedYears();
            });
            yearContainer.appendChild(chip);
        });

        // 최신 연도 기본 선택
        _selectedYears = [defaultYears[0]];

        // 필터 옵션 로드
        await _loadFilterOptions();
    }

    /**
     * 필터 옵션을 API에서 로드합니다.
     * ★ ORG1 선택 시 캐스케이드: ORG1에 속한 하위 옵션만 표시
     */
    async function _loadFilterOptions() {
        try {
            const years = _selectedYears.length ? _selectedYears : [2025];
            _allOptions = await API.getFilterOptions(years, _selectedOrgs1);

            _renderFilterChips('org1-chips', _allOptions.orgs1, _selectedOrgs1, (selected) => {
                _selectedOrgs1 = selected;
                // 캐스케이드: ORG1 변경 시 하위 필터 갱신
                _selectedOrgs2 = [];
                _selectedJobs = [];
                _selectedGrades = [];
                _loadFilterOptions();
                // 히트 표시
                const hint = document.getElementById('cascade-hint');
                if (_selectedOrgs1.length > 0) {
                    hint.textContent = `← ${_selectedOrgs1.join(', ')} 기준`;
                } else {
                    hint.textContent = '';
                }
            });

            _renderFilterChips('org2-chips', _allOptions.orgs2, _selectedOrgs2, (selected) => {
                _selectedOrgs2 = selected;
            });

            _renderFilterChips('job-chips', _allOptions.jobs, _selectedJobs, (selected) => {
                _selectedJobs = selected;
            });

            _renderFilterChips('grade-chips', _allOptions.grades, _selectedGrades, (selected) => {
                _selectedGrades = selected;
            });

        } catch (err) {
            console.warn('필터 옵션 로드 실패:', err.message);
        }
    }

    /**
     * 칩 UI를 렌더링합니다. 선택된 것은 하이라이트 표시.
     */
    function _renderFilterChips(containerId, options, selectedArr, onChange) {
        const container = document.getElementById(containerId);
        container.innerHTML = '';

        if (!options || options.length === 0) {
            container.innerHTML = '<span class="no-options">옵션 없음</span>';
            return;
        }

        options.forEach(opt => {
            const isSelected = selectedArr.includes(opt);
            const chip = _createChip(opt, isSelected);
            chip.addEventListener('click', () => {
                chip.classList.toggle('active');
                // 선택 동기화
                const idx = selectedArr.indexOf(opt);
                if (idx >= 0) {
                    selectedArr.splice(idx, 1);
                } else {
                    selectedArr.push(opt);
                }
                onChange([...selectedArr]);
            });
            container.appendChild(chip);
        });
    }

    function _createChip(text, isActive) {
        const chip = document.createElement('button');
        chip.className = `filter-chip${isActive ? ' active' : ''}`;
        chip.textContent = text;
        return chip;
    }

    function _syncSelectedYears() {
        const chips = document.querySelectorAll('#year-chips .filter-chip');
        _selectedYears = [];
        chips.forEach(c => {
            if (c.classList.contains('active')) {
                _selectedYears.push(parseInt(c.textContent));
            }
        });
    }

    /**
     * 모든 필터를 초기화합니다.
     */
    function reset() {
        _selectedOrgs1 = [];
        _selectedOrgs2 = [];
        _selectedJobs = [];
        _selectedGrades = [];
        document.getElementById('cascade-hint').textContent = '';
        _loadFilterOptions();
    }

    /**
     * 현재 선택된 필터를 객체로 반환합니다.
     */
    function getCurrentFilters() {
        return {
            years: _selectedYears,
            orgs1: _selectedOrgs1,
            orgs2: _selectedOrgs2,
            jobs: _selectedJobs,
            grades: _selectedGrades,
        };
    }

    return { init, getCurrentFilters, reset };
})();

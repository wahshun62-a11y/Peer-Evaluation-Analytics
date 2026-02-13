"""
data_loader.py — 엑셀 데이터를 로드하고 전처리합니다.

핵심 설계 결정:
  - 서버 시작(startup) 시 데이터를 1회만 로드하여 메모리에 상주시킵니다.
  - 연도별 캐싱으로 중복 I/O를 방지합니다.
  - 필터링은 노드 기준으로 적용한 뒤, 해당 노드가 관여한 엣지만 남깁니다.
"""
import os
import pandas as pd
from config import DATA_DIR, AVAILABLE_YEARS
from .network_builder import build_graph
from .metrics_calculator import calculate_system_health_metrics, calculate_dynamic_benchmarks

# 전역 데이터 캐시
_qualitative_cache: dict[int, pd.DataFrame] = {}
_hr_cache: pd.DataFrame | None = None
_combined_cache: dict[tuple, tuple] = {}
_benchmarks_cache: dict = {}

def get_cached_benchmarks():
    return _benchmarks_cache


def load_qualitative_data(year: int) -> pd.DataFrame | None:
    """
    특정 연도의 정성평가 엑셀 파일을 로드합니다.
    """
    if year in _qualitative_cache:
        return _qualitative_cache[year]

    filepath = os.path.join(DATA_DIR, f"02.정성평가_{year}.xlsx")
    if not os.path.exists(filepath):
        return None

    try:
        df = pd.read_excel(filepath)
        if '평가년도' not in df.columns:
            df['평가년도'] = year

        essential_cols = ['평가년도']
        src_col = [c for c in df.columns if '평가자사번' in c]
        dst_col = [c for c in df.columns if '피평가자사번' in c]
        if not src_col or not dst_col:
            print(f"[WARN] {year} 데이터에 평가자사번/피평가자사번 컬럼이 없습니다.")
            return None

        # 컬럼명 표준화 (필요시)
        
        _qualitative_cache[year] = df
        return df
    except Exception as e:
        print(f"[ERROR] {year} 데이터 로드 실패: {e}")
        return None


def load_hr_master_data() -> pd.DataFrame | None:
    """
    HR 기본 정보(조직, 직군, 직급 등)를 로드합니다.
    """
    global _hr_cache
    if _hr_cache is not None:
        return _hr_cache

    filepath = os.path.join(DATA_DIR, "00.HR기본정보.xlsx")
    if not os.path.exists(filepath):
        print(f"[WARN] HR 기본정보 파일이 없습니다: {filepath}")
        return None

    try:
        df = pd.read_excel(filepath)
        use_cols = ['평가년도', '사번', 'ORG1_OP', 'ORG2_OP', 'ORG3_OP', 'JOB_FAMILY_CODE', 'GRADE']
        available = [c for c in use_cols if c in df.columns]
        _hr_cache = df[available].copy()
        # ★ 사번을 문자열로 통일 (int/str 혼재 방지)
        _hr_cache['사번'] = _hr_cache['사번'].astype(str).str.strip()
        return _hr_cache
    except Exception as e:
        print(f"[ERROR] HR 데이터 로드 실패: {e}")
        return None


def prepare_combined_network_data(selected_years: list[int]) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """
    선택된 연도의 정성평가 데이터와 HR 데이터를 결합합니다.
    """
    cache_key = tuple(sorted(selected_years))
    if cache_key in _combined_cache:
        return _combined_cache[cache_key]

    qual_list = [load_qualitative_data(y) for y in selected_years]
    qual_list = [d for d in qual_list if d is not None]

    if not qual_list:
        return None, None

    combined_qual_df = pd.concat(qual_list, ignore_index=True)
    
    # ★ HR 데이터 로드 시도
    hr_df = load_hr_master_data()
    
    if hr_df is None:
        # HR 데이터가 없어도 정성평가 데이터만으로 진행 (이름 등 최소 정보)
        src_id_col = [c for c in combined_qual_df.columns if '평가자사번' in c][0]
        dst_id_col = [c for c in combined_qual_df.columns if '피평가자사번' in c][0]
        src_name_col = [c for c in combined_qual_df.columns if '평가자성명' in c][0]
        dst_name_col = [c for c in combined_qual_df.columns if '피평가자성명' in c][0]

        nodes_src = combined_qual_df[[src_id_col, src_name_col]].rename(columns={src_id_col: '사번', src_name_col: '성명'})
        nodes_dst = combined_qual_df[[dst_id_col, dst_name_col]].rename(columns={dst_id_col: '사번', dst_name_col: '성명'})
        all_nodes_base = pd.concat([nodes_src, nodes_dst]).drop_duplicates(subset=['사번'])
        all_nodes_base['사번'] = all_nodes_base['사번'].astype(str).str.strip().str.replace('\xa0', '', regex=False).str.replace('&nbsp;', '', regex=False)
        
        # 필수 컬럼 채우기
        for col in ['ORG1_OP', 'ORG2_OP', 'ORG3_OP', 'JOB_FAMILY_CODE', 'GRADE']:
            all_nodes_base[col] = 'Unknown'
            
        result = (combined_qual_df, all_nodes_base)
        _combined_cache[cache_key] = result
        return result

    # 가장 최신의 HR 정보를 기준으로 노드 속성 정의
    latest_hr = hr_df[hr_df['평가년도'].isin(selected_years)].sort_values('평가년도').drop_duplicates('사번', keep='last')

    # 노드 리스트 생성 (평가자와 피평가자 모두 포함)
    src_id_col = [c for c in combined_qual_df.columns if '평가자사번' in c][0]
    dst_id_col = [c for c in combined_qual_df.columns if '피평가자사번' in c][0]
    src_name_col = [c for c in combined_qual_df.columns if '평가자성명' in c][0]
    dst_name_col = [c for c in combined_qual_df.columns if '피평가자성명' in c][0]

    nodes_src = combined_qual_df[[src_id_col, src_name_col]].rename(columns={src_id_col: '사번', src_name_col: '성명'})
    nodes_dst = combined_qual_df[[dst_id_col, dst_name_col]].rename(columns={dst_id_col: '사번', dst_name_col: '성명'})
    all_nodes_base = pd.concat([nodes_src, nodes_dst]).drop_duplicates(subset=['사번'])
    
    # ★ 사번을 문자열로 통일 (HR 데이터와 매칭을 위해)
    all_nodes_base['사번'] = all_nodes_base['사번'].astype(str).str.strip().str.replace('\xa0', '', regex=False).str.replace('&nbsp;', '', regex=False)

    # HR 정보 결합 (ORG3 포함)
    merge_cols = ['사번', 'ORG1_OP', 'ORG2_OP', 'ORG3_OP', 'JOB_FAMILY_CODE', 'GRADE']
    available_merge = [c for c in merge_cols if c in latest_hr.columns]
    
    nodes_with_attr = pd.merge(
        all_nodes_base,
        latest_hr[available_merge],
        on='사번', how='left'
    )
    nodes_with_attr.fillna('Unknown', inplace=True)

    result = (combined_qual_df, nodes_with_attr)
    _combined_cache[cache_key] = result
    return result


def filter_network_data(
    nodes_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    orgs1: list[str],
    orgs2: list[str],
    jobs: list[str],
    grades: list[str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    사용자가 선택한 필터 조건에 따라 노드와 엣지를 필터링합니다.
    """
    filtered = nodes_df.copy()

    if orgs1:
        filtered = filtered[filtered['ORG1_OP'].isin(orgs1)]
    if orgs2:
        filtered = filtered[filtered['ORG2_OP'].isin(orgs2)]
    if jobs and 'JOB_FAMILY_CODE' in filtered.columns:
        filtered = filtered[filtered['JOB_FAMILY_CODE'].isin(jobs)]
    if grades and 'GRADE' in filtered.columns:
        filtered = filtered[filtered['GRADE'].isin(grades)]

    valid_ids = set(filtered['사번'])

    # 엣지 컬럼명 표준화
    src_col = [c for c in edges_df.columns if '평가자사번' in c][0]
    dst_col = [c for c in edges_df.columns if '피평가자사번' in c][0]

    # 엣지 필터: source 또는 target 중 하나라도 필터 대상이면 유지 (Ghost Node 지원)
    # ★ 엣지 사번도 문자열로 정규화
    edges_df = edges_df.copy()
    edges_df[src_col] = edges_df[src_col].astype(str).str.strip().str.replace('\xa0', '', regex=False).str.replace('&nbsp;', '', regex=False)
    edges_df[dst_col] = edges_df[dst_col].astype(str).str.strip().str.replace('\xa0', '', regex=False).str.replace('&nbsp;', '', regex=False)

    filtered_edges = edges_df[
        (edges_df[src_col].isin(valid_ids)) | (edges_df[dst_col].isin(valid_ids))
    ].copy()
    filtered_edges = filtered_edges.rename(columns={src_col: 'source', dst_col: 'target'})

    return filtered, filtered_edges


def get_filter_options(selected_years: list[int], orgs1: list[str] | None = None) -> dict:
    """
    필터 드롭다운에 표시할 선택지를 반환합니다.
    """
    _, nodes_df = prepare_combined_network_data(selected_years)
    if nodes_df is None:
        return {"years": selected_years, "orgs1": [], "orgs2": [], "jobs": [], "grades": []}

    result_nodes = nodes_df.copy()
    
    # 캐스케이드: ORG1 선택 시 하위 필터 제한
    if orgs1:
        result_nodes = result_nodes[result_nodes['ORG1_OP'].isin(orgs1)]

    return {
        "years": selected_years,
        "orgs1": sorted(nodes_df['ORG1_OP'].dropna().unique().tolist()),  # ORG1은 항상 전체
        "orgs2": sorted(result_nodes['ORG2_OP'].dropna().unique().tolist()),
        "jobs": sorted(result_nodes['JOB_FAMILY_CODE'].dropna().unique().tolist()) if 'JOB_FAMILY_CODE' in result_nodes.columns else [],
        "grades": sorted(result_nodes['GRADE'].dropna().unique().tolist()) if 'GRADE' in result_nodes.columns else [],
    }


def preload_all_data():
    """
    서버 시작 시 모든 연도 데이터를 미리 로드하고 벤치마크를 계산합니다.
    """
    global _combined_cache, _benchmarks_cache
    _combined_cache = {}  # stale 방지
    _benchmarks_cache = {}

    print("[INFO] 데이터 사전 로딩 및 벤치마크 계산 시작...")
    
    history_metrics = {}
    for year in AVAILABLE_YEARS:
        # 1. Load Data
        result = load_qualitative_data(year)
        if result is not None:
             # print(f"  ✓ {year}년 정성평가: {len(result)}건")
             pass
        
        # 2. Build Graph & Calculate Metrics (for Benchmarks)
        try:
            edges, nodes = prepare_combined_network_data([year])
            if nodes is not None and not nodes.empty and edges is not None:
                # ★ 컬럼명 표준화 (KeyError: 'source' 방지)
                src_id_col = [c for c in edges.columns if '평가자사번' in c][0]
                dst_id_col = [c for c in edges.columns if '피평가자사번' in c][0]
                edges_std = edges.rename(columns={src_id_col: 'source', dst_id_col: 'target'})
                
                # 사번 정규화 (str 처리)
                edges_std['source'] = edges_std['source'].astype(str).str.strip().str.replace('\xa0', '', regex=False).str.replace('&nbsp;', '', regex=False)
                edges_std['target'] = edges_std['target'].astype(str).str.strip().str.replace('\xa0', '', regex=False).str.replace('&nbsp;', '', regex=False)

                G = build_graph(nodes, edges_std)
                metrics = calculate_system_health_metrics(G, nodes, edges_std)
                history_metrics[year] = metrics
                print(f"  ✓ {year}년 분석 완료 (노드 {len(nodes)}개)")
        except Exception as e:
            print(f"  ⚠️ {year}년 분석 실패: {e}")

    # 3. Method 1 & 2: Calculate Dynamic Benchmarks
    try:
        _benchmarks_cache = calculate_dynamic_benchmarks(history_metrics)
        print(f"  ✓ 동적 벤치마크 계산 완료 ({len(history_metrics)}개 연도 기반)")
    except Exception as e:
        print(f"  ⚠️ 벤치마크 계산 실패: {e}")
    
    hr = load_hr_master_data()
    if hr is not None:
        print(f"  ✓ HR 기본정보: {len(hr)}건")
    print("[INFO] 데이터 사전 로딩 완료")

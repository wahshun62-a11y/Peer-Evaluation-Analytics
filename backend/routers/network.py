"""
routers/network.py — 네트워크 분석 API 엔드포인트를 정의합니다.

★ v2.1 변경사항:
  - 캐스케이드 필터: ORG1 선택 시 ORG2/직군/직급 옵션 동적 변경
  - Ghost Node: 필터 외부 연결 노드 표시
  - 정성 피드백 분석: 평균 길이, 크로스-조직 비교, 담합 경고
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.data_loader import (
    prepare_combined_network_data,
    filter_network_data,
    get_filter_options,
    get_cached_benchmarks
)
from services.network_builder import build_graph, graph_to_vis_json
from services.metrics_calculator import (
    calculate_system_health_metrics,
    calculate_individual_metrics,
    calculate_subgroup_metrics,
)
import pandas as pd
import numpy as np

router = APIRouter(prefix="/api", tags=["network"])


# ──────────────────────────────────────────────
# Request/Response 모델
# ──────────────────────────────────────────────

class FilterRequest(BaseModel):
    """프론트엔드에서 보내는 필터 조건"""
    years: list[int] = [2025]
    orgs1: list[str] = []
    orgs2: list[str] = []
    jobs: list[str] = []
    grades: list[str] = []


class SubgroupRequest(FilterRequest):
    """하위 그룹 분석용: 기본 필터 + 그룹 기준 컬럼"""
    group_col: str = "ORG1_OP"


# ──────────────────────────────────────────────
# 공통 헬퍼
# ──────────────────────────────────────────────

def _get_filtered_data(req: FilterRequest):
    """필터 적용된 노드/엣지 DataFrame을 반환하는 공통 로직"""
    raw_edges, all_nodes = prepare_combined_network_data(req.years)
    if raw_edges is None or all_nodes is None:
        raise HTTPException(status_code=404, detail="선택한 연도에 해당하는 데이터가 없습니다.")

    filtered_nodes, filtered_edges = filter_network_data(
        all_nodes, raw_edges, req.orgs1, req.orgs2, req.jobs, req.grades
    )
    return filtered_nodes, filtered_edges, all_nodes


# ──────────────────────────────────────────────
# API 엔드포인트
# ──────────────────────────────────────────────

@router.get("/filter-options")
def api_filter_options(years: str = "2025", orgs1: str = ""):
    """
    필터 드롭다운에 표시할 선택지를 반환합니다.
    
    ★ 캐스케이드 필터: orgs1 파라미터가 있으면 해당 ORG1 내의 ORG2/직군/직급만 반환
    """
    year_list = [int(y.strip()) for y in years.split(",") if y.strip()]
    org1_list = [o.strip() for o in orgs1.split(",") if o.strip()] if orgs1 else None
    return get_filter_options(year_list, org1_list)


@router.post("/network")
def api_network(req: FilterRequest):
    """
    필터 적용된 네트워크 데이터 (노드 + 엣지 + 요약)를 반환합니다.
    
    ★ Ghost Node 지원: 필터 외부 연결 노드도 반투명으로 포함합니다.
    """
    filtered_nodes, filtered_edges, all_nodes = _get_filtered_data(req)

    if len(filtered_edges) == 0:
        return {"nodes": [], "edges": [], "summary": {"node_count": len(filtered_nodes), "edge_count": 0, "ghost_count": 0}, "color_legend": {}}

    return graph_to_vis_json(filtered_nodes, filtered_edges, all_nodes)


@router.post("/metrics/organization")
def api_org_metrics(req: FilterRequest):
    """
    조직 수준 제도 건전성 지표를 반환합니다.
    """
    filtered_nodes, filtered_edges, _ = _get_filtered_data(req)

    if len(filtered_edges) == 0:
        raise HTTPException(status_code=400, detail="선택한 조건에 해당하는 엣지가 없습니다.")

    G = build_graph(filtered_nodes, filtered_edges)
    metrics = calculate_system_health_metrics(G, filtered_nodes, filtered_edges)
    
    # ★ 동적 벤치마크(Method 1 & 2) 포함
    benchmarks = get_cached_benchmarks()
    return {**metrics, "benchmarks": benchmarks}


@router.post("/metrics/individual")
def api_individual_metrics(req: FilterRequest):
    """
    개인 수준 평가 참여 패턴 (Top 10%)을 반환합니다.
    
    Why: 평가부담(양), 크로스-조직률(공간), 상호선정률(관계), 그룹폐쇄성(구조)
         4개 핵심 축의 상위 10% 리스트를 프론트엔드의 탭별 테이블에 표시합니다.
    """
    filtered_nodes, filtered_edges, _ = _get_filtered_data(req)

    if len(filtered_edges) == 0:
        raise HTTPException(status_code=400, detail="선택한 조건에 해당하는 엣지가 없습니다.")

    G = build_graph(filtered_nodes, filtered_edges)
    return calculate_individual_metrics(G, filtered_nodes, filtered_edges)


@router.post("/metrics/subgroup")
def api_subgroup_metrics(req: SubgroupRequest):
    """
    하위 조직별 제도 건전성 비교를 반환합니다.
    """
    filtered_nodes, filtered_edges, _ = _get_filtered_data(req)

    if len(filtered_edges) == 0:
        raise HTTPException(status_code=400, detail="선택한 조건에 해당하는 엣지가 없습니다.")

    G = build_graph(filtered_nodes, filtered_edges)
    return calculate_subgroup_metrics(filtered_nodes, filtered_edges, G, req.group_col)


# ──────────────────────────────────────────────
# 정성 피드백 분석 API (NLP 미사용)
# ──────────────────────────────────────────────

@router.post("/metrics/feedback")
def api_feedback_metrics(req: FilterRequest):
    """
    정성 피드백 데이터를 네트워크 분석에 접목합니다.
    NLP를 사용하지 않고 텍스트 길이·입력 패턴만으로 품질을 추정합니다.

    Returns:
        {
            "cross_org_feedback_quality": { 같은팀/다른팀 피드백 평균 길이 비교 },
            "individual_feedback": [ 개인별 평균 피드백 길이 + 건설적 비율 ],
            "collusion_flags": [ 담합 의심 플래그 ],
        }
    """
    raw_edges, all_nodes = prepare_combined_network_data(req.years)
    if raw_edges is None or all_nodes is None:
        raise HTTPException(status_code=404, detail="데이터 없음")

    filtered_nodes, filtered_edges = filter_network_data(
        all_nodes, raw_edges, req.orgs1, req.orgs2, req.jobs, req.grades
    )[:2]

    # ── 텍스트 컬럼 탐색 ──
    feedback_cols = [c for c in raw_edges.columns if '의견' in c or '피드백' in c or '강점' in c or '보완' in c or '코멘트' in c]
    if not feedback_cols:
        return {"cross_org_feedback_quality": None, "individual_feedback": [], "collusion_flags": []}

    src_col = [c for c in raw_edges.columns if '평가자사번' in c][0]
    dst_col = [c for c in raw_edges.columns if '피평가자사번' in c][0]

    # 필터 적용
    valid_ids = set(filtered_nodes['사번'])
    fb_df = raw_edges[
        (raw_edges[src_col].isin(valid_ids)) | (raw_edges[dst_col].isin(valid_ids))
    ].copy()

    # ── 피드백 길이 계산 ──
    fb_df['_fb_combined'] = fb_df[feedback_cols].fillna('').astype(str).agg(' '.join, axis=1)
    fb_df['_fb_len'] = fb_df['_fb_combined'].str.strip().str.len()

    # ── 1단계: 크로스-조직 피드백 품질 비교 ──
    org_col = 'ORG3_OP' if 'ORG3_OP' in all_nodes.columns else 'ORG2_OP'
    node_org = all_nodes[['사번', org_col]].drop_duplicates(subset=['사번'])
    
    fb_merged = fb_df.merge(
        node_org.rename(columns={'사번': src_col, org_col: 'src_org'}), on=src_col, how='left'
    ).merge(
        node_org.rename(columns={'사번': dst_col, org_col: 'tgt_org'}), on=dst_col, how='left'
    )
    fb_merged['_same_org'] = fb_merged['src_org'] == fb_merged['tgt_org']

    same_len = fb_merged[fb_merged['_same_org']]['_fb_len'].mean()
    cross_len = fb_merged[~fb_merged['_same_org']]['_fb_len'].mean()

    cross_quality = {
        "same_org_avg_len": round(same_len, 1) if not pd.isna(same_len) else 0,
        "cross_org_avg_len": round(cross_len, 1) if not pd.isna(cross_len) else 0,
        "org_level_used": org_col,
    }

    # ── 2단계: 개인별 피드백 길이 + 건설적 피드백 비율 ──
    # "건설적 피드백" = 보완점/개선 관련 컬럼이 비어있지 않은 비율
    improvement_cols = [c for c in feedback_cols if '보완' in c or '개선' in c or '발전' in c]
    
    individual_fb = fb_df.groupby(src_col).agg(
        avg_feedback_len=('_fb_len', 'mean'),
        feedback_count=('_fb_len', 'count'),
    ).reset_index().rename(columns={src_col: '사번'})
    individual_fb['avg_feedback_len'] = individual_fb['avg_feedback_len'].round(1)

    if improvement_cols:
        fb_df['_has_constructive'] = fb_df[improvement_cols].fillna('').astype(str).apply(
            lambda row: any(len(v.strip()) > 5 for v in row), axis=1
        )
        constructive_rate = fb_df.groupby(src_col)['_has_constructive'].mean().reset_index()
        constructive_rate.columns = ['사번', 'constructive_rate']
        constructive_rate['constructive_rate'] = (constructive_rate['constructive_rate'] * 100).round(1)
        individual_fb = individual_fb.merge(constructive_rate, on='사번', how='left')
    else:
        individual_fb['constructive_rate'] = None

    # 노드 정보 결합
    individual_fb = individual_fb.merge(
        filtered_nodes[['사번', '성명', 'ORG1_OP', 'ORG2_OP', 'GRADE']],
        on='사번', how='inner'
    )
    individual_fb = individual_fb.sort_values('avg_feedback_len', ascending=True).head(50)

    # ── 3단계: 담합 의심 플래그 ──
    # 조건: 상호선정 + 피드백 극단적으로 짧음 (보완점 기피)
    edge_set = set(zip(fb_df[src_col] if src_col in fb_df.columns else fb_df['source'],
                       fb_df[dst_col] if dst_col in fb_df.columns else fb_df['target']))

    collusion_flags = []
    for _, row in individual_fb.iterrows():
        person_id = row['사번']
        # 상호선정 확인
        outgoing = {t for s, t in edge_set if s == person_id}
        incoming = {s for s, t in edge_set if t == person_id}
        mutual_count = len(outgoing & incoming)
        total_connections = len(outgoing | incoming)
        mutual_rate = mutual_count / total_connections if total_connections > 0 else 0

        # 담합 의심 조건: 상호선정률 60%+ & 피드백 짧고 & 건설적 비율 낮음
        is_suspect = (
            mutual_rate > 0.6
            and row['avg_feedback_len'] < 30
            and (row.get('constructive_rate') is not None and row['constructive_rate'] < 20)
        )

        if is_suspect:
            collusion_flags.append({
                "사번": person_id,
                "성명": row['성명'],
                "ORG1_OP": row['ORG1_OP'],
                "mutual_rate": round(mutual_rate * 100, 1),
                "avg_feedback_len": row['avg_feedback_len'],
                "constructive_rate": row.get('constructive_rate', 0),
                "flag": "⚠️ 상호선정 高 + 피드백 짧음 + 보완점 기피",
            })

    return {
        "cross_org_feedback_quality": cross_quality,
        "individual_feedback": individual_fb.to_dict(orient='records'),
        "collusion_flags": collusion_flags,
    }

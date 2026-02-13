"""
metrics_calculator.py — 동료평가 제도 건전성 지표를 계산합니다.

★ 핵심 프레임 전환:
  기존: "협업 네트워크 분석" → 실제 협업과 무관한 데이터로 오해 유발
  변경: "평가자 선정 패턴 진단" → 제도가 건전하게 운영되고 있는가?

이 네트워크의 엣지 방향:
  source(평가자) → target(피평가자)
  즉, "피평가자가 평가자를 선정한 관계"를 나타냅니다.

  Out-degree(어떤 사람) = 이 사람을 평가자로 선정한 피평가자 수 → 평가 부담
  In-degree(어떤 사람)  = 이 사람이 선정한 평가자 수 → (피평가자로서) 받은 평가 수
"""
import networkx as nx
import pandas as pd
import numpy as np # Import numpy for quantile calc
import numpy as np # Import numpy for quantile calc
import numpy as np # Import numpy for quantile calc
from config import TOP_PERCENT


# ══════════════════════════════════════════════
#  유틸리티 함수
# ══════════════════════════════════════════════

def _gini(values: list) -> float:
    """Gini 계수: 0 = 완전 균등, 1 = 완전 불균등"""
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    total = sum(sorted_vals)
    if n == 0 or total == 0:
        return 0.0
    cumsum = sum((2 * (i + 1) - n - 1) * val for i, val in enumerate(sorted_vals))
    return round(cumsum / (n * total), 4)


def _enrich_edges_with_org(edges_df: pd.DataFrame, nodes_df: pd.DataFrame) -> pd.DataFrame:
    """ìţì§ì source/targetì ORG1, ORG2, ORG3 ì ë³´ë¥¼ ê²°í©í©ëë¤."""
    org_cols = ['사번', 'ORG1_OP', 'ORG2_OP']
    if 'ORG3_OP' in nodes_df.columns:
        org_cols.append('ORG3_OP')
    node_org = nodes_df[org_cols].drop_duplicates(subset=['사번'])

    src_rename = {'사번': 'source', 'ORG1_OP': 'src_org1', 'ORG2_OP': 'src_org2'}
    tgt_rename = {'사번': 'target', 'ORG1_OP': 'tgt_org1', 'ORG2_OP': 'tgt_org2'}
    if 'ORG3_OP' in node_org.columns:
        src_rename['ORG3_OP'] = 'src_org3'
        tgt_rename['ORG3_OP'] = 'tgt_org3'

    merged = edges_df.merge(
        node_org.rename(columns=src_rename), on='source', how='left'
    ).merge(
        node_org.rename(columns=tgt_rename), on='target', how='left'
    )
    return merged


# ══════════════════════════════════════════════
#  조직 수준: 제도 건전성 지표 (5개)
# ══════════════════════════════════════════════

def calculate_system_health_metrics(
    G: nx.DiGraph,
    nodes_df: pd.DataFrame,
    edges_df: pd.DataFrame
) -> dict:
    """
    조직 전체의 동료평가 제도 건전성을 진단합니다.

    Returns:
        {
            "cross_org_ratio":  크로스-조직 선정 비율 (0~1),
            "gini_coefficient": 평가 요청 집중도 Gini (0~1),
            "reciprocity":      상호 선정 비율 (0~1),
            "avg_evaluators":   피평가자당 평균 평가자 수,
            "participation_density": 제도 참여 밀도 (네트워크 밀도),
        }
    """
    metrics = {}
    total_edges = len(edges_df)

    # ── 1. 크로스-조직 선정 3단계 분포 ──
    # ★ ORG3 기준이 기본 (팀 레벨에서의 크로스 비율)
    if total_edges > 0:
        enriched = _enrich_edges_with_org(edges_df, nodes_df)
        has_org3 = 'src_org3' in enriched.columns

        # ORG2 기준
        same_org2 = (enriched['src_org2'] == enriched['tgt_org2']).sum()
        diff_org2 = total_edges - same_org2
        metrics['cross_org2_ratio'] = round(diff_org2 / total_edges, 4)

        # ORG3 기준 (팀 레벨) — KPI 카드의 기본 크로스 비율
        if has_org3:
            same_org3 = (enriched['src_org3'] == enriched['tgt_org3']).sum()
            diff_org3 = total_edges - same_org3
            metrics['cross_org3_ratio'] = round(diff_org3 / total_edges, 4)

            same_org2_diff_org3 = ((enriched['src_org2'] == enriched['tgt_org2']) &
                                   (enriched['src_org3'] != enriched['tgt_org3'])).sum()

            metrics['same_team_ratio'] = round(same_org3 / total_edges, 4)
            metrics['same_dept_diff_team_ratio'] = round(same_org2_diff_org3 / total_edges, 4)
            metrics['cross_dept_ratio'] = round(diff_org2 / total_edges, 4)
        else:
            metrics['cross_org3_ratio'] = metrics['cross_org2_ratio']
            metrics['same_team_ratio'] = round(same_org2 / total_edges, 4)
            metrics['same_dept_diff_team_ratio'] = 0.0
            metrics['cross_dept_ratio'] = round(diff_org2 / total_edges, 4)
    else:
        metrics['cross_org2_ratio'] = 0.0
        metrics['cross_org3_ratio'] = 0.0
        metrics['same_team_ratio'] = 0.0
        metrics['same_dept_diff_team_ratio'] = 0.0
        metrics['cross_dept_ratio'] = 0.0

    # ── 2. 평가 요청 집중도 (Gini 계수) ──
    # Why: 특정인에게 평가 요청이 과도하게 집중되면 평가 품질이 저하됩니다.
    #      분모: 필터링된 Core Nodes (조직 구성원)
    core_ids = set(nodes_df['사번'])
    out_degrees = [G.out_degree(n) for n in core_ids]
    metrics['gini_coefficient'] = _gini(out_degrees)

    # ── 3. 상호 선정 비율 (Reciprocity) ──
    # Why: A가 B를 선정하고 B도 A를 선정한 비율 (조직 내부 응집도/담합 진단).
    #      분무/분자 모두 Core-Core 관계로 한정하여 조직 내 '서로 좋은말하기' 깊이 측정.
    core_edges = edges_df[edges_df['source'].isin(core_ids) & edges_df['target'].isin(core_ids)]
    if not core_edges.empty:
        core_edge_set = set(zip(core_edges['source'], core_edges['target']))
        reciprocal_count = sum(1 for s, t in core_edge_set if (t, s) in core_edge_set)
        metrics['reciprocity'] = round(reciprocal_count / len(core_edge_set), 4)
    else:
        metrics['reciprocity'] = 0.0

    # ── 4. 피평가자당 평균 평가자 수 ──
    # Why: 구성원이 평균적으로 몇 명의 평가자로부터 피드백을 받는지 (외부 평가 포함).
    #      분모: Core Nodes 전체 (0점자 포함)
    in_degrees = [G.in_degree(n) for n in core_ids]
    metrics['avg_evaluators'] = round(sum(in_degrees) / len(core_ids), 1) if core_ids else 0.0

    # ── 5. 제도 참여 밀도 ──
    # Why: Core Node 간의 가능한 관계 중 실제 평가 관계의 비중.
    core_subgraph = G.subgraph(core_ids)
    metrics['participation_density'] = round(nx.density(core_subgraph), 4) if len(core_ids) > 1 else 0.0

    return metrics


# ══════════════════════════════════════════════
#  개인 수준: 평가 참여 패턴 (4개 핵심 지표, Top N%)
#
#  ★ 지표 설계 원칙 (4개 축):
#    1. 양(量)   — 평가 부담 집중도: 요청이 몰리는 사람
#    2. 공간     — 평가자 다양성: 조직 경계를 넘는 비율
#    3. 관계     — 상호 선정률: 호혜적 관계 비율 (⚠️ 높을수록 경고)
#    4. 구조     — 그룹 폐쇄성: 닫힌 클리크 형성 정도
# ══════════════════════════════════════════════

def calculate_individual_metrics(
    G: nx.DiGraph,
    nodes_df: pd.DataFrame,
    edges_df: pd.DataFrame
) -> dict:
    """
    개인별 평가 참여 패턴을 분석합니다.

    Returns:
        {
            "selection_burden":  [평가자로 선정된 횟수 Top N%],
            "cross_org_rate":    [개인별 크로스-조직 비율 Top N%],
            "mutual_selection":  [상호 선정 비율 Top N% — ⚠️ 높을수록 경고],
            "group_closure":     [평가 그룹 폐쇄성 Top N%],
        }
    """
    enriched = _enrich_edges_with_org(edges_df, nodes_df)
    edge_set = set(zip(edges_df['source'], edges_df['target']))

    # ── 1. 평가 부담 집중도 (Out-degree) ──
    # "이 사람을 평가자로 선정한 피평가자 수" → 양(量) 축
    out_deg = {n: d for n, d in G.out_degree()}

    # ── 2. 개인별 크로스-조직 비율 (ORG3 기준: 팀 외 비율) ──
    # → 공간 축: 조직 경계를 넘어 평가자를 선정/선정받는 정도
    has_org3 = 'src_org3' in enriched.columns
    person_cross = {}
    for person_id in nodes_df['사번']:
        person_edges = enriched[
            (enriched['source'] == person_id) | (enriched['target'] == person_id)
        ]
        if len(person_edges) == 0:
            person_cross[person_id] = 0.0
        else:
            if has_org3:
                cross = (person_edges['src_org3'] != person_edges['tgt_org3']).sum()
            else:
                cross = (person_edges['src_org2'] != person_edges['tgt_org2']).sum()
            person_cross[person_id] = round(cross / len(person_edges), 4)

    # ── 3. 개인별 상호 선정 비율 ──
    # → 관계 축: A↔B 양방향 비율. ⚠️ 높을수록 "서로 좋은 평가 교환" 경고
    person_recip = {}
    for person_id in nodes_df['사번']:
        outgoing = [(s, t) for s, t in edge_set if s == person_id]
        incoming = [(s, t) for s, t in edge_set if t == person_id]
        all_edges = set(outgoing + incoming)
        if len(all_edges) == 0:
            person_recip[person_id] = 0.0
        else:
            mutual = sum(1 for s, t in all_edges if (t, s) in edge_set)
            person_recip[person_id] = round(mutual / len(all_edges), 4)

    # ── 4. 평가 그룹 폐쇄성 (Clustering) ──
    # → 구조 축: 나의 평가 관계자들끼리도 서로 평가하는 정도 → 닫힌 그룹
    clustering = nx.clustering(G)

    # ── 결과 조합 ──
    raw_metrics = {
        'selection_burden': out_deg,
        'cross_org_rate': person_cross,
        'mutual_selection': person_recip,
        'group_closure': clustering,
    }

    result = {}
    # nodes_df의 사번 세트 (핵심 노드만 대상으로 지표 생성)
    core_ids = set(nodes_df['사번'])

    for key, metric_dict in raw_metrics.items():
        df_m = pd.DataFrame(list(metric_dict.items()), columns=['사번', 'value'])
        # ★ 핵심 노드만 필터 (Ghost 노드 제외)
        df_m = df_m[df_m['사번'].isin(core_ids)]
        df_m = df_m.sort_values('value', ascending=False)
        top_n = max(5, int(len(df_m) * TOP_PERCENT))

        df_top = pd.merge(
            df_m.head(top_n),
            nodes_df[['사번', '성명', 'ORG1_OP', 'ORG2_OP', 'GRADE']],
            on='사번', how='left'
        )
        df_top['value'] = df_top['value'].round(4)
        # ★ NaN 제거 (JSON 직렬화 오류 방지)
        df_top = df_top.fillna({'성명': '-', 'ORG1_OP': 'Unknown', 'ORG2_OP': 'Unknown', 'GRADE': '-'})
        df_top = df_top.where(df_top.notna(), None)  # 잔여 NaN → None (JSON null)
        result[key] = df_top.to_dict(orient='records')

    return result


# ══════════════════════════════════════════════
#  하위 조직별 비교
# ══════════════════════════════════════════════

def calculate_subgroup_metrics(
    nodes_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    G: nx.DiGraph,
    group_col: str
) -> list[dict]:
    """
    ORG1/ORG2별로 제도 운영 건전성을 비교합니다.

    ★ 엣지 범위: KPI 카드와 동일하게 Ghost 포함 (source OR target이 그룹 소속)
    ★ 크로스-조직: ORG1, ORG2, ORG3 3개 레벨 모두 계산
    """
    groups = nodes_df[group_col].dropna().unique()
    enriched = _enrich_edges_with_org(edges_df, nodes_df)
    edge_set = set(zip(edges_df['source'], edges_df['target']))
    has_org3 = 'src_org3' in enriched.columns
    results = []

    for group in groups:
        if group == 'Unknown':
            continue

        group_nodes = nodes_df[nodes_df[group_col] == group]
        member_ids = set(group_nodes['사번'])
        node_count = len(member_ids)

        if node_count < 3:
            continue

        # ★ Ghost 포함 엣지 범위 (KPI 카드와 동일): source OR target이 그룹 소속
        group_edges = edges_df[
            (edges_df['source'].isin(member_ids)) | (edges_df['target'].isin(member_ids))
        ]
        group_enriched = enriched[
            (enriched['source'].isin(member_ids)) | (enriched['target'].isin(member_ids))
        ]

        n_edges = len(group_edges)
        if n_edges == 0:
            continue

        # ── 크로스-조직 비율: 3개 레벨 모두 계산 ──
        cross_org1 = (group_enriched['src_org1'] != group_enriched['tgt_org1']).sum()
        cross_org2 = (group_enriched['src_org2'] != group_enriched['tgt_org2']).sum()
        cross_org1_ratio = round(cross_org1 / n_edges, 4)
        cross_org2_ratio = round(cross_org2 / n_edges, 4)

        if has_org3:
            cross_org3 = (group_enriched['src_org3'] != group_enriched['tgt_org3']).sum()
            cross_org3_ratio = round(cross_org3 / n_edges, 4)
        else:
            cross_org3_ratio = cross_org2_ratio

        # ── 상호 선정 비율 (Core-Core 기준) ──
        # 조직 내부의 담합/호혜성을 측정하기 위해 멤버 간 관계로 한정
        core_group_edges = group_edges[group_edges['source'].isin(member_ids) & group_edges['target'].isin(member_ids)]
        if not core_group_edges.empty:
            core_group_set = set(zip(core_group_edges['source'], core_group_edges['target']))
            recip_count = sum(1 for s, t in core_group_set if (t, s) in core_group_set)
            reciprocity = round(recip_count / len(core_group_set), 4)
        else:
            reciprocity = 0.0

        # ── 평균 평가자 수 (in-degree: 그룹 멤버가 받은 평가 수) ──
        # 분모: 해당 그룹의 총 인원 수 (node_count) - 0점자 포함
        in_edges = edges_df[edges_df['target'].isin(member_ids)]
        avg_eval = round(len(in_edges) / node_count, 1)

        # ── Gini (평가 부담 집중도 — 그룹 멤버의 out-degree) ──
        group_src_edges = edges_df[edges_df['source'].isin(member_ids)]
        out_degs = group_src_edges.groupby('source').size().reindex(member_ids, fill_value=0).tolist()
        gini = _gini(out_degs)

        results.append({
            'group_name': group,
            'member_count': node_count,
            'cross_org1_ratio': cross_org1_ratio,
            'cross_org2_ratio': cross_org2_ratio,
            'cross_org3_ratio': cross_org3_ratio,
            'reciprocity': reciprocity,
            'avg_evaluators': avg_eval,
            'gini_coefficient': gini,
        })

    results.sort(key=lambda x: x['member_count'], reverse=True)
    return results

def calculate_dynamic_benchmarks(history_metrics: dict[int, dict]) -> dict:
    """
    모든 연도의 지표 분포를 분석하여 동적 임계값(Threshold)과 추세(History)를 계산합니다.
    (Method 1: 분포 기반 Threshold, Method 2: 연도별 추세)
    """
    if not history_metrics:
        return {}
    
    # DataFrame 변환 (행: 연도, 열: 지표)
    df = pd.DataFrame.from_dict(history_metrics, orient='index').sort_index()
    
    benchmarks = {}
    for col in df.columns:
        # 수치형 데이터만 처리
        if not np.issubdtype(df[col].dtype, np.number):
            continue
            
        series = df[col].dropna()
        if series.empty:
            continue
            
        benchmarks[col] = {
            "q1": float(series.quantile(0.25)) if not series.empty else 0.0,
            "median": float(series.median()) if not series.empty else 0.0,
            "q3": float(series.quantile(0.75)) if not series.empty else 0.0,
            "total_avg": float(series.mean()) if not series.empty else 0.0,
            "min": float(series.min()) if not series.empty else 0.0,
            "max": float(series.max()) if not series.empty else 0.0,
            "history": [x if not (pd.isna(x) or np.isinf(x)) else 0.0 for x in series.tolist()],
            "years": series.index.tolist()
        }
    return benchmarks

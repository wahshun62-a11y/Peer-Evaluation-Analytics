"""
network_builder.py — NetworkX 그래프를 생성합니다.

핵심 설계 결정:
  - 필터링된 노드/엣지 DataFrame으로부터 NetworkX DiGraph를 생성합니다.
  - Ghost Node(경계 노드) 지원: 필터 대상이 아닌 외부 연결 노드를 반투명으로 표시합니다.
  - Vis.js가 브라우저에서 직접 렌더링하므로, 서버에서 HTML을 생성할 필요가 없습니다.
"""
import networkx as nx
import pandas as pd
from config import COLORS


def build_graph(nodes_df: pd.DataFrame, edges_df: pd.DataFrame) -> nx.DiGraph:
    """
    필터링된 데이터로 NetworkX 방향 그래프(DiGraph)를 생성합니다.
    """
    G = nx.from_pandas_edgelist(
        edges_df, source='source', target='target',
        create_using=nx.DiGraph()
    )
    # 고립 노드 추가 (밀도 계산 등에서 분모가 됨)
    G.add_nodes_from(nodes_df['사번'])
    return G


def graph_to_vis_json(
    nodes_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    all_nodes_df: pd.DataFrame | None = None
) -> dict:
    """
    Vis.js 네트워크 그래프에 필요한 JSON 데이터를 생성합니다.
    
    ★ Ghost Node 지원:
      - nodes_df: 필터로 선택된 '핵심' 노드
      - all_nodes_df: HR 정보가 포함된 전체 노드 (Ghost 노드 정보 조회용)
      - edges_df에 등장하지만 nodes_df에 없는 노드 → Ghost Node로 표시
    """
    # 조직별 색상 매핑
    unique_orgs = nodes_df['ORG1_OP'].unique()
    color_map = {org: COLORS[i % len(COLORS)] for i, org in enumerate(unique_orgs)}

    core_ids = set(nodes_df['사번'])

    # Ghost 노드 수집: 엣지에 등장하지만 핵심 노드가 아닌 것
    edge_ids = set(edges_df['source'].tolist() + edges_df['target'].tolist())
    ghost_ids = edge_ids - core_ids

    # Ghost 노드 정보 조회
    ghost_info = {}
    if all_nodes_df is not None and len(ghost_ids) > 0:
        ghost_rows = all_nodes_df[all_nodes_df['사번'].isin(ghost_ids)]
        for _, row in ghost_rows.iterrows():
            ghost_info[row['사번']] = row

    vis_nodes = []
    # 핵심 노드 (정상 표시)
    for _, row in nodes_df.iterrows():
        vis_nodes.append({
            "id": row['사번'],
            "label": f"{row['성명']}",
            "title": (
                f"성명: {row['성명']}\n"
                f"사번: {row['사번']}\n"
                f"ORG1: {row['ORG1_OP']}\n"
                f"ORG2: {row['ORG2_OP']}\n"
                f"직군: {row.get('JOB_FAMILY_CODE', '-')}\n"
                f"직급: {row.get('GRADE', '-')}"
            ),
            "color": color_map.get(row['ORG1_OP'], '#97C2FC'),
            "org1": row['ORG1_OP'],
            "isGhost": False,
        })

    # Ghost 노드 (반투명 표시)
    for gid in ghost_ids:
        info = ghost_info.get(gid, {})
        org1 = info.get('ORG1_OP', 'Unknown') if isinstance(info, pd.Series) else info.get('ORG1_OP', 'Unknown')
        name = info.get('성명', str(gid)) if isinstance(info, pd.Series) else str(gid)
        vis_nodes.append({
            "id": gid,
            "label": f"{name}",
            "title": f"[외부 연결] ORG1: {org1}",
            "color": {
                "background": "rgba(180,180,180,0.3)",
                "border": "rgba(120,120,120,0.5)",
            },
            "org1": org1,
            "isGhost": True,
            "borderDashes": [5, 5],
            "font": {"color": "rgba(100,100,100,0.6)"},
        })

    vis_edges = []
    for _, row in edges_df.iterrows():
        src, tgt = row['source'], row['target']
        is_cross = (src in ghost_ids) or (tgt in ghost_ids)
        vis_edges.append({
            "from": src,
            "to": tgt,
            "dashes": is_cross,
            "color": {"color": "rgba(150,150,150,0.4)"} if is_cross else {"color": "rgba(100,100,100,0.6)"},
        })

    return {
        "nodes": vis_nodes,
        "edges": vis_edges,
        "summary": {
            "node_count": len([n for n in vis_nodes if not n.get('isGhost')]),
            "edge_count": len(vis_edges),
            "ghost_count": len(ghost_ids),
        },
        "color_legend": {org: color for org, color in color_map.items()},
    }

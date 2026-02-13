import sys
import os
import pandas as pd
import numpy as np

# backend 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.data_loader import prepare_combined_network_data, filter_network_data
from services.network_builder import build_graph
from services.metrics_calculator import calculate_system_health_metrics, calculate_subgroup_metrics

def verify_data_integrity(years=[2025]):
    print(f"--- Metric Verification Start (Years: {years}) ---")
    
    # 1. 데이터 로드
    raw_edges, all_nodes = prepare_combined_network_data(years)
    if raw_edges is None:
        print("Error: No data found.")
        return

    # 2. 전체 필터링 (테스트를 위해 전체 조직 선택)
    nodes, edges = filter_network_data(all_nodes, raw_edges, [], [], [], [])
    G = build_graph(nodes, edges)
    
    # 3. 전체 지표 계산
    overall_metrics = calculate_system_health_metrics(G, nodes, edges)
    print(f"\n[Overall Metrics]")
    print(f"  Avg Evaluators: {overall_metrics['avg_evaluators']}")
    print(f"  Gini Coefficient: {overall_metrics['gini_coefficient']}")
    print(f"  Reciprocity: {overall_metrics['reciprocity']}")
    print(f"  Participation Density: {overall_metrics['participation_density']}")

    # 4. 하위 조직별 지표 계산 (ORG2_OP 기준)
    subgroup_metrics = calculate_subgroup_metrics(nodes, edges, G, "ORG2_OP")
    
    print(f"\n[Subgroup Comparison (ORG2_OP)]")
    total_sub_members = 0
    total_sub_evals = 0
    weighted_avg_evals = 0
    
    for sub in subgroup_metrics:
        sub_members = sub['member_count']
        sub_avg = sub['avg_evaluators']
        total_sub_members += sub_members
        total_sub_evals += round(sub_avg * sub_members)
        print(f"  - {sub['group_name']}: Members={sub_members}, Avg={sub_avg}")

    # 5. 정합성 검증
    calculated_overall_avg = round(total_sub_evals / total_sub_members, 1) if total_sub_members > 0 else 0
    
    print(f"\n[Integrity Results]")
    print(f"  Overall Avg Evaluators (from KPI): {overall_metrics['avg_evaluators']}")
    print(f"  Calculated Weighted Avg from Subgroups: {calculated_overall_avg}")
    
    diff = abs(overall_metrics['avg_evaluators'] - calculated_overall_avg)
    if diff <= 0.1:
        print("  >>> SUCCESS: Overall average matches weighted average of subgroups.")
    else:
        print(f"  >>> FAILURE: Discrepancy detected! Diff={round(diff, 2)}")

    # Gini 검증 (논리적 확인)
    # Gini는 하위 조직의 가중평균과 일치할 의무는 없으나, 전체 분포의 Gini가 비정상적인지 확인
    if 0 <= overall_metrics['gini_coefficient'] <= 1:
        print("  >>> SUCCESS: Gini coefficient is within valid range (0~1).")
    else:
        print("  >>> FAILURE: Gini coefficient is out of range!")

if __name__ == "__main__":
    verify_data_integrity()

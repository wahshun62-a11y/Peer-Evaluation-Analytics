/**
 * network-graph.js — Vis.js 네트워크 그래프 렌더링
 *
 * ★ 개선 사항:
 *   1. 연결 수(Degree)에 비례한 노드 크기 조절
 *   2. BarnesHut 물리 엔진 적용으로 대규모 그래프 레이아웃 최적화
 *   3. 노드 선택 시 연결된 노드/엣지만 하이라이트 (Focus 모드)
 *   4. 가독성 높은 폰트 및 화살표 스타일 적용
 */
const NetworkGraph = (() => {

    let _network = null;
    let _allNodes = null;
    let _allEdges = null;

    function render(data) {
        const container = document.getElementById('network-container');

        if (!data || !data.nodes || data.nodes.length === 0) {
            container.innerHTML = '<p class="empty-msg">네트워크 데이터가 없습니다.</p>';
            return;
        }

        // 범례 렌더링
        const legendEl = document.getElementById('network-legend');
        if (data.color_legend) {
            let legendHtml = '<div class="legend-items">';
            Object.entries(data.color_legend).forEach(([org, color]) => {
                legendHtml += `<span class="legend-item"><span class="legend-dot" style="background:${color}"></span>${org}</span>`;
            });
            legendHtml += `<span class="legend-item"><span class="legend-dot" style="background:rgba(180,180,180,0.4); border:1.5px dashed #999"></span>외부 연결(Ghost)</span>`;
            legendHtml += '</div>';
            legendHtml += `<p class="legend-summary">노드 ${data.summary.node_count}명 · 엣지 ${data.summary.edge_count}건 · Ghost ${data.summary.ghost_count || 0}명</p>`;
            legendEl.innerHTML = legendHtml;
        }

        // --- 1. Degree(연결수) 계산 ---
        const degreeMap = {};
        data.edges.forEach(e => {
            degreeMap[e.from] = (degreeMap[e.from] || 0) + 1;
            degreeMap[e.to] = (degreeMap[e.to] || 0) + 1;
        });

        // --- 2. Vis.js 데이터 세트 준비 ---
        _allNodes = new vis.DataSet(data.nodes.map(n => {
            const deg = degreeMap[n.id] || 1;
            const size = n.isGhost ? 8 : (10 + Math.sqrt(deg) * 3); // Degree 비례 크기

            const node = {
                id: n.id,
                label: n.label,
                title: n.title,
                size: size,
                color: n.isGhost ? {
                    background: 'rgba(230,230,230,0.5)',
                    border: 'rgba(150,150,150,0.5)',
                    highlight: { background: '#eee', border: '#999' }
                } : {
                    background: n.color,
                    border: n.color,
                    highlight: { background: n.color, border: '#333' }
                },
                font: {
                    size: 11,
                    color: n.isGhost ? '#999' : '#333',
                    strokeWidth: 2,
                    strokeColor: '#ffffff'
                }
            };
            if (n.isGhost) {
                node.borderDashes = [4, 4];
                node.opacity = 0.6;
            }
            return node;
        }));

        _allEdges = new vis.DataSet(data.edges.map(e => ({
            from: e.from,
            to: e.to,
            dashes: e.dashes || false,
            width: 1,
            color: { color: e.dashes ? '#ccc' : '#bbb', opacity: 0.6, highlight: '#002D80' },
            arrows: { to: { enabled: true, scaleFactor: 0.4 } }, // 화살표 크기 축소
            smooth: { type: 'curvedCW', roundness: 0.1 } // 곡선 엣지
        })));

        const options = {
            nodes: { shape: 'dot' },
            physics: {
                solver: 'barnesHut',
                barnesHut: {
                    gravitationalConstant: -3000,
                    centralGravity: 0.3,
                    springLength: 95,
                    springConstant: 0.04,
                    damping: 0.09
                },
                stabilization: { iterations: 200 }
            },
            interaction: {
                hover: true,
                tooltipDelay: 200,
                hideEdgesOnDrag: true
            }
        };

        if (_network) _network.destroy();
        _network = new vis.Network(container, { nodes: _allNodes, edges: _allEdges }, options);

        // --- 3. 인터랙션: 클릭 시 하이라이트 ---
        _network.on("click", (params) => {
            if (params.nodes.length > 0) {
                const selectedId = params.nodes[0];
                _highlightConnections(selectedId);
            } else {
                _resetHighlight();
            }
        });
    }

    function _highlightConnections(nodeId) {
        const connectedNodes = _network.getConnectedNodes(nodeId);
        const connectedEdges = _network.getConnectedEdges(nodeId);

        // 모든 노드/엣지 페이드 아웃
        const updateNodes = [];
        _allNodes.forEach(node => {
            const isRelevant = (node.id === nodeId || connectedNodes.includes(node.id));
            updateNodes.push({
                id: node.id,
                opacity: isRelevant ? 1 : 0.1,
                font: { color: isRelevant ? (node.isGhost ? '#999' : '#333') : 'rgba(0,0,0,0)' }
            });
        });

        const updateEdges = [];
        _allEdges.forEach(edge => {
            const isRelevant = connectedEdges.includes(edge.id);
            updateEdges.push({
                id: edge.id,
                color: { opacity: isRelevant ? 1 : 0.05 }
            });
        });

        _allNodes.update(updateNodes);
        _allEdges.update(updateEdges);
    }

    function _resetHighlight() {
        const updateNodes = [];
        _allNodes.forEach(node => {
            updateNodes.push({
                id: node.id,
                opacity: node.isGhost ? 0.6 : 1,
                font: { color: node.isGhost ? '#999' : '#333' }
            });
        });

        const updateEdges = [];
        _allEdges.forEach(edge => {
            updateEdges.push({
                id: edge.id,
                color: { opacity: 0.6 }
            });
        });

        _allNodes.update(updateNodes);
        _allEdges.update(updateEdges);
    }

    return { render };
})();

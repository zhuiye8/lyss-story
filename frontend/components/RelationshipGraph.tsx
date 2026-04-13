"use client";

import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import type { CharacterNode, RelationshipEdge } from "@/types";

interface Props {
  nodes: CharacterNode[];
  edges: RelationshipEdge[];
  width?: number;
  height?: number;
}

const ROLE_COLORS: Record<string, string> = {
  protagonist: "#f59e0b",
  antagonist: "#ef4444",
  supporting: "#6b7280",
};

const ROLE_RADIUS: Record<string, number> = {
  protagonist: 28,
  antagonist: 24,
  supporting: 18,
};

const ROLE_LABEL: Record<string, string> = {
  protagonist: "主",
  antagonist: "敌",
};

export default function RelationshipGraph({
  nodes,
  edges,
  width = 700,
  height = 500,
}: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [tooltip, setTooltip] = useState<{
    x: number; y: number; text: string; detail: string;
  } | null>(null);

  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const g = svg.append("g");

    // Zoom
    svg.call(
      d3.zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.3, 3])
        .on("zoom", (event) => g.attr("transform", event.transform))
    );

    const nodeData = nodes.map((n) => ({ ...n })) as any[];
    const nodeIds = new Set(nodeData.map((n: any) => n.id));
    const linkData = edges
      .filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target))
      .map((e, i) => ({ ...e, _index: i })) as any[];

    // Count parallel edges between same pair to offset curves
    const pairIndex = new Map<string, number>();
    const pairCount = new Map<string, number>();
    linkData.forEach((l: any) => {
      const key = [l.source, l.target].sort().join("||");
      pairCount.set(key, (pairCount.get(key) || 0) + 1);
    });
    linkData.forEach((l: any) => {
      const key = [l.source, l.target].sort().join("||");
      const idx = pairIndex.get(key) || 0;
      l._curveIndex = idx;
      l._curveTotal = pairCount.get(key) || 1;
      pairIndex.set(key, idx + 1);
    });

    // Simulation
    const simulation = d3.forceSimulation(nodeData)
      .force("link", d3.forceLink(linkData).id((d: any) => d.id).distance(200))
      .force("charge", d3.forceManyBody().strength(-600))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide(55));

    // Arrow marker
    svg.append("defs").append("marker")
      .attr("id", "arrow")
      .attr("viewBox", "0 -4 8 8")
      .attr("refX", 38).attr("refY", 0)
      .attr("markerWidth", 5).attr("markerHeight", 5)
      .attr("orient", "auto")
      .append("path").attr("d", "M0,-4L8,0L0,4").attr("fill", "#bbb");

    // Links — curved paths, NO text labels
    const link = g.append("g")
      .selectAll("path")
      .data(linkData)
      .join("path")
      .attr("fill", "none")
      .attr("stroke", "#bbb")
      .attr("stroke-width", 1.5)
      .attr("stroke-opacity", 0.6)
      .attr("marker-end", "url(#arrow)")
      .style("cursor", "pointer")
      .on("mouseenter", function (event, d: any) {
        d3.select(this).attr("stroke", "#f59e0b").attr("stroke-width", 3).attr("stroke-opacity", 1);
        const [mx, my] = d3.pointer(event, svgRef.current);
        setTooltip({ x: mx, y: my, text: d.predicate, detail: d.detail || "" });
      })
      .on("mouseleave", function () {
        d3.select(this).attr("stroke", "#bbb").attr("stroke-width", 1.5).attr("stroke-opacity", 0.6);
        setTooltip(null);
      });

    // Nodes
    const node = g.append("g")
      .selectAll("g")
      .data(nodeData)
      .join("g")
      .call(d3.drag<SVGGElement, any>()
        .on("start", (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x; d.fy = d.y;
        })
        .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
        .on("end", (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null; d.fy = null;
        }) as any);

    // Circle
    node.append("circle")
      .attr("r", (d: any) => ROLE_RADIUS[d.role] || 18)
      .attr("fill", (d: any) => ROLE_COLORS[d.role] || "#6b7280")
      .attr("stroke", "#fff")
      .attr("stroke-width", 2.5)
      .style("cursor", "grab");

    // Role icon inside circle
    node.append("text")
      .text((d: any) => ROLE_LABEL[d.role] || "")
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .attr("font-size", 12)
      .attr("font-weight", "bold")
      .attr("fill", "#fff")
      .style("pointer-events", "none");

    // Name below circle
    node.append("text")
      .text((d: any) => d.name)
      .attr("text-anchor", "middle")
      .attr("dy", (d: any) => (ROLE_RADIUS[d.role] || 18) + 16)
      .attr("font-size", 13)
      .attr("font-weight", 600)
      .attr("fill", "#333")
      .style("pointer-events", "none");

    // Tick
    simulation.on("tick", () => {
      link.attr("d", (d: any) => {
        const dx = d.target.x - d.source.x;
        const dy = d.target.y - d.source.y;
        const len = Math.sqrt(dx * dx + dy * dy) || 1;
        // Offset for parallel edges
        const offset = (d._curveIndex - (d._curveTotal - 1) / 2) * 35;
        if (Math.abs(offset) < 5) {
          return `M${d.source.x},${d.source.y}L${d.target.x},${d.target.y}`;
        }
        const mx = (d.source.x + d.target.x) / 2 + (-dy / len) * offset;
        const my = (d.source.y + d.target.y) / 2 + (dx / len) * offset;
        return `M${d.source.x},${d.source.y}Q${mx},${my},${d.target.x},${d.target.y}`;
      });

      node.attr("transform", (d: any) => `translate(${d.x},${d.y})`);
    });

    return () => { simulation.stop(); };
  }, [nodes, edges, width, height]);

  if (nodes.length === 0) {
    return <p className="text-gray-500 text-sm py-8 text-center">暂无角色关系数据</p>;
  }

  return (
    <div className="relative">
      <svg
        ref={svgRef}
        width={width}
        height={height}
        className="border rounded-lg bg-gray-50"
        style={{ maxWidth: "100%" }}
      />
      {tooltip && (
        <div
          className="absolute z-10 bg-gray-900 text-white text-xs rounded-lg px-3 py-2 shadow-lg pointer-events-none"
          style={{ left: tooltip.x + 12, top: tooltip.y - 10 }}
        >
          <p className="font-bold">{tooltip.text}</p>
          {tooltip.detail && <p className="text-gray-400 mt-0.5">{tooltip.detail}</p>}
        </div>
      )}
      <p className="text-xs text-gray-400 text-center mt-2">
        悬停连线查看关系 · 拖拽节点调整布局 · 滚轮缩放
      </p>
    </div>
  );
}

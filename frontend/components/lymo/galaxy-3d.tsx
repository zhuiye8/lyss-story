"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import dynamic from "next/dynamic";
import * as THREE from "three";

import type { CharacterWithArc, KnowledgeGraphData } from "@/types";

// react-force-graph-3d must be SSR-disabled
const ForceGraph3D = dynamic(
  () => import("react-force-graph-3d").then((m) => m.default),
  { ssr: false }
);

const ROLE_COLOR: Record<string, string> = {
  protagonist: "#d4a84b",
  antagonist: "#c73e3a",
  supporting: "#5a8fd4",
};

const PRED_COLOR = (predicate: string): string => {
  const p = predicate || "";
  if (/信任|保护|爱|恋|依赖|支持/.test(p)) return "#5aa67d"; // jade
  if (/敌|恨|怒|杀|害/.test(p)) return "#c73e3a"; // vermilion
  if (/疑|惧|怕/.test(p)) return "#9575cd";
  if (/师|徒|父|母|兄|姐|血/.test(p)) return "#d4a84b"; // gold - family
  return "#5a8fd4"; // stellar default
};

interface Galaxy3DProps {
  characters: CharacterWithArc[];
  kg: KnowledgeGraphData;
  onSelectCharacter?: (character: any) => void;
  bibleChars?: any[];
}

export function Galaxy3D({ characters, kg, onSelectCharacter, bibleChars }: Galaxy3DProps) {
  const [dim, setDim] = useState({ w: 800, h: 600 });
  const wrapperRef = useRef<HTMLDivElement>(null);
  const fgRef = useRef<any>(null);

  useEffect(() => {
    if (!wrapperRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setDim({ w: entry.contentRect.width, h: entry.contentRect.height });
      }
    });
    observer.observe(wrapperRef.current);
    return () => observer.disconnect();
  }, []);

  const graphData = useMemo(() => {
    const bibleMap = new Map<string, any>();
    (bibleChars || []).forEach((c: any) => bibleMap.set(c.character_id, c));

    const nodes = characters.map((c: any) => {
      const bible = bibleMap.get(c.character_id) || {};
      return {
        id: c.character_id,
        name: c.name,
        role: c.role,
        color: ROLE_COLOR[c.role] || "#6b7785",
        val: c.role === "protagonist" ? 12 : c.role === "antagonist" ? 10 : 6,
        ...bible,
        ...c,
      };
    });

    const idSet = new Set(nodes.map((n) => n.id));
    const links = (kg.edges || [])
      .filter((e: any) => idSet.has(e.source) && idSet.has(e.target))
      .map((e: any) => ({
        source: e.source,
        target: e.target,
        predicate: e.predicate,
        color: PRED_COLOR(e.predicate),
        detail: e.detail,
      }));

    return { nodes, links };
  }, [characters, kg, bibleChars]);

  // Custom node: glowing sphere
  const nodeThreeObject = useMemo(() => {
    const textureCache = new Map<string, THREE.Texture>();

    return (node: any) => {
      const color = node.color || "#6b7785";
      const size = node.val || 6;

      const group = new THREE.Group();

      // Core sphere with emissive
      const geometry = new THREE.SphereGeometry(size, 32, 32);
      const material = new THREE.MeshStandardMaterial({
        color,
        emissive: color,
        emissiveIntensity: 0.5,
        roughness: 0.2,
        metalness: 0.3,
      });
      const sphere = new THREE.Mesh(geometry, material);
      group.add(sphere);

      // Outer glow halo (sprite)
      const haloColor = new THREE.Color(color);
      const haloCanvas = document.createElement("canvas");
      haloCanvas.width = 128;
      haloCanvas.height = 128;
      const ctx = haloCanvas.getContext("2d")!;
      const gradient = ctx.createRadialGradient(64, 64, 8, 64, 64, 64);
      gradient.addColorStop(
        0,
        `rgba(${haloColor.r * 255}, ${haloColor.g * 255}, ${haloColor.b * 255}, 0.5)`
      );
      gradient.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, 128, 128);
      const haloTexture = new THREE.CanvasTexture(haloCanvas);
      const haloMat = new THREE.SpriteMaterial({
        map: haloTexture,
        blending: THREE.AdditiveBlending,
        transparent: true,
        depthWrite: false,
      });
      const halo = new THREE.Sprite(haloMat);
      halo.scale.set(size * 4, size * 4, 1);
      group.add(halo);

      // Name label sprite
      const name = node.name || "";
      let labelTexture = textureCache.get(name);
      if (!labelTexture) {
        const labelCanvas = document.createElement("canvas");
        labelCanvas.width = 512;
        labelCanvas.height = 128;
        const lctx = labelCanvas.getContext("2d")!;
        lctx.fillStyle = "rgba(15, 20, 25, 0)";
        lctx.fillRect(0, 0, 512, 128);
        lctx.font =
          'bold 56px "Noto Serif SC", "Source Han Serif SC", serif';
        lctx.textAlign = "center";
        lctx.textBaseline = "middle";
        lctx.shadowColor = "rgba(0,0,0,0.9)";
        lctx.shadowBlur = 16;
        lctx.shadowOffsetX = 0;
        lctx.shadowOffsetY = 2;
        lctx.fillStyle = color;
        lctx.fillText(name, 256, 64);
        labelTexture = new THREE.CanvasTexture(labelCanvas);
        textureCache.set(name, labelTexture);
      }

      const labelMat = new THREE.SpriteMaterial({
        map: labelTexture,
        transparent: true,
        depthTest: false,
        depthWrite: false,
      });
      const labelSprite = new THREE.Sprite(labelMat);
      labelSprite.scale.set(size * 4.5, size * 1.1, 1);
      labelSprite.position.y = size + 3;
      group.add(labelSprite);

      return group;
    };
  }, []);

  // Link particle effect for emphasis
  const linkParticles = (link: any) => {
    if (!link.predicate) return 0;
    return 2; // particles along the line for motion
  };

  return (
    <div ref={wrapperRef} className="relative w-full h-full bg-lymo-ink-950 overflow-hidden">
      {/* Background starfield */}
      <div className="absolute inset-0 star-field opacity-60 pointer-events-none" />

      <ForceGraph3D
        ref={fgRef}
        graphData={graphData}
        width={dim.w}
        height={dim.h}
        backgroundColor="rgba(0,0,0,0)"
        nodeThreeObject={nodeThreeObject}
        nodeThreeObjectExtend={false}
        nodeLabel={(n: any) =>
          `<div style="padding:6px 10px;background:#1d252f;border:1px solid #2d3d4e;border-radius:6px;font-family:'Noto Sans SC';color:#e8ecef;">
            <div style="font-weight:600;color:${n.color}">${n.name}</div>
            <div style="font-size:11px;color:#a8b3bd">${n.role === "protagonist" ? "主角" : n.role === "antagonist" ? "反派" : "配角"}</div>
          </div>`
        }
        linkColor={(l: any) => l.color || "#2d3d4e"}
        linkOpacity={0.5}
        linkWidth={1.2}
        linkDirectionalParticles={linkParticles}
        linkDirectionalParticleSpeed={0.006}
        linkDirectionalParticleWidth={2}
        linkDirectionalParticleColor={(l: any) => l.color || "#5a8fd4"}
        linkLabel={(l: any) =>
          `<div style="padding:4px 8px;background:#1d252f;border-radius:4px;color:${l.color};font-size:11px">${l.predicate || ""}${l.detail ? ` · ${l.detail}` : ""}</div>`
        }
        onNodeClick={(node: any) => {
          // Fly-to camera
          if (fgRef.current) {
            const distance = 80;
            const distRatio = 1 + distance / Math.hypot(node.x || 0, node.y || 0, node.z || 0);
            fgRef.current.cameraPosition(
              {
                x: (node.x || 0) * distRatio,
                y: (node.y || 0) * distRatio,
                z: (node.z || 0) * distRatio,
              },
              node,
              1500
            );
          }
          onSelectCharacter?.(node);
        }}
        cooldownTicks={100}
        enableNodeDrag
      />
    </div>
  );
}

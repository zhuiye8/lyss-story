import { cn } from "@/lib/utils";

/**
 * Each agent has a unique color so logs / cost dashboards feel consistent.
 */
export const AGENT_PALETTE: Record<string, { bg: string; text: string; label: string }> = {
  // Init pipeline
  concept:           { bg: "bg-lymo-vermilion-500/15", text: "text-lymo-vermilion-300", label: "Concept" },
  world_builder:     { bg: "bg-lymo-stellar-500/15",   text: "text-lymo-stellar-400",   label: "World" },
  character_designer:{ bg: "bg-lymo-gold-500/15",      text: "text-lymo-gold-400",      label: "Character" },
  outline_planner:   { bg: "bg-lymo-jade-500/15",      text: "text-lymo-jade-400",      label: "Outline" },
  director:          { bg: "bg-lymo-vermilion-500/20", text: "text-lymo-vermilion-300", label: "Director" },
  outline_parser:    { bg: "bg-slate-500/15",          text: "text-slate-300",          label: "Parser" },
  outline_enricher:  { bg: "bg-slate-500/15",          text: "text-slate-300",          label: "Enricher" },
  // Chapter pipeline
  world:         { bg: "bg-lymo-stellar-500/15", text: "text-lymo-stellar-400", label: "World" },
  planner:       { bg: "bg-lymo-jade-500/15",    text: "text-lymo-jade-400",    label: "Planner" },
  camera:        { bg: "bg-purple-500/15",       text: "text-purple-300",       label: "Camera" },
  writer:        { bg: "bg-lymo-vermilion-500/15",text: "text-lymo-vermilion-300",label: "Writer" },
  consistency:   { bg: "bg-lymo-gold-500/15",    text: "text-lymo-gold-400",    label: "Consistency" },
  titler:        { bg: "bg-pink-500/15",         text: "text-pink-300",         label: "Titler" },
  character_arc: { bg: "bg-lymo-gold-500/20",    text: "text-lymo-gold-400",    label: "Arc" },
  // Scene
  scene_splitter:   { bg: "bg-cyan-500/15",     text: "text-cyan-300",    label: "SceneSplit" },
  scene_writer:     { bg: "bg-lymo-vermilion-500/20", text: "text-lymo-vermilion-300", label: "SceneWrite" },
  scene_consistency:{ bg: "bg-lymo-gold-500/10", text: "text-lymo-gold-400", label: "SceneCheck" },
  extractor:         { bg: "bg-emerald-500/15",  text: "text-emerald-300",  label: "Extractor" },
  character_reviewer:{ bg: "bg-amber-500/15",    text: "text-amber-300",    label: "Reviewer" },
};

export function AgentChip({ name, className }: { name: string; className?: string }) {
  const p = AGENT_PALETTE[name] || {
    bg: "bg-muted",
    text: "text-muted-foreground",
    label: name,
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium border border-border/50",
        p.bg,
        p.text,
        className
      )}
    >
      {p.label}
    </span>
  );
}

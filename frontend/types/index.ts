export interface StoryResponse {
  story_id: string;
  title: string;
  theme: string;
  status: string;
  chapter_count: number;
  is_published?: boolean;
}

export interface ArcOutline {
  name: string;
  chapter_start: number;
  chapter_end: number;
  goal: string;
  key_milestones: string[];
}

export interface LongOutline {
  target_chapters: number;
  arcs: ArcOutline[];
}

export interface StoryBible {
  title: string;
  genre: string;
  setting: string;
  world_rules: { rule_id: string; description: string }[];
  power_system?: { name: string; levels: string[]; rules: string[] };
  style_guide: {
    tone: string;
    pov_preference: string;
    language_style: string;
    dialogue_style: string;
  };
  taboos: string[];
  characters: CharacterProfile[];
  initial_conflicts: string[];
  planned_arc: string;
  long_outline?: LongOutline | null;
}

export interface CharacterProfile {
  character_id: string;
  name: string;
  role: string;
  personality: string;
  background: string;
  goals: string[];
}

export interface ChapterSummary {
  chapter_num: number;
  title: string;
  pov: string;
  word_count: number;
  has_warnings: boolean;
  is_published?: boolean;
}

export interface ChapterDetail extends ChapterSummary {
  story_id: string;
  content: string;
  events_covered: string[];
  consistency_warnings: string[];
}

export interface GenerationStatus {
  story_id: string;
  status: string;
  current_chapter: number | null;
  error_message: string | null;
}

export interface ChapterVersionSummary {
  id: number;
  version_num: number;
  title: string;
  pov: string;
  word_count: number;
  feedback: string;
  created_at: string;
}

export interface ChapterVersionDetail extends ChapterVersionSummary {
  story_id: string;
  chapter_num: number;
  content: string;
}

// --- Visualization types ---

export interface CharacterNode {
  id: string;
  name: string;
  role: string;
}

export interface RelationshipEdge {
  source: string;
  target: string;
  predicate: string;
  detail: string;
  valid_from: number;
  valid_to: number | null;
}

export interface KnowledgeGraphData {
  nodes: CharacterNode[];
  edges: RelationshipEdge[];
}

export interface StoryEvent {
  event_id: string;
  time: number;
  description: string;
  actors: string[];
  location: string;
  pre_events: string[];
  effects: string[];
  visibility: { public: boolean; known_to: string[] } | string;
}

export interface CharacterWithArc {
  character_id: string;
  name: string;
  role: string;
  personality: string;
  background: string;
  goals: string[];
  arc_summary: Record<string, unknown> | null;
  arc_name: string | null;
}

// --- StoryBible V2 types ---

export interface SpecialAbilityV2 {
  name: string;
  description: string;
  functions: string[];
}

export interface FactionV2 {
  name: string;
  description: string;
  stance: string;
}

export interface CharacterProfileV2 {
  character_id: string;
  name: string;
  role: string;
  gender?: string;
  age?: string;
  appearance?: string;
  personality: string;
  background: string;
  goals: string[];
  weaknesses?: string[];
  arc_plan?: string;
  relationships?: { target_id: string; target_name: string; relation_type: string; description: string }[];
  status?: string;
}

export interface VolumeOutlineV2 {
  volume_num: number;
  volume_name: string;
  chapter_start: number;
  chapter_end: number;
  estimated_words?: number;
  main_plot: string;
  subplots: string[];
  conflicts: string[];
  new_characters: string[];
  key_locations: string[];
  climax_event: string;
}

export interface WorldSettingV2 {
  world_background: string;
  special_ability?: SpecialAbilityV2 | null;
  factions?: FactionV2[];
  power_system?: { name: string; levels: string[]; rules: string[] };
  world_rules?: { rule_id: string; description: string }[];
}

export interface StoryBibleV2 extends StoryBible {
  bible_version?: number;
  tone?: string;
  one_line_summary?: string;
  synopsis?: string;
  inspiration?: string;
  world?: WorldSettingV2;
  protagonist?: CharacterProfileV2 | null;
  antagonist?: CharacterProfileV2 | null;
  supporting_characters?: CharacterProfileV2[];
  primary_pov?: string;
  volumes?: VolumeOutlineV2[];
}

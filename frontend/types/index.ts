export interface StoryResponse {
  story_id: string;
  title: string;
  theme: string;
  status: string;
  chapter_count: number;
  is_published?: boolean;
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

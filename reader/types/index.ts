export interface Book {
  id: string;
  title: string;
  theme: string;
  chapter_count: number;
  updated_at: string;
}

export interface BookDetail {
  id: string;
  title: string;
  theme: string;
  genre: string;
  setting: string;
  characters: { name: string; role: string }[];
  chapters: {
    chapter_num: number;
    title: string;
    pov: string;
    word_count: number;
  }[];
}

export interface ChapterContent {
  story_id: string;
  story_title: string;
  chapter_num: number;
  title: string;
  pov: string;
  content: string;
  word_count: number;
  prev_chapter: number | null;
  next_chapter: number | null;
}

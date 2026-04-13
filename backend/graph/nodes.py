import logging

from backend.agents.camera import CameraAgent
from backend.agents.character_arc import CharacterArcAgent
from backend.agents.consistency import ConsistencyAgent
from backend.agents.director import DirectorAgent
from backend.agents.planner import PlotPlannerAgent
from backend.agents.titler import TitlerAgent
from backend.agents.world import WorldAgent
from backend.agents.writer import WriterAgent
from backend.llm.client import LLMClient
from backend.memory.chapter_extractor import ChapterExtractor
from backend.memory.layered_memory import LayeredMemory
from backend.memory.plot_dedup import PlotDedupStore
from backend.models.graph_state import ChapterGraphState, InitGraphState
from backend.progress import ProgressStore
from backend.storage.json_store import JSONStore
from backend.storage.sqlite_store import SQLiteStore
from backend.storage.vector_store import VectorStore

logger = logging.getLogger(__name__)


def _find_current_arc(long_outline: dict | None, chapter_num: int) -> dict | None:
    """Locate the arc covering the given chapter number.

    If chapter_num falls within an arc's [chapter_start, chapter_end] range,
    that arc is returned. If chapter_num exceeds the last arc's end (story
    overrun), the last arc is returned so the final-stage guidance still
    applies. Returns None if long_outline is missing or has no arcs.
    """
    if not long_outline:
        return None
    arcs = long_outline.get("arcs") or []
    if not arcs:
        return None
    for arc in arcs:
        start = arc.get("chapter_start")
        end = arc.get("chapter_end")
        if start is None or end is None:
            continue
        if start <= chapter_num <= end:
            return arc
    # Overrun: return last arc so final-stage guidance persists
    return arcs[-1]


def _normalize_visibility(event: dict) -> dict:
    """Ensure event visibility is structured {public, known_to}.

    Old events may have visibility as a string ("full"/"partial"/"hidden").
    This normalizes them to the new structured format for downstream use.
    """
    vis = event.get("visibility")
    if isinstance(vis, str):
        event["visibility"] = {"public": vis == "full", "known_to": []}
    elif not isinstance(vis, dict):
        event["visibility"] = {"public": True, "known_to": []}
    return event


def _split_chapter(draft: str, target_chars: int) -> list[str]:
    """Split a long draft into multiple chapters at natural break points.

    If the draft is within 1.3× target, return it as-is (single chapter).
    Otherwise split at *** scene markers first, then at paragraph boundaries.
    Each resulting chunk targets ~target_chars.
    """
    if len(draft) <= int(target_chars * 1.3):
        return [draft]

    # Split at scene markers (*** on its own line)
    scenes: list[str] = []
    for part in draft.split("***"):
        part = part.strip()
        if part:
            scenes.append(part)

    if len(scenes) < 2:
        # No scene markers — split at paragraph boundaries
        paragraphs = draft.split("\n\n")
        scenes = [p.strip() for p in paragraphs if p.strip()]

    # Greedy merge: combine adjacent scenes until reaching ~target_chars
    chapters: list[str] = []
    current = ""
    for scene in scenes:
        if current and len(current) + len(scene) + 10 > target_chars:
            chapters.append(current.strip())
            current = scene
        else:
            separator = "\n\n***\n\n" if current else ""
            current += separator + scene
    if current.strip():
        chapters.append(current.strip())

    # Safety: if any chunk is still > 2× target, do a hard paragraph split
    result: list[str] = []
    for ch in chapters:
        if len(ch) <= int(target_chars * 1.5):
            result.append(ch)
        else:
            # Hard split at paragraph boundary near target
            paras = ch.split("\n\n")
            buf = ""
            for p in paras:
                p = p.strip()
                if not p:
                    continue
                if buf and len(buf) + len(p) + 2 > target_chars:
                    result.append(buf.strip())
                    buf = p
                else:
                    buf += ("\n\n" + p if buf else p)
            if buf.strip():
                result.append(buf.strip())

    return result if result else [draft]


def create_init_nodes(llm: LLMClient, title: str = ""):
    """Create node functions for the story initialization graph."""

    async def generate_bible_node(state: InitGraphState) -> dict:
        agent = DirectorAgent(llm)
        bible = await agent.run(
            user_theme=state["user_theme"],
            user_requirements=state["user_requirements"],
            title=title,
            story_id=state["story_id"],
        )
        return {"story_bible": bible}

    async def extract_characters_node(state: InitGraphState) -> dict:
        bible = state["story_bible"]
        characters = bible.get("characters", [])

        # V2 fallback: if flat characters list is empty, extract from structured fields
        if not characters:
            from backend.models.story_bible import extract_characters_from_bible
            characters = extract_characters_from_bible(bible)

        # Ensure each character has an ID
        for i, c in enumerate(characters):
            if not c.get("character_id"):
                c["character_id"] = f"char_{i+1}"
        return {"characters": characters}

    async def init_world_node(state: InitGraphState) -> dict:
        bible = state["story_bible"]
        world_state = {
            "story_id": state["story_id"],
            "current_time": 0,
            "time_description": "故事开始",
            "global_flags": [],
            "locations": bible.get("locations", []),
            "active_character_ids": [
                c.get("character_id", f"char_{i}")
                for i, c in enumerate(state["characters"])
            ],
            "version": 0,
        }
        return {"initial_world_state": world_state}

    return generate_bible_node, extract_characters_node, init_world_node


def create_chapter_nodes(
    llm: LLMClient,
    sqlite: SQLiteStore,
    json_store: JSONStore,
    vector: VectorStore,
    progress_store: ProgressStore | None = None,
    layered_memory: LayeredMemory | None = None,
    chapter_extractor: ChapterExtractor | None = None,
    plot_dedup: PlotDedupStore | None = None,
):
    """Create node functions for the chapter generation graph."""

    def _enter(story_id: str, stage: str, detail: str = ""):
        if progress_store:
            progress_store.enter_stage(story_id, stage, detail)

    def _finish(story_id: str, stage: str, detail: str = ""):
        if progress_store:
            progress_store.finish_stage(story_id, stage, detail)

    async def load_context_node(state: ChapterGraphState) -> dict:
        story_id = state["story_id"]
        _enter(story_id, "load_context")
        bible = json_store.load_story_bible(story_id) or state.get("story_bible", {})
        world = await sqlite.get_world_state(story_id) or state.get("world_state", {})
        events = json_store.load_event_graph(story_id)
        characters = json_store.load_characters(story_id) or state.get("character_profiles", [])

        # Merge latest character arc summary into each character profile (B4.2)
        arc_count = 0
        for char in characters:
            cid = char.get("character_id")
            if not cid:
                continue
            try:
                latest = await sqlite.get_latest_character_arc(story_id, cid)
                if latest and latest.get("summary"):
                    char["arc_summary"] = latest["summary"]
                    char["arc_summary_arc_name"] = latest.get("arc_name", "")
                    arc_count += 1
            except Exception as e:
                logger.warning(f"[load_context] Failed to load arc for {cid}: {e}")

        detail = f"{len(events)}个事件, {len(characters)}个角色"
        if arc_count:
            detail += f", {arc_count}个弧线"
        _finish(story_id, "load_context", detail)
        logger.info(
            f"[load_context] Loaded context for story {story_id}, "
            f"{len(events)} events, {len(characters)} characters, {arc_count} arc summaries"
        )
        return {
            "story_bible": bible,
            "world_state": world,
            "event_history": events,
            "character_profiles": characters,
        }

    async def world_advance_node(state: ChapterGraphState) -> dict:
        _enter(state["story_id"], "world_advance", "调用World Agent...")
        agent = WorldAgent(llm)
        result = await agent.run(
            story_bible=state["story_bible"],
            world_state=state["world_state"],
            event_history=state["event_history"],
            character_profiles=state["character_profiles"],
            story_id=state["story_id"],
            chapter_num=state["chapter_num"],
        )

        # B5.2: Parse storylines and flatten events
        storylines = result.get("storylines") or []
        if storylines:
            # Flatten all storyline events into one new_events list
            new_events = []
            for sl in storylines:
                new_events.extend(sl.get("new_events", []))
        else:
            # Backward compat: old World output has flat new_events
            new_events = result.get("new_events", [])

        # Update world state
        world_state = state["world_state"].copy()
        world_state["current_time"] = result.get("updated_time", world_state.get("current_time", 0) + 1)
        world_state["time_description"] = result.get("time_description", "")

        updates = result.get("world_state_updates", {})
        # Ensure flags are strings (LLM may return dicts)
        def to_str(v) -> str:
            return v if isinstance(v, str) else str(v)
        existing_flags = [to_str(f) for f in world_state.get("global_flags", [])]
        add_flags = [to_str(f) for f in updates.get("global_flags_add", [])]
        remove_flags = [to_str(f) for f in updates.get("global_flags_remove", [])]
        flags = set(existing_flags)
        flags.update(add_flags)
        flags -= set(remove_flags)
        world_state["global_flags"] = list(flags)
        world_state["version"] = world_state.get("version", 0) + 1

        lines_label = f"{len(storylines)}线" if storylines else "单线"
        _finish(state["story_id"], "world_advance", f"生成{len(new_events)}个事件 ({lines_label})")
        logger.info(
            f"[world_advance] Generated {len(new_events)} events across {len(storylines) or 1} storylines, "
            f"time={world_state['current_time']}"
        )
        return {
            "new_events": new_events,
            "storylines": storylines,
            "world_state": world_state,
        }

    async def plot_plan_node(state: ChapterGraphState) -> dict:
        long_outline = (state.get("story_bible") or {}).get("long_outline")
        current_arc = _find_current_arc(long_outline, state["chapter_num"])
        arc_label = current_arc.get("name", "") if current_arc else "无大纲"

        # B4.1: Query for similar past plot patterns to avoid repetition
        similar_past = []
        if plot_dedup:
            arc_goal = current_arc.get("goal", "") if current_arc else ""
            query = f"{arc_goal} {state['story_bible'].get('planned_arc', '')}"
            try:
                similar_past = plot_dedup.find_similar(
                    story_id=state["story_id"],
                    query_text=query,
                    top_k=5,
                    exclude_recent=2,
                )
            except Exception as e:
                logger.warning(f"[plot_plan] Dedup query failed: {e}")

        dedup_label = f", 查重{len(similar_past)}条" if similar_past else ""
        _enter(state["story_id"], "plot_plan", f"调用Plot Planner... ({arc_label}{dedup_label})")
        agent = PlotPlannerAgent(llm)
        plot = await agent.run(
            story_bible=state["story_bible"],
            new_events=state["new_events"],
            chapter_num=state["chapter_num"],
            event_history=state["event_history"],
            current_arc=current_arc,
            similar_past_patterns=similar_past if similar_past else None,
            storylines=state.get("storylines") or None,
            story_id=state["story_id"],
        )
        _finish(state["story_id"], "plot_plan", plot.get("chapter_goal", "")[:30])
        logger.info(
            f"[plot_plan] Chapter {state['chapter_num']} arc={arc_label} "
            f"dedup={len(similar_past)} goal={plot.get('chapter_goal', '')[:50]}"
        )
        return {"plot_structure": plot}

    async def camera_decide_node(state: ChapterGraphState) -> dict:
        # Gather previous POVs from chapter history
        story_id = state["story_id"]
        chapters = await sqlite.list_chapters(story_id)
        previous_povs = [ch.get("pov", "") for ch in chapters]

        # Normalize event visibility for Camera consumption (B5.1)
        normalized_events = [_normalize_visibility(e) for e in (state.get("new_events") or [])]

        _enter(state["story_id"], "camera_decide", f"调用Camera Agent... ({len(normalized_events)}事件)")
        agent = CameraAgent(llm)
        decision = await agent.run(
            plot_structure=state["plot_structure"],
            character_profiles=state["character_profiles"],
            chapter_num=state["chapter_num"],
            previous_povs=previous_povs,
            new_events=normalized_events,
            story_id=state["story_id"],
        )

        # B5.3: Post-LLM visibility enforcement
        pov_id = decision.get("pov_character_id", "")
        valid_ids = {e.get("event_id") for e in normalized_events if e.get("event_id")}
        events_by_id = {e.get("event_id"): e for e in normalized_events if e.get("event_id")}

        def _is_visible_to_pov(event: dict) -> bool:
            vis = event.get("visibility", {})
            if isinstance(vis, dict):
                if vis.get("public"):
                    return True
                if pov_id in (vis.get("known_to") or []):
                    return True
            if pov_id in (event.get("actors") or []):
                return True
            return False

        # Validate and auto-correct: move wrongly-visible events to foreshadowing/hidden
        raw_visible = [eid for eid in decision.get("visible_events", []) if eid in valid_ids]
        raw_foreshadow = [eid for eid in decision.get("foreshadowing_events", []) if eid in valid_ids]
        raw_hidden = [eid for eid in decision.get("hidden_events", []) if eid in valid_ids]

        corrected_visible = []
        auto_moved = []
        for eid in raw_visible:
            ev = events_by_id.get(eid)
            if ev and _is_visible_to_pov(ev):
                corrected_visible.append(eid)
            else:
                auto_moved.append(eid)
                raw_foreshadow.append(eid)  # downgrade to foreshadowing

        if auto_moved:
            logger.warning(
                f"[camera_decide] Auto-moved {len(auto_moved)} events from visible to foreshadowing "
                f"(POV {pov_id} can't see them): {auto_moved}"
            )

        # Ensure any uncategorized events end up in hidden
        categorized = set(corrected_visible) | set(raw_foreshadow) | set(raw_hidden)
        uncategorized = valid_ids - categorized
        if uncategorized:
            raw_hidden.extend(uncategorized)
            logger.info(f"[camera_decide] Added {len(uncategorized)} uncategorized events to hidden: {uncategorized}")

        decision["visible_events"] = corrected_visible
        decision["foreshadowing_events"] = raw_foreshadow
        decision["hidden_events"] = raw_hidden

        vis_count = len(corrected_visible)
        fore_count = len(raw_foreshadow)
        hid_count = len(raw_hidden)
        _finish(state["story_id"], "camera_decide",
                f"POV: {pov_id} | 可见{vis_count} 伏笔{fore_count} 隐藏{hid_count}")
        logger.info(
            f"[camera_decide] POV={pov_id} visible={vis_count} "
            f"foreshadow={fore_count} hidden={hid_count} pacing={decision.get('pacing')}"
        )
        return {"camera_decision": decision}

    async def load_memories_node(state: ChapterGraphState) -> dict:
        story_id = state["story_id"]
        _enter(story_id, "load_memories", "加载角色记忆...")
        memory_contexts: dict = {}

        if layered_memory:
            pov_id = state["camera_decision"].get("pov_character_id", "") if state.get("camera_decision") else ""
            scene_query = state["plot_structure"].get("chapter_goal", "") if state.get("plot_structure") else ""

            # Load memory for POV character (most detailed)
            if pov_id:
                ctx = await layered_memory.build_context(
                    story_id, pov_id, state["character_profiles"],
                    state["chapter_num"], scene_query=scene_query,
                )
                memory_contexts[pov_id] = ctx.to_prompt_text()

            # Load L0 identity for other active characters
            for c in state["character_profiles"]:
                cid = c.get("character_id", "")
                if cid and cid != pov_id:
                    ctx = await layered_memory.build_context(
                        story_id, cid, state["character_profiles"],
                        state["chapter_num"],
                    )
                    memory_contexts[cid] = ctx.identity_core  # Only L0 for non-POV

        total_chars = sum(len(v) for v in memory_contexts.values())
        _finish(story_id, "load_memories", f"{len(memory_contexts)}个角色, ~{int(total_chars/1.5)}tok")
        logger.info(f"[load_memories] Loaded memory for {len(memory_contexts)} characters, ~{total_chars} chars")
        return {"memory_contexts": memory_contexts}

    async def write_chapter_node(state: ChapterGraphState) -> dict:
        # Get previous chapter summary + timeline for continuity
        prev_summary = ""
        prev_timeline = None
        if state["chapter_num"] > 1:
            prev = await sqlite.get_chapter(state["story_id"], state["chapter_num"] - 1)
            if prev:
                content = prev.get("content", "")
                prev_summary = content[:500] + "..." if len(content) > 500 else content
                prev_timeline = prev.get("metadata", {}).get("timeline")

        # Build retry feedback from consistency result
        retry_feedback = ""
        if state.get("consistency_result") and not state["consistency_pass"]:
            issues = state["consistency_result"].get("issues", [])
            retry_feedback = "\n".join(
                f"- [{i.get('severity', '')}] {i.get('description', '')}: {i.get('suggestion', '')}"
                for i in issues
            )

        retry_num = state.get("retry_count", 0)
        human_feedback = state.get("human_feedback") or ""
        detail_suffix = ""
        if retry_num:
            detail_suffix = f"(重试#{retry_num})"
        elif human_feedback:
            detail_suffix = "(按反馈重写)"
        _enter(state["story_id"], "write_chapter", f"调用Writer Agent...{detail_suffix}")
        agent = WriterAgent(llm)
        draft = await agent.run(
            story_bible=state["story_bible"],
            plot_structure=state["plot_structure"],
            camera_decision=state["camera_decision"],
            character_profiles=state["character_profiles"],
            chapter_num=state["chapter_num"],
            previous_chapter_summary=prev_summary,
            retry_feedback=retry_feedback,
            memory_contexts=state.get("memory_contexts"),
            human_feedback=human_feedback,
            previous_timeline=prev_timeline,
            story_id=state["story_id"],
        )
        _finish(state["story_id"], "write_chapter", f"{len(draft)}字")
        logger.info(f"[write_chapter] Generated {len(draft)} chars (retry #{state.get('retry_count', 0)})")
        return {
            "chapter_draft": draft,
            "retry_count": state.get("retry_count", 0) + (1 if retry_feedback else 0),
        }

    async def consistency_check_node(state: ChapterGraphState) -> dict:
        _enter(state["story_id"], "consistency_check", "调用Consistency Agent...")
        agent = ConsistencyAgent(llm)
        result = await agent.run(
            chapter_draft=state["chapter_draft"],
            story_bible=state["story_bible"],
            world_state=state["world_state"],
            character_profiles=state["character_profiles"],
            camera_decision=state["camera_decision"],
            plot_structure=state["plot_structure"],
            memory_contexts=state.get("memory_contexts"),
            story_id=state["story_id"],
            chapter_num=state["chapter_num"],
        )
        passed = result.get("pass", False)
        _finish(state["story_id"], "consistency_check", f"{'通过' if passed else '未通过'}, 评分{result.get('score', 0)}")
        logger.info(f"[consistency_check] Pass={passed}, score={result.get('score', 0)}")
        return {
            "consistency_result": result,
            "consistency_pass": passed,
        }

    async def _save_single_chapter(
        story_id: str,
        chapter_num: int,
        content: str,
        pov_name: str,
        events_covered: list,
        base_metadata: dict,
        prev_time_marker: str,
    ) -> str:
        """Save one chapter with Titler + timeline. Returns title."""
        metadata = {**base_metadata}
        try:
            titler = TitlerAgent(llm)
            title_result = await titler.run(
                chapter_draft=content,
                chapter_num=chapter_num,
                story_title=(state_bible := base_metadata.get("_story_bible") or {}).get("title", ""),
                chapter_goal=(base_metadata.get("plot_structure") or {}).get("chapter_goal", ""),
                previous_time_marker=prev_time_marker,
                story_id=story_id,
            )
            title = title_result.get("title", "")[:20]
            metadata["timeline"] = {
                "time_marker": title_result.get("time_marker", ""),
                "time_span": title_result.get("time_span", ""),
                "primary_locations": title_result.get("primary_locations", []),
            }
        except Exception as e:
            logger.warning(f"[save_chapter] Titler failed for ch{chapter_num}: {e}")
            title = (base_metadata.get("plot_structure") or {}).get("chapter_goal", "")[:20]
        # Remove internal helper key
        metadata.pop("_story_bible", None)
        await sqlite.save_chapter(
            story_id=story_id,
            chapter_num=chapter_num,
            title=title,
            pov=pov_name,
            content=content,
            events=events_covered,
            metadata=metadata,
        )
        return title

    async def save_chapter_node(state: ChapterGraphState) -> dict:
        story_id = state["story_id"]

        pov_id = state["camera_decision"].get("pov_character_id", "")
        pov_name = pov_id
        for c in state["character_profiles"]:
            if c.get("character_id") == pov_id:
                pov_name = c.get("name", pov_id)
                break

        events_covered = state["camera_decision"].get("visible_events", [])
        base_metadata = {
            "plot_structure": state["plot_structure"],
            "camera_decision": state["camera_decision"],
            "consistency_score": state["consistency_result"].get("score", 0) if state.get("consistency_result") else 0,
            "consistency_warnings": [],
            "retry_count": state.get("retry_count", 0),
            "_story_bible": state.get("story_bible"),  # temp, removed before save
        }

        # Split chapter if too long
        target = state.get("target_word_count", 3000)
        chunks = _split_chapter(state["chapter_draft"], target)

        _enter(story_id, "save_chapter")

        prev_time_marker = ""
        if state["chapter_num"] > 1:
            prev_ch = await sqlite.get_chapter(story_id, state["chapter_num"] - 1)
            if prev_ch:
                prev_time_marker = prev_ch.get("metadata", {}).get("timeline", {}).get("time_marker", "")

        saved_titles = []
        for i, chunk in enumerate(chunks):
            ch_num = state["chapter_num"] + i
            title = await _save_single_chapter(
                story_id, ch_num, chunk, pov_name,
                events_covered if i == 0 else [],
                base_metadata, prev_time_marker,
            )
            saved_titles.append(f"ch{ch_num}:{title}")
            # Next chunk uses this chunk's time for continuity
            prev_time_marker = ""

        # Update world state
        await sqlite.save_world_state(
            story_id, state["world_state"], state["world_state"].get("version", 0)
        )
        json_store.append_events(story_id, state["new_events"])

        # B4.1: Index plot pattern for dedup
        if plot_dedup and state.get("plot_structure"):
            try:
                plot_dedup.index_chapter(
                    story_id=story_id,
                    chapter_num=state["chapter_num"],
                    plot_structure=state["plot_structure"],
                    new_events=state.get("new_events", []),
                )
            except Exception as e:
                logger.warning(f"[save_chapter] Plot dedup index failed: {e}")

        label = " + ".join(saved_titles)
        _finish(story_id, "save_chapter", f"保存{len(chunks)}章 — {label}")
        logger.info(f"[save_chapter] Saved {len(chunks)} chapter(s): {label}")
        return {"error_message": ""}

    async def save_with_warning_node(state: ChapterGraphState) -> dict:
        story_id = state["story_id"]
        pov_id = state["camera_decision"].get("pov_character_id", "")
        pov_name = pov_id
        for c in state["character_profiles"]:
            if c.get("character_id") == pov_id:
                pov_name = c.get("name", pov_id)
                break

        events_covered = state["camera_decision"].get("visible_events", [])
        warnings = [
            i.get("description", "")
            for i in state.get("consistency_result", {}).get("issues", [])
        ]
        base_metadata = {
            "plot_structure": state["plot_structure"],
            "camera_decision": state["camera_decision"],
            "consistency_score": state["consistency_result"].get("score", 0) if state.get("consistency_result") else 0,
            "consistency_warnings": warnings,
            "retry_count": state.get("retry_count", 0),
            "_story_bible": state.get("story_bible"),
        }

        # Split chapter if too long
        target = state.get("target_word_count", 3000)
        chunks = _split_chapter(state["chapter_draft"], target)

        prev_time_marker = ""
        if state["chapter_num"] > 1:
            prev_ch = await sqlite.get_chapter(story_id, state["chapter_num"] - 1)
            if prev_ch:
                prev_time_marker = prev_ch.get("metadata", {}).get("timeline", {}).get("time_marker", "")

        saved_titles = []
        for i, chunk in enumerate(chunks):
            ch_num = state["chapter_num"] + i
            title = await _save_single_chapter(
                story_id, ch_num, chunk, pov_name,
                events_covered if i == 0 else [],
                base_metadata, prev_time_marker,
            )
            saved_titles.append(f"ch{ch_num}:{title}")
            prev_time_marker = ""

        await sqlite.save_world_state(
            story_id, state["world_state"], state["world_state"].get("version", 0)
        )
        json_store.append_events(story_id, state["new_events"])

        # B4.1: Index plot pattern for dedup
        if plot_dedup and state.get("plot_structure"):
            try:
                plot_dedup.index_chapter(
                    story_id=story_id,
                    chapter_num=state["chapter_num"],
                    plot_structure=state["plot_structure"],
                    new_events=state.get("new_events", []),
                )
            except Exception as e:
                logger.warning(f"[save_with_warning] Plot dedup index failed: {e}")

        label = " + ".join(saved_titles)
        logger.warning(
            f"[save_with_warning] Saved {len(chunks)} chapter(s): {label} "
            f"with {len(warnings)} warnings"
        )
        return {"error_message": f"章节已保存（{len(chunks)}章），但存在{len(warnings)}个一致性警告"}

    async def extract_memories_node(state: ChapterGraphState) -> dict:
        story_id = state["story_id"]
        chapter_num = state["chapter_num"]
        _enter(story_id, "extract_memories", "提取角色记忆...")

        extraction_result = None
        extract_detail = ""
        if chapter_extractor and state.get("chapter_draft"):
            try:
                extraction_result = await chapter_extractor.extract_and_save(
                    story_id=story_id,
                    chapter_num=chapter_num,
                    chapter_content=state["chapter_draft"],
                    character_profiles=state["character_profiles"],
                    camera_decision=state.get("camera_decision", {}),
                )
                extract_detail = (
                    f"{len(extraction_result.character_memories)}条记忆, "
                    f"{len(extraction_result.relationship_changes)}条关系"
                )
            except Exception as e:
                logger.error(f"[extract_memories] Failed: {e}")
                _finish(story_id, "extract_memories", f"提取失败: {str(e)[:50]}")
                return {}
        else:
            _finish(story_id, "extract_memories", "跳过（无提取器）")
            return {}

        # B4.2: Refresh character arcs when entering a new arc boundary
        arc_refreshed = 0
        long_outline = (state.get("story_bible") or {}).get("long_outline")
        current_arc = _find_current_arc(long_outline, chapter_num)

        if current_arc and extraction_result:
            # Which characters appeared in this chapter (extracted by ChapterExtractor)
            appeared_ids = {
                cs.get("character_id")
                for cs in extraction_result.character_states
                if cs.get("character_id")
            }
            # Filter to main characters (protagonist/antagonist) that appeared
            main_chars = [
                c for c in state.get("character_profiles", [])
                if c.get("role") in ("protagonist", "antagonist")
                and c.get("character_id") in appeared_ids
            ]

            # Load recent chapters once (up to 3)
            recent_chapters: list[dict] = []
            start_ch = max(1, chapter_num - 2)
            for n in range(start_ch, chapter_num + 1):
                ch = await sqlite.get_chapter(story_id, n)
                if ch:
                    recent_chapters.append({
                        "chapter_num": n,
                        "title": ch.get("title", ""),
                        "content": ch.get("content", ""),
                    })

            arc_agent = CharacterArcAgent(llm)
            current_arc_name = current_arc.get("name", "")

            for char in main_chars:
                cid = char.get("character_id")
                if not cid:
                    continue
                try:
                    latest = await sqlite.get_latest_character_arc(story_id, cid)
                    needs_refresh = (
                        latest is None
                        or latest.get("arc_name", "") != current_arc_name
                    )
                    if not needs_refresh:
                        continue

                    previous_summary = latest.get("summary") if latest else None
                    summary = await arc_agent.run(
                        character_profile=char,
                        recent_chapters=recent_chapters,
                        previous_arc_summary=previous_summary,
                        current_arc_info=current_arc,
                        story_id=story_id,
                        chapter_num=chapter_num,
                    )
                    if summary:
                        await sqlite.save_character_arc(
                            story_id=story_id,
                            character_id=cid,
                            chapter_num=chapter_num,
                            arc_name=current_arc_name,
                            summary=summary,
                        )
                        arc_refreshed += 1
                except Exception as e:
                    logger.warning(
                        f"[extract_memories] Arc refresh failed for {cid}: {e}"
                    )

        final_detail = extract_detail
        if arc_refreshed:
            final_detail += f", 刷新{arc_refreshed}个弧线"
        _finish(story_id, "extract_memories", final_detail)
        logger.info(
            f"[extract_memories] Chapter {chapter_num}: {extract_detail}, "
            f"arc_refreshed={arc_refreshed}"
        )
        return {}

    return (
        load_context_node,
        world_advance_node,
        plot_plan_node,
        camera_decide_node,
        load_memories_node,
        write_chapter_node,
        consistency_check_node,
        save_chapter_node,
        save_with_warning_node,
        extract_memories_node,
    )

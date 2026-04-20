import logging

from backend.agents.camera import CameraAgent
from backend.agents.character_arc import CharacterArcAgent
from backend.agents.character_reviewer import CharacterReviewerAgent
from backend.agents.consistency import ConsistencyAgent
from backend.agents.planner import PlotPlannerAgent
from backend.agents.scene_consistency import SceneConsistencyAgent
from backend.agents.scene_splitter import SceneSplitterAgent
from backend.agents.scene_writer import SceneWriterAgent
from backend.agents.titler import TitlerAgent
from backend.agents.world import WorldAgent
# WriterAgent is legacy (replaced by SceneWriterAgent in Phase 4)
from backend.llm.client import LLMClient
from backend.memory.chapter_extractor import ChapterExtractor
from backend.memory.context_builder import ContextBuilder, bundle_to_writer_text
from backend.memory.layered_memory import LayeredMemory
from backend.memory.plot_dedup import PlotDedupStore
from backend.memory.world_book import WorldBook
from backend.models.graph_state import ChapterGraphState, InitGraphState
from backend.progress import ProgressStore
from backend.storage.json_store import JSONStore
from backend.storage.sqlite_store import SQLiteStore
from backend.storage.vector_store import VectorStore

logger = logging.getLogger(__name__)


def _find_current_volume(bible: dict, chapter_num: int) -> dict | None:
    volumes = bible.get("volumes") or []
    if not volumes:
        return None
    for vol in volumes:
        start = vol.get("chapter_start")
        end = vol.get("chapter_end")
        if start is None or end is None:
            continue
        if start <= chapter_num <= end:
            return vol
    return volumes[-1]


def create_init_nodes(llm: LLMClient, title: str = "", world_book: WorldBook | None = None):
    """Create node functions for the 8-step story initialization graph.

    Pipeline: concept → world_build → character_design → outline_plan
              → assemble_bible → extract_characters → init_world → init_world_book
    """
    from backend.agents.concept import ConceptAgent
    from backend.agents.world_builder import WorldBuilderAgent
    from backend.agents.character_designer import CharacterDesigner
    from backend.agents.outline_planner import OutlinePlannerAgent
    from backend.models.story_bible import extract_characters_from_bible

    async def concept_node(state: InitGraphState) -> dict:
        logger.info(f"[init] Step 1: ConceptAgent for story {state['story_id']}")
        agent = ConceptAgent(llm)
        concept = await agent.run(
            user_theme=state["user_theme"],
            user_requirements=state["user_requirements"],
            title=title,
            story_id=state["story_id"],
        )
        logger.info(f"[init] Concept done: {concept.get('title', '')}")
        return {"concept": concept}

    async def world_build_node(state: InitGraphState) -> dict:
        logger.info(f"[init] Step 2: WorldBuilderAgent")
        agent = WorldBuilderAgent(llm)
        world_setting = await agent.run(
            concept=state["concept"],
            story_id=state["story_id"],
        )
        n_factions = len(world_setting.get("factions", []))
        logger.info(f"[init] World done: {n_factions} factions")
        return {"world_setting": world_setting}

    async def character_design_node(state: InitGraphState) -> dict:
        logger.info(f"[init] Step 3: CharacterDesigner")
        agent = CharacterDesigner(llm)
        characters_design = await agent.run(
            concept=state["concept"],
            world_setting=state["world_setting"],
            story_id=state["story_id"],
        )
        n = 1 + (1 if characters_design.get("antagonist") else 0) + len(characters_design.get("supporting_characters", []))
        logger.info(f"[init] Characters done: {n} characters")
        return {"characters_design": characters_design}

    async def outline_plan_node(state: InitGraphState) -> dict:
        logger.info(f"[init] Step 4: OutlinePlannerAgent")
        agent = OutlinePlannerAgent(llm)
        outline = await agent.run(
            concept=state["concept"],
            world_setting=state["world_setting"],
            characters_design=state["characters_design"],
            story_id=state["story_id"],
        )
        n_vol = len(outline.get("volumes", []))
        logger.info(f"[init] Outline done: {n_vol} volumes")
        return {"outline": outline}

    async def assemble_bible_node(state: InitGraphState) -> dict:
        logger.info(f"[init] Step 5: Assembling StoryBible V2")
        concept = state.get("concept") or {}
        world = state.get("world_setting") or {}
        chars = state.get("characters_design") or {}
        outline = state.get("outline") or {}

        protagonist = chars.get("protagonist")
        antagonist = chars.get("antagonist")
        supporting = chars.get("supporting_characters", [])

        volumes = outline.get("volumes", [])

        bible = {
            "bible_version": 2,
            "title": concept.get("title", ""),
            "genre": concept.get("genre", ""),
            "tone": concept.get("tone", ""),
            "one_line_summary": concept.get("one_line_summary", ""),
            "synopsis": concept.get("synopsis", ""),
            "inspiration": concept.get("inspiration", ""),
            "world": {
                "world_background": world.get("world_background", ""),
                "special_ability": concept.get("special_ability"),
                "factions": world.get("factions", []),
                "power_system": world.get("power_system"),
                "world_rules": world.get("world_rules", []),
            },
            "protagonist": protagonist,
            "antagonist": antagonist,
            "supporting_characters": supporting,
            "primary_pov": protagonist.get("character_id", "char_protagonist") if protagonist else "",
            "style_guide": {
                "tone": concept.get("tone", ""),
                "pov_preference": "第三人称限知",
                "language_style": "现代白话",
                "dialogue_style": "简洁有力",
            },
            "taboos": [],
            "initial_conflicts": outline.get("initial_conflicts", []),
            "planned_arc": outline.get("planned_arc", ""),
            "volumes": volumes,
            "world_rules": world.get("world_rules", []),
            "power_system": world.get("power_system"),
        }
        return {"story_bible": bible}

    async def extract_characters_node(state: InitGraphState) -> dict:
        bible = state["story_bible"]
        characters = extract_characters_from_bible(bible)
        for i, c in enumerate(characters):
            if not c.get("character_id"):
                c["character_id"] = f"char_{i+1}"
        logger.info(f"[init] Step 6: Extracted {len(characters)} characters")
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
        logger.info(f"[init] Step 7: World state initialized")
        return {"initial_world_state": world_state}

    async def init_world_book_node(state: InitGraphState) -> dict:
        if not world_book:
            return {}
        try:
            n = await world_book.sync_from_bible(state["story_id"], state["story_bible"])
            logger.info(f"[init] Step 8: WorldBook synced {n} entries")
        except Exception as e:
            logger.warning(f"[init] WorldBook sync failed: {e}")
        return {}

    return (
        concept_node, world_build_node, character_design_node, outline_plan_node,
        assemble_bible_node, extract_characters_node, init_world_node, init_world_book_node,
    )


def create_chapter_nodes(
    llm: LLMClient,
    sqlite: SQLiteStore,
    json_store: JSONStore,
    vector: VectorStore,
    progress_store: ProgressStore | None = None,
    layered_memory: LayeredMemory | None = None,
    chapter_extractor: ChapterExtractor | None = None,
    plot_dedup: PlotDedupStore | None = None,
    context_builder: ContextBuilder | None = None,
    chapter_consistency_threshold: int = 70,
    chapter_max_critical: int = 0,
    chapter_max_warnings: int = 3,
    scene_consistency_threshold: float = 0.7,
):
    """Create chapter-generation pipeline nodes with Phase 1-5 machinery."""

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

        # Merge latest active character arc summary into each character profile
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

        storylines = result.get("storylines") or []
        if storylines:
            new_events = []
            for sl in storylines:
                new_events.extend(sl.get("new_events", []))
        else:
            new_events = result.get("new_events", [])

        world_state = state["world_state"].copy()
        world_state["current_time"] = result.get("updated_time", world_state.get("current_time", 0) + 1)
        world_state["time_description"] = result.get("time_description", "")

        updates = result.get("world_state_updates", {})
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
        return {
            "new_events": new_events,
            "storylines": storylines,
            "world_state": world_state,
        }

    async def plot_plan_node(state: ChapterGraphState) -> dict:
        bible = state.get("story_bible") or {}
        current_volume = _find_current_volume(bible, state["chapter_num"])
        vol_label = current_volume.get("volume_name", "") if current_volume else "无大纲"

        similar_past = []
        if plot_dedup:
            vol_plot = current_volume.get("main_plot", "") if current_volume else ""
            query = f"{vol_plot} {bible.get('planned_arc', '')}"
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
        _enter(state["story_id"], "plot_plan", f"调用Plot Planner... ({vol_label}{dedup_label})")
        agent = PlotPlannerAgent(llm)
        plot = await agent.run(
            story_bible=bible,
            new_events=state["new_events"],
            chapter_num=state["chapter_num"],
            event_history=state["event_history"],
            current_volume=current_volume,
            similar_past_patterns=similar_past if similar_past else None,
            storylines=state.get("storylines") or None,
            story_id=state["story_id"],
        )
        _finish(state["story_id"], "plot_plan", plot.get("chapter_goal", "")[:30])
        return {"plot_structure": plot}

    async def camera_decide_node(state: ChapterGraphState) -> dict:
        story_id = state["story_id"]
        chapters = await sqlite.list_chapters(story_id)
        previous_povs = [ch.get("pov", "") for ch in chapters]

        new_events = state.get("new_events") or []
        _enter(state["story_id"], "camera_decide", f"调用Camera Agent... ({len(new_events)}事件)")
        primary_pov = (state.get("story_bible") or {}).get("primary_pov", "")
        agent = CameraAgent(llm)
        decision = await agent.run(
            plot_structure=state["plot_structure"],
            character_profiles=state["character_profiles"],
            chapter_num=state["chapter_num"],
            previous_povs=previous_povs,
            new_events=new_events,
            primary_pov=primary_pov,
            story_id=state["story_id"],
        )

        pov_id = decision.get("pov_character_id", "")
        valid_ids = {e.get("event_id") for e in new_events if e.get("event_id")}
        events_by_id = {e.get("event_id"): e for e in new_events if e.get("event_id")}

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
                raw_foreshadow.append(eid)

        categorized = set(corrected_visible) | set(raw_foreshadow) | set(raw_hidden)
        uncategorized = valid_ids - categorized
        if uncategorized:
            raw_hidden.extend(uncategorized)

        decision["visible_events"] = corrected_visible
        decision["foreshadowing_events"] = raw_foreshadow
        decision["hidden_events"] = raw_hidden

        _finish(
            state["story_id"], "camera_decide",
            f"POV:{pov_id}|见{len(corrected_visible)} 埋{len(raw_foreshadow)} 藏{len(raw_hidden)}"
        )
        return {"camera_decision": decision}

    async def build_context_node(state: ChapterGraphState) -> dict:
        """Phase 3: assemble a ContextBundle for the whole chapter using ContextBuilder."""
        story_id = state["story_id"]
        _enter(story_id, "build_context", "组装三层记忆...")
        if not context_builder:
            _finish(story_id, "build_context", "跳过")
            return {"context_bundle": {}, "upstream_dependencies": []}

        # Primary characters = POV + any characters in plot beats
        pov_id = state["camera_decision"].get("pov_character_id", "") if state.get("camera_decision") else ""
        plot_chars = []
        plot = state.get("plot_structure") or {}
        for b in (plot.get("beats") or []):
            if isinstance(b, dict):
                plot_chars.extend(b.get("characters") or [])
        primary_chars = [pov_id] + list({c for c in plot_chars if c and c != pov_id})[:3]

        bundle = await context_builder.build(
            story_id=story_id,
            chapter_num=state["chapter_num"],
            story_bible=state.get("story_bible") or {},
            character_profiles=state.get("character_profiles") or [],
            plot_structure=plot,
            scene=None,
            primary_characters=[c for c in primary_chars if c],
        )

        # Build dependency rows for Phase 2 tracking (chapter-level)
        upstream_deps = []
        for ch in bundle.dependency_chapters:
            vid = await sqlite.get_live_version_id(story_id, ch)
            if vid is not None:
                upstream_deps.append({
                    "depends_on_chapter": ch,
                    "depends_on_version_id": vid,
                    "dep_type": "memory",
                })

        _finish(
            story_id, "build_context",
            f"bible={len(bundle.bible_core)} recent={len(bundle.recent_summary)} "
            f"tail={len(bundle.last_tail)} mem={len(bundle.vector_memory)} "
            f"lore={len(bundle.triggered_entry_names)}"
        )
        logger.info(
            f"[build_context] ch{state['chapter_num']} deps={bundle.dependency_chapters} "
            f"triggered={bundle.triggered_entry_names}"
        )
        return {
            "context_bundle": bundle.to_dict(),
            "upstream_dependencies": upstream_deps,
        }

    async def load_memories_node(state: ChapterGraphState) -> dict:
        """Legacy memory loader - kept for ConsistencyAgent compatibility.

        Phase 3 ContextBuilder has largely superseded this, but we still load
        structured per-character contexts for agents that consume them directly.
        """
        story_id = state["story_id"]
        _enter(story_id, "load_memories", "加载角色记忆...")
        memory_contexts: dict = {}

        if layered_memory:
            pov_id = state["camera_decision"].get("pov_character_id", "") if state.get("camera_decision") else ""
            scene_query = state["plot_structure"].get("chapter_goal", "") if state.get("plot_structure") else ""

            if pov_id:
                ctx = await layered_memory.build_context(
                    story_id, pov_id, state["character_profiles"],
                    state["chapter_num"], scene_query=scene_query,
                )
                memory_contexts[pov_id] = ctx.to_prompt_text()

            for c in state["character_profiles"]:
                cid = c.get("character_id", "")
                if cid and cid != pov_id:
                    ctx = await layered_memory.build_context(
                        story_id, cid, state["character_profiles"],
                        state["chapter_num"],
                    )
                    memory_contexts[cid] = ctx.identity_core

        _finish(story_id, "load_memories", f"{len(memory_contexts)}个角色")
        return {"memory_contexts": memory_contexts}

    async def scene_split_node(state: ChapterGraphState) -> dict:
        """Phase 4: split plot structure into 2-5 scenes based on target word count."""
        story_id = state["story_id"]
        target = state.get("target_word_count", 3000)
        _enter(story_id, "scene_split", f"拆分场景 (目标{target}字)...")
        splitter = SceneSplitterAgent(llm)

        # Previous chapter tail for continuity
        prev_tail = ""
        if state["chapter_num"] > 1:
            prev_summary = await sqlite.get_chapter_summary(story_id, state["chapter_num"] - 1)
            if prev_summary and prev_summary.get("tail_snippet"):
                prev_tail = prev_summary["tail_snippet"]
            else:
                prev = await sqlite.get_chapter(story_id, state["chapter_num"] - 1)
                if prev:
                    prev_tail = (prev.get("content", "") or "")[-300:]

        scenes = await splitter.run(
            chapter_num=state["chapter_num"],
            plot_structure=state["plot_structure"],
            target_word_count=target,
            character_profiles=state["character_profiles"],
            previous_chapter_tail=prev_tail,
            story_id=story_id,
        )
        _finish(story_id, "scene_split", f"{len(scenes)}个场景")
        logger.info(
            f"[scene_split] chapter {state['chapter_num']}: {len(scenes)} scenes, "
            f"targets={[s.get('target_words') for s in scenes]}"
        )
        return {
            "scenes": scenes,
            "current_scene_idx": 0,
            "scene_contents": [],
            "scene_retry_count": {},
            "scene_consistency_results": [],
        }

    async def write_scenes_node(state: ChapterGraphState) -> dict:
        """Phase 4: iterate scenes — per-scene ContextBuilder + SceneWriter + SceneConsistency.

        Done in a single node with an internal for-loop (scenes are dynamic).
        """
        story_id = state["story_id"]
        chapter_num = state["chapter_num"]
        scenes = state.get("scenes") or []
        if not scenes:
            # Fallback to single synthetic scene covering the whole chapter
            target = state.get("target_word_count", 3000)
            scenes = [{
                "scene_idx": 1,
                "scene_id": f"ch{chapter_num}_s1",
                "pov_character_id": (state.get("camera_decision") or {}).get("pov_character_id", ""),
                "location": "",
                "characters_present": [],
                "time_marker": "",
                "beats": (state.get("plot_structure") or {}).get("beats", []),
                "purpose": (state.get("plot_structure") or {}).get("chapter_goal", ""),
                "target_words": target,
                "opening_hook": "",
                "closing_hook": "",
            }]

        writer = SceneWriterAgent(llm)
        checker = SceneConsistencyAgent(llm)
        max_retries = 2  # per scene

        scene_contents: list[str] = []
        scene_results: list[dict] = []
        retry_counts: dict = {}
        prev_scene_tail = ""

        human_feedback = state.get("human_feedback") or ""

        # If consistency_check failed and we're retrying, inject its issues as
        # chapter-level feedback so every scene_writer call knows what went wrong.
        chapter_retry_feedback = ""
        cr = state.get("consistency_result")
        if cr and not state.get("consistency_pass"):
            issues = cr.get("issues") or []
            if issues:
                lines = ["[整章一致性检查未通过，请在本次重写中修正以下问题]"]
                for issue in issues:
                    sev = issue.get("severity", "")
                    desc = issue.get("description", "")
                    sug = issue.get("suggestion", "")
                    lines.append(f"- [{sev}] {desc}（建议：{sug}）")
                chapter_retry_feedback = "\n".join(lines)

        for idx, scene in enumerate(scenes):
            scene_idx = scene.get("scene_idx", idx + 1)
            _enter(story_id, "write_scenes", f"场景{scene_idx}/{len(scenes)}")

            # Build per-scene context
            scene_ctx_text = ""
            character_cards_block = ""
            unresolved_block = ""
            world_book_block = ""
            if context_builder:
                primary_chars = [scene.get("pov_character_id")] + (scene.get("characters_present") or [])
                primary_chars = [c for c in primary_chars if c]
                bundle = await context_builder.build(
                    story_id=story_id,
                    chapter_num=chapter_num,
                    story_bible=state.get("story_bible") or {},
                    character_profiles=state.get("character_profiles") or [],
                    plot_structure=state.get("plot_structure"),
                    scene=scene,
                    primary_characters=primary_chars,
                )
                scene_ctx_text = bundle_to_writer_text(bundle)
                character_cards_block = bundle.character_cards
                unresolved_block = bundle.unresolved_threads
                world_book_block = bundle.lorebook
            else:
                scene_ctx_text = ""

            # Write with retry loop
            scene_content = ""
            last_check = {"pass": True, "score": 1.0, "failed_items": []}
            retry_count = 0
            retry_feedback = ""

            for attempt in range(max_retries + 1):
                # Combine feedback sources:
                #   1. human_feedback — user-provided (first attempt only)
                #   2. chapter_retry_feedback — from failed consistency_check
                #   3. retry_feedback — from failed scene_consistency on prior attempt
                feedback_parts = []
                if attempt == 0 and human_feedback:
                    feedback_parts.append(human_feedback)
                if chapter_retry_feedback:
                    feedback_parts.append(chapter_retry_feedback)
                if attempt > 0 and retry_feedback:
                    feedback_parts.append(retry_feedback)
                combined_feedback = "\n\n".join(feedback_parts)

                scene_content = await writer.run(
                    scene=scene,
                    chapter_num=chapter_num,
                    context_block=scene_ctx_text,
                    previous_scene_tail=prev_scene_tail,
                    human_feedback=combined_feedback,
                    story_id=story_id,
                )
                if not scene_content:
                    logger.warning(f"[write_scenes] empty draft for scene {scene_idx} attempt {attempt+1}")
                    retry_count += 1
                    retry_feedback = "上次生成为空，请严格按目标字数输出场景正文。"
                    continue

                last_check = await checker.run(
                    scene=scene,
                    scene_content=scene_content,
                    character_cards_block=character_cards_block,
                    unresolved_threads_block=unresolved_block,
                    world_book_block=world_book_block,
                    story_id=story_id,
                    chapter_num=chapter_num,
                )
                scene_score = last_check.get("score", 0.0)
                scene_passed = scene_score >= scene_consistency_threshold
                # Also check for high-severity failures regardless of score
                high_severity = any(
                    f.get("severity") == "high"
                    for f in (last_check.get("failed_items") or [])
                )
                if high_severity:
                    scene_passed = False

                logger.info(
                    f"[write_scenes] scene {scene_idx}/{len(scenes)} "
                    f"attempt {attempt+1} words={len(scene_content)} "
                    f"score={scene_score:.2f}/{scene_consistency_threshold} passed={scene_passed}"
                )
                last_check["pass"] = scene_passed
                if scene_passed:
                    break
                retry_count += 1
                retry_feedback = checker.format_retry_feedback(last_check)

            retry_counts[scene_idx] = retry_count
            scene_contents.append(scene_content)
            scene_results.append({
                "scene_idx": scene_idx,
                "pass": last_check.get("pass", True),
                "score": last_check.get("score", 0.0),
                "failed_items": last_check.get("failed_items") or [],
                "retry_count": retry_count,
                "word_count": len(scene_content),
            })

            # Update previous scene tail for next iteration
            prev_scene_tail = scene_content[-300:] if scene_content else ""

            # Persist scene row
            version_id_tmp = state.get("current_version_id") or 0
            try:
                await sqlite.save_chapter_scene(
                    story_id=story_id,
                    chapter_num=chapter_num,
                    source_version_id=version_id_tmp,
                    scene_idx=scene_idx,
                    scene_id=scene.get("scene_id", f"ch{chapter_num}_s{scene_idx}"),
                    pov_character_id=scene.get("pov_character_id", ""),
                    location=scene.get("location", ""),
                    characters=scene.get("characters_present") or [],
                    beats=scene.get("beats") or [],
                    purpose=scene.get("purpose", ""),
                    target_words=scene.get("target_words", 800),
                    content=scene_content,
                    consistency_score=last_check.get("score", 0.0),
                    consistency_issues=last_check.get("failed_items") or [],
                    retry_count=retry_count,
                )
            except Exception as e:
                logger.warning(f"[write_scenes] Failed to persist scene {scene_idx}: {e}")

        total_words = sum(len(c) for c in scene_contents)
        avg_score = sum(r["score"] for r in scene_results) / max(1, len(scene_results))
        _finish(
            story_id, "write_scenes",
            f"{len(scene_contents)}场{total_words}字 均分{avg_score:.2f}"
        )
        return {
            "scene_contents": scene_contents,
            "scene_retry_count": retry_counts,
            "scene_consistency_results": scene_results,
        }

    async def assemble_chapter_node(state: ChapterGraphState) -> dict:
        """Phase 4: merge scene_contents into a single chapter_draft."""
        story_id = state["story_id"]
        contents = state.get("scene_contents") or []
        if not contents:
            return {"chapter_draft": "", "error_message": "场景生成失败，无内容"}
        # Join scenes with a light delimiter (blank line) — scene markers are internal
        draft = "\n\n".join([c.strip() for c in contents if c and c.strip()])
        _finish(story_id, "assemble_chapter", f"{len(contents)}场→{len(draft)}字")
        return {"chapter_draft": draft}

    async def consistency_check_node(state: ChapterGraphState) -> dict:
        _enter(state["story_id"], "consistency_check", "整章终检...")
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

        # Apply configurable thresholds instead of trusting LLM's own pass/fail
        score = result.get("score", 0)
        issues = result.get("issues") or []
        n_critical = sum(1 for i in issues if i.get("severity") == "critical")
        n_warning = sum(1 for i in issues if i.get("severity") == "warning")

        passed = (
            score >= chapter_consistency_threshold
            and n_critical <= chapter_max_critical
            and n_warning <= chapter_max_warnings
        )

        detail = (
            f"{'通过' if passed else '未通过'} "
            f"评分{score}/{chapter_consistency_threshold} "
            f"critical={n_critical}/{chapter_max_critical} "
            f"warning={n_warning}/{chapter_max_warnings}"
        )
        _finish(state["story_id"], "consistency_check", detail)
        logger.info(f"[consistency_check] {detail}")

        result["_threshold"] = chapter_consistency_threshold
        result["_passed_by_threshold"] = passed
        return {
            "consistency_result": result,
            "consistency_pass": passed,
        }

    async def _title_chapter(
        story_id: str, chapter_num: int, content: str,
        base_metadata: dict, prev_time_marker: str,
    ) -> tuple[str, dict]:
        metadata = {**base_metadata}
        try:
            titler = TitlerAgent(llm)
            title_result = await titler.run(
                chapter_draft=content,
                chapter_num=chapter_num,
                story_title=(base_metadata.get("_story_bible") or {}).get("title", ""),
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
        metadata.pop("_story_bible", None)
        return title, metadata

    async def save_chapter_node(state: ChapterGraphState) -> dict:
        story_id = state["story_id"]
        chapter_num = state["chapter_num"]

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
            "scene_count": len(state.get("scene_contents") or []),
            "scene_retry_counts": state.get("scene_retry_count") or {},
            "_story_bible": state.get("story_bible"),
        }

        _enter(story_id, "save_chapter")

        prev_time_marker = ""
        if chapter_num > 1:
            prev_ch = await sqlite.get_chapter(story_id, chapter_num - 1)
            if prev_ch:
                prev_time_marker = prev_ch.get("metadata", {}).get("timeline", {}).get("time_marker", "")

        title, metadata = await _title_chapter(
            story_id, chapter_num, state["chapter_draft"], base_metadata, prev_time_marker,
        )

        # Unified save: chapter_versions(is_live=1) + chapters view
        version_id = await sqlite.save_chapter_and_version(
            story_id=story_id,
            chapter_num=chapter_num,
            title=title,
            pov=pov_name,
            content=state["chapter_draft"],
            events=events_covered,
            metadata=metadata,
            feedback="",
        )

        # Update world state
        await sqlite.save_world_state(
            story_id, state["world_state"], state["world_state"].get("version", 0)
        )
        json_store.append_events(story_id, state["new_events"])

        if plot_dedup and state.get("plot_structure"):
            try:
                plot_dedup.index_chapter(
                    story_id=story_id,
                    chapter_num=chapter_num,
                    plot_structure=state["plot_structure"],
                    new_events=state.get("new_events", []),
                )
            except Exception as e:
                logger.warning(f"[save_chapter] Plot dedup index failed: {e}")

        _finish(story_id, "save_chapter", f"{title} (v{version_id})")
        return {"error_message": "", "current_version_id": version_id}

    async def save_with_warning_node(state: ChapterGraphState) -> dict:
        story_id = state["story_id"]
        chapter_num = state["chapter_num"]
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
            "scene_count": len(state.get("scene_contents") or []),
            "scene_retry_counts": state.get("scene_retry_count") or {},
            "_story_bible": state.get("story_bible"),
        }

        prev_time_marker = ""
        if chapter_num > 1:
            prev_ch = await sqlite.get_chapter(story_id, chapter_num - 1)
            if prev_ch:
                prev_time_marker = prev_ch.get("metadata", {}).get("timeline", {}).get("time_marker", "")

        title, metadata = await _title_chapter(
            story_id, chapter_num, state["chapter_draft"], base_metadata, prev_time_marker,
        )

        version_id = await sqlite.save_chapter_and_version(
            story_id=story_id,
            chapter_num=chapter_num,
            title=title,
            pov=pov_name,
            content=state["chapter_draft"],
            events=events_covered,
            metadata=metadata,
            feedback=f"[warn×{len(warnings)}]",
        )

        await sqlite.save_world_state(
            story_id, state["world_state"], state["world_state"].get("version", 0)
        )
        json_store.append_events(story_id, state["new_events"])

        if plot_dedup and state.get("plot_structure"):
            try:
                plot_dedup.index_chapter(
                    story_id=story_id,
                    chapter_num=chapter_num,
                    plot_structure=state["plot_structure"],
                    new_events=state.get("new_events", []),
                )
            except Exception as e:
                logger.warning(f"[save_with_warning] Plot dedup index failed: {e}")

        logger.warning(
            f"[save_with_warning] Saved ch{chapter_num} v{version_id} with {len(warnings)} warnings"
        )
        return {
            "error_message": f"章节已保存，但存在{len(warnings)}个一致性警告",
            "current_version_id": version_id,
        }

    async def extract_memories_node(state: ChapterGraphState) -> dict:
        story_id = state["story_id"]
        chapter_num = state["chapter_num"]
        version_id = state.get("current_version_id") or await sqlite.get_live_version_id(story_id, chapter_num)
        _enter(story_id, "extract_memories", "提取角色记忆+章节摘要...")

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
                    source_version_id=version_id,
                )
                extract_detail = (
                    f"{len(extraction_result.character_memories)}条记忆, "
                    f"{len(extraction_result.relationship_changes)}条关系"
                )
            except Exception as e:
                logger.error(f"[extract_memories] Failed: {e}")
                _finish(story_id, "extract_memories", f"提取失败: {str(e)[:50]}")
                return {}

        # Phase 5: CharacterReviewer per in-scene character
        reviewer_count = 0
        if extraction_result:
            appeared_ids = {
                cs.get("character_id")
                for cs in extraction_result.character_states
                if cs.get("character_id")
            }
            profiles_by_id = {c.get("character_id"): c for c in state.get("character_profiles", [])}
            reviewer = CharacterReviewerAgent(llm)
            for cid in list(appeared_ids)[:5]:  # cap
                prof = profiles_by_id.get(cid)
                if not prof:
                    continue
                try:
                    # Fetch previous state
                    import aiosqlite
                    async with aiosqlite.connect(sqlite.db_path) as db:
                        db.row_factory = aiosqlite.Row
                        cursor = await db.execute(
                            """SELECT * FROM character_states
                               WHERE story_id = ? AND character_id = ?
                                 AND chapter_num < ? AND is_active = 1
                               ORDER BY chapter_num DESC LIMIT 1""",
                            (story_id, cid, chapter_num),
                        )
                        row = await cursor.fetchone()
                    prev_state = dict(row) if row else None
                    review = await reviewer.run(
                        character_profile=prof,
                        chapter_content=state["chapter_draft"],
                        previous_state=prev_state,
                        chapter_num=chapter_num,
                        story_id=story_id,
                    )
                    if review:
                        # Merge into character_states (update the just-inserted row)
                        import json as _json
                        async with aiosqlite.connect(sqlite.db_path) as db:
                            await db.execute(
                                """UPDATE character_states
                                   SET state_json = ?
                                   WHERE story_id = ? AND character_id = ?
                                     AND chapter_num = ? AND source_version_id = ?""",
                                (
                                    _json.dumps({
                                        **(prev_state or {}),
                                        **review,
                                    }, ensure_ascii=False),
                                    story_id, cid, chapter_num, version_id or 0,
                                ),
                            )
                            await db.commit()
                        reviewer_count += 1
                except Exception as e:
                    logger.warning(f"[extract_memories] CharacterReviewer failed for {cid}: {e}")

        # B4.2: Refresh character arcs when entering a new volume boundary
        arc_refreshed = 0
        current_volume = _find_current_volume(state.get("story_bible") or {}, chapter_num)

        if current_volume and extraction_result:
            appeared_ids = {
                cs.get("character_id")
                for cs in extraction_result.character_states
                if cs.get("character_id")
            }
            main_chars = [
                c for c in state.get("character_profiles", [])
                if c.get("role") in ("protagonist", "antagonist")
                and c.get("character_id") in appeared_ids
            ]

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
            current_vol_name = current_volume.get("volume_name", "")

            for char in main_chars:
                cid = char.get("character_id")
                if not cid:
                    continue
                try:
                    latest = await sqlite.get_latest_character_arc(story_id, cid)
                    needs_refresh = (
                        latest is None
                        or latest.get("arc_name", "") != current_vol_name
                    )
                    if not needs_refresh:
                        continue

                    previous_summary = latest.get("summary") if latest else None
                    summary = await arc_agent.run(
                        character_profile=char,
                        recent_chapters=recent_chapters,
                        previous_arc_summary=previous_summary,
                        current_arc_info=current_volume,
                        story_id=story_id,
                        chapter_num=chapter_num,
                    )
                    if summary:
                        await sqlite.save_character_arc(
                            story_id=story_id,
                            character_id=cid,
                            chapter_num=chapter_num,
                            arc_name=current_vol_name,
                            summary=summary,
                            source_version_id=version_id,
                        )
                        arc_refreshed += 1
                except Exception as e:
                    logger.warning(
                        f"[extract_memories] Arc refresh failed for {cid}: {e}"
                    )

        # Phase 4: also store scene texts into vector store for future retrieval
        if state.get("scene_contents") and version_id:
            scenes = state.get("scenes") or []
            for idx, content in enumerate(state.get("scene_contents") or []):
                if not content:
                    continue
                scene_meta = scenes[idx] if idx < len(scenes) else {}
                try:
                    vector.add_scene_text(
                        story_id=story_id,
                        chapter_num=chapter_num,
                        scene_idx=scene_meta.get("scene_idx", idx + 1),
                        content=content,
                        metadata={
                            "location": scene_meta.get("location", ""),
                            "pov": scene_meta.get("pov_character_id", ""),
                            "characters": scene_meta.get("characters_present", []),
                        },
                        source_version_id=version_id,
                    )
                except Exception as e:
                    logger.warning(f"[extract_memories] scene_text persist failed: {e}")

        # Phase 2: record chapter dependencies
        if version_id:
            deps = state.get("upstream_dependencies") or []
            if deps:
                try:
                    await sqlite.record_chapter_dependencies(
                        story_id=story_id,
                        chapter_num=chapter_num,
                        source_version_id=version_id,
                        deps=deps,
                    )
                except Exception as e:
                    logger.warning(f"[extract_memories] dep record failed: {e}")

        final_detail = extract_detail
        if reviewer_count:
            final_detail += f", {reviewer_count}个角色更新"
        if arc_refreshed:
            final_detail += f", 刷新{arc_refreshed}个弧线"
        _finish(story_id, "extract_memories", final_detail)
        logger.info(
            f"[extract_memories] ch{chapter_num}: {final_detail}"
        )
        return {}

    return (
        load_context_node,
        world_advance_node,
        plot_plan_node,
        camera_decide_node,
        build_context_node,
        load_memories_node,
        scene_split_node,
        write_scenes_node,
        assemble_chapter_node,
        consistency_check_node,
        save_chapter_node,
        save_with_warning_node,
        extract_memories_node,
    )

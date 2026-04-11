import logging

from backend.agents.camera import CameraAgent
from backend.agents.consistency import ConsistencyAgent
from backend.agents.director import DirectorAgent
from backend.agents.planner import PlotPlannerAgent
from backend.agents.titler import TitlerAgent
from backend.agents.world import WorldAgent
from backend.agents.writer import WriterAgent
from backend.llm.client import LLMClient
from backend.memory.chapter_extractor import ChapterExtractor
from backend.memory.layered_memory import LayeredMemory
from backend.models.graph_state import ChapterGraphState, InitGraphState
from backend.progress import ProgressStore
from backend.storage.json_store import JSONStore
from backend.storage.sqlite_store import SQLiteStore
from backend.storage.vector_store import VectorStore

logger = logging.getLogger(__name__)


def create_init_nodes(llm: LLMClient):
    """Create node functions for the story initialization graph."""

    async def generate_bible_node(state: InitGraphState) -> dict:
        agent = DirectorAgent(llm)
        bible = await agent.run(
            user_theme=state["user_theme"],
            user_requirements=state["user_requirements"],
            story_id=state["story_id"],
        )
        return {"story_bible": bible}

    async def extract_characters_node(state: InitGraphState) -> dict:
        bible = state["story_bible"]
        characters = bible.get("characters", [])
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
        _finish(story_id, "load_context", f"{len(events)}个事件, {len(characters)}个角色")
        logger.info(f"[load_context] Loaded context for story {story_id}, {len(events)} events, {len(characters)} characters")
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

        _finish(state["story_id"], "world_advance", f"生成{len(new_events)}个事件")
        logger.info(f"[world_advance] Generated {len(new_events)} new events, time={world_state['current_time']}")
        return {
            "new_events": new_events,
            "world_state": world_state,
        }

    async def plot_plan_node(state: ChapterGraphState) -> dict:
        _enter(state["story_id"], "plot_plan", "调用Plot Planner...")
        agent = PlotPlannerAgent(llm)
        plot = await agent.run(
            story_bible=state["story_bible"],
            new_events=state["new_events"],
            chapter_num=state["chapter_num"],
            event_history=state["event_history"],
            story_id=state["story_id"],
        )
        _finish(state["story_id"], "plot_plan", plot.get("chapter_goal", "")[:30])
        logger.info(f"[plot_plan] Chapter goal: {plot.get('chapter_goal', '')[:50]}")
        return {"plot_structure": plot}

    async def camera_decide_node(state: ChapterGraphState) -> dict:
        # Gather previous POVs from chapter history
        story_id = state["story_id"]
        chapters = await sqlite.list_chapters(story_id)
        previous_povs = [ch.get("pov", "") for ch in chapters]

        _enter(state["story_id"], "camera_decide", "调用Camera Agent...")
        agent = CameraAgent(llm)
        decision = await agent.run(
            plot_structure=state["plot_structure"],
            character_profiles=state["character_profiles"],
            chapter_num=state["chapter_num"],
            previous_povs=previous_povs,
            story_id=state["story_id"],
        )
        _finish(state["story_id"], "camera_decide", f"POV: {decision.get('pov_character_id')}")
        logger.info(f"[camera_decide] POV: {decision.get('pov_character_id')}, pacing: {decision.get('pacing')}")
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
        # Get previous chapter summary for continuity
        prev_summary = ""
        if state["chapter_num"] > 1:
            prev = await sqlite.get_chapter(state["story_id"], state["chapter_num"] - 1)
            if prev:
                content = prev.get("content", "")
                prev_summary = content[:500] + "..." if len(content) > 500 else content

        # Build retry feedback from consistency result
        retry_feedback = ""
        if state.get("consistency_result") and not state["consistency_pass"]:
            issues = state["consistency_result"].get("issues", [])
            retry_feedback = "\n".join(
                f"- [{i.get('severity', '')}] {i.get('description', '')}: {i.get('suggestion', '')}"
                for i in issues
            )

        retry_num = state.get("retry_count", 0)
        _enter(state["story_id"], "write_chapter", f"调用Writer Agent...{f'(重试#{retry_num})' if retry_num else ''}")
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

    async def save_chapter_node(state: ChapterGraphState) -> dict:
        story_id = state["story_id"]

        # Save chapter to SQLite
        pov_id = state["camera_decision"].get("pov_character_id", "")
        # Resolve POV name
        pov_name = pov_id
        for c in state["character_profiles"]:
            if c.get("character_id") == pov_id:
                pov_name = c.get("name", pov_id)
                break

        events_covered = state["camera_decision"].get("visible_events", [])
        metadata = {
            "plot_structure": state["plot_structure"],
            "camera_decision": state["camera_decision"],
            "consistency_score": state["consistency_result"].get("score", 0) if state.get("consistency_result") else 0,
            "consistency_warnings": [],
            "retry_count": state.get("retry_count", 0),
        }

        # Generate chapter title via TitlerAgent
        try:
            titler = TitlerAgent(llm)
            title_result = await titler.run(
                chapter_draft=state["chapter_draft"],
                chapter_num=state["chapter_num"],
                story_title=state["story_bible"].get("title", "") if state.get("story_bible") else "",
                chapter_goal=state["plot_structure"].get("chapter_goal", "") if state.get("plot_structure") else "",
                story_id=story_id,
            )
            title = title_result.get("title", "")[:20]
        except Exception as e:
            logger.warning(f"[save_chapter] Titler failed, using fallback: {e}")
            title = state["plot_structure"].get("chapter_goal", "")[:20] if state.get("plot_structure") else ""

        await sqlite.save_chapter(
            story_id=story_id,
            chapter_num=state["chapter_num"],
            title=title,
            pov=pov_name,
            content=state["chapter_draft"],
            events=events_covered,
            metadata=metadata,
        )

        # Update world state
        await sqlite.save_world_state(
            story_id, state["world_state"], state["world_state"].get("version", 0)
        )

        # Append new events to event graph
        json_store.append_events(story_id, state["new_events"])

        _enter(state["story_id"], "save_chapter")
        _finish(state["story_id"], "save_chapter", f"保存成功 — {title}")
        logger.info(f"[save_chapter] Chapter {state['chapter_num']} saved successfully")
        return {"error_message": ""}

    async def save_with_warning_node(state: ChapterGraphState) -> dict:
        # Same as save_chapter but with warnings
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
        metadata = {
            "plot_structure": state["plot_structure"],
            "camera_decision": state["camera_decision"],
            "consistency_score": state["consistency_result"].get("score", 0) if state.get("consistency_result") else 0,
            "consistency_warnings": warnings,
            "retry_count": state.get("retry_count", 0),
        }

        # Generate chapter title via TitlerAgent
        try:
            titler = TitlerAgent(llm)
            title_result = await titler.run(
                chapter_draft=state["chapter_draft"],
                chapter_num=state["chapter_num"],
                story_title=state["story_bible"].get("title", "") if state.get("story_bible") else "",
                chapter_goal=state["plot_structure"].get("chapter_goal", "") if state.get("plot_structure") else "",
                story_id=story_id,
            )
            title = title_result.get("title", "")[:20]
        except Exception as e:
            logger.warning(f"[save_with_warning] Titler failed, using fallback: {e}")
            title = state["plot_structure"].get("chapter_goal", "")[:20] if state.get("plot_structure") else ""

        await sqlite.save_chapter(
            story_id=story_id,
            chapter_num=state["chapter_num"],
            title=title,
            pov=pov_name,
            content=state["chapter_draft"],
            events=events_covered,
            metadata=metadata,
        )

        await sqlite.save_world_state(
            story_id, state["world_state"], state["world_state"].get("version", 0)
        )
        json_store.append_events(story_id, state["new_events"])

        logger.warning(f"[save_with_warning] Chapter {state['chapter_num']} '{title}' saved with {len(warnings)} warnings")
        return {"error_message": f"章节已保存，但存在{len(warnings)}个一致性警告"}

    async def extract_memories_node(state: ChapterGraphState) -> dict:
        story_id = state["story_id"]
        _enter(story_id, "extract_memories", "提取角色记忆...")

        if chapter_extractor and state.get("chapter_draft"):
            try:
                result = await chapter_extractor.extract_and_save(
                    story_id=story_id,
                    chapter_num=state["chapter_num"],
                    chapter_content=state["chapter_draft"],
                    character_profiles=state["character_profiles"],
                    camera_decision=state.get("camera_decision", {}),
                )
                detail = f"{len(result.character_memories)}条记忆, {len(result.relationship_changes)}条关系"
                _finish(story_id, "extract_memories", detail)
            except Exception as e:
                logger.error(f"[extract_memories] Failed: {e}")
                _finish(story_id, "extract_memories", f"提取失败: {str(e)[:50]}")
        else:
            _finish(story_id, "extract_memories", "跳过（无提取器）")

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

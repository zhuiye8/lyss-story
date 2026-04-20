"""Keyword-triggered world book (Phase 3).

World facts (factions, locations, power system, rules, special abilities, etc.)
are registered as entries with trigger keywords. Before generation we scan the
current plan/outline/tail and only inject entries whose keys are mentioned.
This avoids dumping the entire world bible into every prompt.
"""
import logging

from backend.storage.sqlite_store import SQLiteStore

logger = logging.getLogger(__name__)


class WorldBook:
    def __init__(self, sqlite: SQLiteStore):
        self.sqlite = sqlite

    async def sync_from_bible(self, story_id: str, bible: dict) -> int:
        """Extract entries from a story_bible dict into world_book_entries.

        Rebuilds the whole entry set to reflect the latest bible.
        Returns number of entries saved.
        """
        await self.sqlite.clear_world_book(story_id)
        count = 0

        world = bible.get("world") or {}

        # Special ability (金手指) — always active (核心设定)
        special = world.get("special_ability") or {}
        if isinstance(special, dict) and special.get("name"):
            name = special["name"]
            triggers = self._clean_triggers(special.get("trigger_keys"), default=[name])
            desc = special.get("description", "")
            functions = special.get("functions") or []
            if functions:
                desc += "\n功能：" + "；".join(functions)
            await self.sqlite.upsert_world_book_entry(
                story_id=story_id,
                entry_type="special_ability",
                entry_id="special_ability",
                name=name,
                description=desc.strip(),
                trigger_keys=triggers,
                priority=100,
                always_active=True,
            )
            count += 1

        # Factions
        factions = world.get("factions") or []
        for idx, f in enumerate(factions):
            if not isinstance(f, dict):
                continue
            name = f.get("name") or f"势力{idx+1}"
            triggers = self._clean_triggers(f.get("trigger_keys"), default=[name])
            desc = f.get("description", "")
            stance = f.get("stance", "")
            if stance:
                desc += f"\n立场：{stance}"
            await self.sqlite.upsert_world_book_entry(
                story_id=story_id,
                entry_type="faction",
                entry_id=f"faction_{idx}_{name}",
                name=name,
                description=desc.strip(),
                trigger_keys=triggers,
                priority=50,
                always_active=False,
            )
            count += 1

        # Power system
        power = world.get("power_system") or bible.get("power_system")
        if isinstance(power, dict) and power.get("name"):
            name = power["name"]
            triggers = self._clean_triggers(
                power.get("trigger_keys"),
                default=[name] + list(power.get("levels") or [])[:3],
            )
            levels = power.get("levels") or []
            rules = power.get("rules") or []
            desc_parts = []
            if levels:
                desc_parts.append("境界：" + "→".join([str(x) for x in levels]))
            if rules:
                desc_parts.append("规则：" + "；".join([str(x) for x in rules]))
            await self.sqlite.upsert_world_book_entry(
                story_id=story_id,
                entry_type="power_system",
                entry_id="power_system",
                name=name,
                description="\n".join(desc_parts),
                trigger_keys=triggers,
                priority=80,
                always_active=True,
            )
            count += 1

        # World rules (top level or inside world)
        world_rules = bible.get("world_rules") or world.get("world_rules") or []
        for idx, r in enumerate(world_rules):
            if not isinstance(r, dict):
                continue
            rid = r.get("rule_id") or f"R{idx+1}"
            desc = r.get("description", "")
            if not desc:
                continue
            triggers = self._clean_triggers(
                r.get("trigger_keys"), default=self._auto_keys_from_text(desc, max_keys=3)
            )
            await self.sqlite.upsert_world_book_entry(
                story_id=story_id,
                entry_type="world_rule",
                entry_id=f"rule_{rid}",
                name=rid,
                description=desc,
                trigger_keys=triggers,
                priority=40,
                always_active=False,
            )
            count += 1

        # World background — always active core lore
        bg = world.get("world_background")
        if bg:
            await self.sqlite.upsert_world_book_entry(
                story_id=story_id,
                entry_type="background",
                entry_id="world_background",
                name="世界背景",
                description=bg[:800],
                trigger_keys=[],
                priority=90,
                always_active=True,
            )
            count += 1

        logger.info(f"[WorldBook] Synced {count} entries for story {story_id}")
        return count

    @staticmethod
    def _clean_triggers(raw, default: list[str] | None = None) -> list[str]:
        if not raw:
            return [k for k in (default or []) if k]
        if isinstance(raw, str):
            return [k.strip() for k in raw.split(",") if k.strip()]
        if isinstance(raw, list):
            return [str(k).strip() for k in raw if str(k).strip()]
        return default or []

    @staticmethod
    def _auto_keys_from_text(text: str, max_keys: int = 3) -> list[str]:
        """Crude fallback: pick the first few 2-4 char tokens."""
        import re
        tokens = re.findall(r"[\u4e00-\u9fa5]{2,4}", text or "")
        seen: list[str] = []
        for t in tokens:
            if t not in seen:
                seen.append(t)
            if len(seen) >= max_keys:
                break
        return seen

    async def get_triggered(
        self,
        story_id: str,
        scan_text: str,
        max_entries: int = 5,
        char_budget: int = 1500,
    ) -> list[dict]:
        """Scan scan_text, return hit entries (+always_active), capped to budgets."""
        entries = await self.sqlite.list_world_book_entries(story_id)
        scored: list[tuple[int, int, dict]] = []  # (hit_count, priority, entry)
        always_on: list[dict] = []

        for e in entries:
            if e.get("always_active"):
                always_on.append(e)
                continue
            keys = e.get("trigger_keys") or []
            if not keys:
                continue
            hits = sum(1 for k in keys if k and k in scan_text)
            if hits > 0:
                scored.append((hits, e.get("priority", 0), e))

        # Sort by hit_count desc, then priority desc
        scored.sort(key=lambda t: (-t[0], -t[1]))
        triggered = [e for _, _, e in scored[:max_entries]]

        # Combine always-on (by priority) + triggered
        always_on.sort(key=lambda e: -e.get("priority", 0))
        combined = always_on + [e for e in triggered if e not in always_on]

        # Budget truncate
        total = 0
        out = []
        for e in combined:
            desc_len = len(e.get("description", "")) + len(e.get("name", "")) + 5
            if total + desc_len > char_budget and out:
                break
            out.append(e)
            total += desc_len
        return out

    @staticmethod
    def format_for_prompt(entries: list[dict]) -> str:
        if not entries:
            return ""
        lines = []
        for e in entries:
            title = f"[{e.get('entry_type', '')}] {e.get('name', '')}"
            desc = e.get("description", "")
            if desc:
                lines.append(f"{title}\n{desc}")
            else:
                lines.append(title)
        return "\n\n".join(lines)

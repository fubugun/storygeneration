"""下载并整理课程项目使用的公开中文故事数据。

数据来源：
1. Jiann/STORAL：人工中文寓言故事
2. SuperYuanAI/PACE-SFT-DATASETS：中文剧情续写
3. i0445/islm-stories：关键词控制故事

运行：python collect_real_data.py
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Iterable

from datasets import load_dataset

try:
    import jieba.analyse
except ImportError:
    jieba = None


OUTPUT_DIR = Path("data/real")
SYSTEM_PROMPT = (
    "你是一名中文短故事作者。请自然使用给定关键词，遵守人物和世界观设定，"
    "写出具有开端、发展和结局的完整故事。"
)

BLOCKED_TERMS = {
    "强奸",
    "乱伦",
    "色情",
    "性虐",
    "露骨性描写",
}


def clean_text(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    text = text.replace("\u3000", " ").replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def valid_story(story: str, minimum: int = 100, maximum: int = 5000) -> bool:
    if not minimum <= len(story) <= maximum:
        return False
    if any(term in story for term in BLOCKED_TERMS):
        return False
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", story))
    return chinese_chars >= minimum * 0.55


def story_hash(story: str) -> str:
    normalized = re.sub(r"\W+", "", story).lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def fallback_keywords(story: str, limit: int = 4) -> list[str]:
    chunks = re.findall(r"[\u4e00-\u9fff]{2,8}", story)
    stop = {"一个", "自己", "他们", "我们", "这个", "那个", "后来", "最后", "因为"}
    counter: Counter[str] = Counter()
    for chunk in chunks:
        for size in (2, 3):
            for index in range(max(0, len(chunk) - size + 1)):
                token = chunk[index : index + size]
                if token not in stop:
                    counter[token] += 1
    return [word for word, _ in counter.most_common(limit)]


def extract_keywords(story: str, limit: int = 4) -> list[str]:
    if jieba is not None:
        words = [
            clean_text(word)
            for word in jieba.analyse.extract_tags(story, topK=limit * 2)
            if 2 <= len(clean_text(word)) <= 8
        ]
        if len(words) >= 2:
            return words[:limit]
    return fallback_keywords(story, limit)


def make_record(
    system: str,
    user: str,
    assistant: str,
    source: str,
    source_id: str,
) -> dict:
    return {
        "messages": [
            {"role": "system", "content": clean_text(system)},
            {"role": "user", "content": clean_text(user)},
            {"role": "assistant", "content": clean_text(assistant)},
        ],
        "source": source,
        "source_id": source_id,
    }


def storal_records(split: str) -> Iterable[dict]:
    dataset = load_dataset("Jiann/STORAL", split=split)
    for row in dataset:
        story = clean_text(row["story"])
        moral = clean_text(row["moral"])
        if not valid_story(story):
            continue
        keywords = extract_keywords(story)
        user = (
            f"关键词：{'、'.join(keywords)}\n"
            f"故事主题：{moral}\n"
            "角色要求：自行设定一名主角，并保持人物性格前后一致。\n"
            f"篇幅：约{len(story)}字"
        )
        yield make_record(
            SYSTEM_PROMPT,
            user,
            story,
            "Jiann/STORAL",
            f"storal-{split}-{row['id']}",
        )


def pace_records(split: str) -> Iterable[dict]:
    dataset = load_dataset("SuperYuanAI/PACE-SFT-DATASETS", split=split)
    for index, row in enumerate(dataset):
        if row.get("task") != "continuation":
            continue
        messages = row.get("messages") or []
        if len(messages) < 3:
            continue
        assistant = clean_text(messages[-1].get("content"))
        if not valid_story(assistant, minimum=160, maximum=7000):
            continue
        normalized_messages = [
            {
                "role": clean_text(message.get("role")),
                "content": clean_text(message.get("content")),
            }
            for message in messages
            if message.get("role") in {"system", "user", "assistant"}
            and clean_text(message.get("content"))
        ]
        if len(normalized_messages) < 3:
            continue
        yield {
            "messages": normalized_messages,
            "source": "SuperYuanAI/PACE-SFT-DATASETS",
            "source_id": f"pace-{split}-{row.get('ip_id', index)}-{index}",
        }


def islm_records(split: str) -> Iterable[dict]:
    dataset = load_dataset("i0445/islm-stories", "default", split=split)
    for row in dataset:
        if row.get("language") != "zh":
            continue
        messages = row.get("messages") or []
        assistant = next(
            (
                clean_text(message.get("content"))
                for message in reversed(messages)
                if message.get("role") == "assistant"
            ),
            "",
        )
        if not valid_story(assistant, minimum=80, maximum=3000):
            continue
        keywords = [clean_text(word) for word in row.get("target_words", []) if word]
        theme = clean_text(row.get("theme")) or "日常生活"
        user = (
            f"关键词：{'、'.join(keywords)}\n"
            f"故事主题：{theme}\n"
            "角色要求：设置一名明确的主角，并保持人物行为一致。\n"
            f"篇幅：约{len(assistant)}字"
        )
        yield make_record(
            SYSTEM_PROMPT,
            user,
            assistant,
            "i0445/islm-stories",
            f"islm-{row.get('id')}",
        )


def deduplicate(records: Iterable[dict], seen: set[str]) -> list[dict]:
    result: list[dict] = []
    for record in records:
        story = record["messages"][-1]["content"]
        digest = story_hash(story)
        if digest in seen:
            continue
        seen.add(digest)
        result.append(record)
    return result


def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()

    split_sources = {
        "train": [
            storal_records("storal_zh_train"),
            pace_records("train"),
            islm_records("train"),
        ],
        "validation": [
            storal_records("storal_zh_valid"),
            pace_records("validation"),
            islm_records("validation"),
        ],
        "test": [
            storal_records("storal_zh_test"),
            islm_records("test"),
        ],
    }

    stats: dict[str, object] = {"splits": {}, "sources": {}}
    for split_name, sources in split_sources.items():
        combined: list[dict] = []
        for source_records in sources:
            source_list = deduplicate(source_records, seen)
            combined.extend(source_list)
            if source_list:
                source_name = source_list[0]["source"]
                stats["sources"].setdefault(source_name, 0)
                stats["sources"][source_name] += len(source_list)
        write_jsonl(OUTPUT_DIR / f"{split_name}.jsonl", combined)
        stats["splits"][split_name] = len(combined)
        print(f"{split_name}: {len(combined)}")

    stats["total"] = sum(stats["splits"].values())
    with (OUTPUT_DIR / "stats.json").open("w", encoding="utf-8") as file:
        json.dump(stats, file, ensure_ascii=False, indent=2)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


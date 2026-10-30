"""把简单故事 JSONL 转换为 LLaMA-Factory 的 messages 格式。

输入每行示例：
{"keywords":["森林","机器人"],"character":"小林","identity":"学生","personality":"勇敢","goal":"找到出口","genre":"科幻","tone":"温暖","story":"正文"}
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path


SYSTEM_PROMPT = (
    "你是一名中文短故事作者。请严格遵守人物设定，自然使用所有关键词，"
    "故事应有开端、发展和结局。"
)


def convert(record: dict) -> dict:
    keywords = record.get("keywords", [])
    if isinstance(keywords, str):
        keywords = [item.strip() for item in keywords.replace("，", ",").split(",")]
    story = str(record.get("story", "")).strip()
    if not story:
        raise ValueError("缺少 story 字段")

    user = (
        f"关键词：{'、'.join(keywords)}\n"
        f"故事类型：{record.get('genre', '不限')}\n"
        f"情感基调：{record.get('tone', '不限')}\n"
        f"主角：{record.get('character', '主人公')}\n"
        f"身份：{record.get('identity', '普通人')}\n"
        f"性格：{record.get('personality', '善良')}\n"
        f"目标：{record.get('goal', '解决眼前的问题')}\n"
        f"篇幅：约{record.get('length', len(story))}字"
    )
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
            {"role": "assistant", "content": story},
        ]
    }


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/sample_stories.jsonl")
    parser.add_argument("--output", default="data/processed")
    args = parser.parse_args()

    source = Path(args.input)
    output = Path(args.output)
    converted: list[dict] = []
    seen: set[str] = set()

    with source.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
                story = str(raw.get("story", "")).strip()
                digest = hashlib.sha256(story.encode("utf-8")).hexdigest()
                if len(story) < 80 or digest in seen:
                    continue
                seen.add(digest)
                converted.append(convert(raw))
            except Exception as exc:
                print(f"跳过第{line_number}行：{exc}")

    random.Random(42).shuffle(converted)
    total = len(converted)
    if total >= 3:
        validation_size = max(1, int(total * 0.1))
        test_size = max(1, int(total * 0.1))
        train_end = total - validation_size - test_size
        valid_end = train_end + validation_size
    else:
        train_end = total
        valid_end = total
    write_jsonl(output / "train.jsonl", converted[:train_end])
    write_jsonl(output / "validation.jsonl", converted[train_end:valid_end])
    write_jsonl(output / "test.jsonl", converted[valid_end:])
    print(f"处理完成：共{total}条，输出到 {output}")


if __name__ == "__main__":
    main()


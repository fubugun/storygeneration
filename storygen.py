"""个性化故事生成器的核心逻辑。

默认使用 demo 模式，方便没有 GPU 时演示。
设置 STORYGEN_BACKEND=hf 后可加载真实的 Qwen 模型。
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class StoryRequest:
    keywords: list[str]
    character_name: str
    character_identity: str
    personality: str
    character_goal: str
    genre: str
    tone: str
    length: int = 600

    @classmethod
    def from_form(
        cls,
        keywords: str,
        character_name: str,
        character_identity: str,
        personality: str,
        character_goal: str,
        genre: str,
        tone: str,
        length: int,
    ) -> "StoryRequest":
        keyword_list = [
            item.strip()
            for item in re.split(r"[,，、\s]+", keywords)
            if item.strip()
        ]
        if not keyword_list:
            raise ValueError("请至少输入一个关键词。")
        return cls(
            keywords=keyword_list[:8],
            character_name=character_name.strip() or "林安",
            character_identity=character_identity.strip() or "普通学生",
            personality=personality.strip() or "善良、勇敢",
            character_goal=character_goal.strip() or "解决眼前的困难",
            genre=genre,
            tone=tone,
            length=int(length),
        )


def build_messages(request: StoryRequest, feedback: str = "") -> list[dict[str, str]]:
    system = (
        "你是一名中文短故事作者。请严格遵守人物设定，自然使用所有关键词。"
        "主角的姓名、身份、性格和目标在全文中不得改变；如果主角是人类，"
        "不得将其写成机器人或其他身份。故事应有开端、发展、转折和结局，"
        "不要增加复杂亲属关系，不要解释创作过程。"
    )
    user = (
        f"关键词：{'、'.join(request.keywords)}\n"
        f"故事类型：{request.genre}\n"
        f"情感基调：{request.tone}\n"
        f"主角：{request.character_name}\n"
        f"身份：{request.character_identity}\n"
        f"性格：{request.personality}\n"
        f"目标：{request.character_goal}\n"
        f"篇幅：约{request.length}字\n"
        "写作要求：全部关键词自然出现；主角身份前后一致；结局回应主角目标。"
    )
    if feedback:
        user += f"\n上一版存在以下问题，请修正后重写：{feedback}"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def check_story(story: str, request: StoryRequest) -> dict[str, Any]:
    missing = [word for word in request.keywords if word not in story]
    keyword_coverage = (len(request.keywords) - len(missing)) / len(request.keywords)

    character_items = [request.character_name, request.character_identity]
    character_hits = sum(1 for item in character_items if item and item in story)
    character_score = character_hits / len(character_items)

    identity_conflicts: list[str] = []
    human_markers = (
        "人类", "修理师", "学生", "教师", "医生", "记者", "警察", "作家", "司机", "店主"
    )
    if any(marker in request.character_identity for marker in human_markers):
        escaped_name = re.escape(request.character_name)
        robot_patterns = (
            rf"机器人{escaped_name}",
            rf"{escaped_name}(?:原来|其实|竟然|本来)?是(?:一台|一个)?机器人",
        )
        if any(re.search(pattern, story) for pattern in robot_patterns):
            identity_conflicts.append("人类主角被写成机器人")
    if identity_conflicts:
        character_score = 0.0

    development_words = ("突然", "然而", "后来", "直到", "却", "于是")
    ending_words = ("最后", "终于", "从此", "那一刻", "明白", "回家", "约定")
    has_development = any(word in story for word in development_words)
    has_ending = any(word in story[-160:] for word in ending_words)
    structure_score = (int(bool(story.strip())) + int(has_development) + int(has_ending)) / 3

    length_ratio = len(story) / max(request.length, 1)
    length_ok = 0.6 <= length_ratio <= 1.5
    passed = (
        keyword_coverage >= 0.85
        and character_score >= 0.5
        and not identity_conflicts
        and structure_score >= 0.66
        and length_ok
    )

    issues: list[str] = []
    if missing:
        issues.append("遗漏关键词：" + "、".join(missing))
    if character_score < 0.5:
        issues.append("主角身份或姓名体现不足")
    if identity_conflicts:
        issues.extend(identity_conflicts)
    if structure_score < 0.66:
        issues.append("故事缺少明显的发展或结局")
    if not length_ok:
        issues.append(f"当前约{len(story)}字，与目标{request.length}字差距较大")

    return {
        "通过质检": passed,
        "关键词覆盖率": f"{keyword_coverage:.0%}",
        "角色一致性": f"{character_score:.0%}",
        "结构完整度": f"{structure_score:.0%}",
        "实际字数": len(story),
        "角色冲突": identity_conflicts or ["未发现"],
        "问题": issues or ["未发现明显问题"],
    }


def demo_generate(request: StoryRequest, attempt: int = 1) -> str:
    """无需模型的演示生成器，用于课堂展示页面和功能流程。"""

    name = request.character_name
    identity = request.character_identity
    keywords = request.keywords
    first = keywords[0]
    second = keywords[1] if len(keywords) > 1 else "秘密"
    rest = "、".join(keywords[2:]) or "一段被遗忘的往事"

    paragraphs = [
        f"《{first}与{second}》\n",
        (
            f"傍晚，{request.tone}的光落在城市边缘。{name}是一名{identity}，"
            f"性格{request.personality}。这一天，{name}在{first}附近发现了{second}，"
            "原本平静的生活因此改变。"
        ),
        (
            f"{name}一直想要{request.character_goal}。眼前的线索同时指向{rest}，"
            "每一个细节都像在提醒他，有人正等待一个迟到了很久的答案。"
        ),
        (
            "突然，远处传来一阵急促的声响。主角没有立刻追上去，而是先检查周围，"
            "再把散落的线索按时间排好。看似无关的事物，渐渐连成了同一条道路。"
        ),
        (
            f"然而，真正的困难并不是找到答案，而是决定是否相信它。{name}想起自己的目标，"
            "也想起一路上帮助过自己的人，最终选择继续向前。"
        ),
        (
            f"后来，{keywords[-1]}再次出现。{name}终于明白，这场经历并非偶然。"
            "它既是一道考验，也是一封写给未来的信。"
        ),
        (
            f"最后，{name}完成了自己的目标。清晨到来时，{first}仍留在原处，"
            f"而{second}已经有了新的意义。从此以后，{name}不再害怕未知，"
            "因为他知道，真正重要的答案往往藏在愿意坚持的人心里。"
        ),
    ]

    extras = [
        "风从街道尽头吹来，旧招牌发出轻微的响声，像是在为这次选择作证。",
        "他把重要的细节记在随身的小本子上，也把自己的犹豫诚实地写了进去。",
        "路上的人并不知道发生了什么，但一个善意的眼神仍给了他继续前进的勇气。",
        "夜色渐深，周围变得安静，只有脚步声提醒他已经离答案越来越近。",
        "过去的误会在交谈中慢慢解开，原本互不信任的人也开始愿意彼此倾听。",
        "当所有线索重新摆在面前时，他发现最早被忽略的细节反而最接近真相。",
    ]
    insert_at = -1
    extra_index = 0
    while len("".join(paragraphs)) < request.length * 0.85:
        paragraphs.insert(insert_at, extras[extra_index % len(extras)])
        extra_index += 1
        if extra_index > 12:
            break

    return "\n\n".join(paragraphs)


class HFGenerator:
    """Transformers 后端。只有选择 hf 模式时才导入大型依赖。"""

    def __init__(self) -> None:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "HF模式需要安装 torch、transformers、accelerate 和 peft。"
            ) from exc

        self.torch = torch
        self.model_name = os.getenv(
            "STORYGEN_MODEL", "Qwen/Qwen3-4B-Instruct-2507"
        )
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype="auto",
            device_map="auto",
        )

        adapter = os.getenv("STORYGEN_ADAPTER", "").strip()
        if adapter:
            from peft import PeftModel

            self.model = PeftModel.from_pretrained(self.model, adapter)

    def generate(self, request: StoryRequest, feedback: str = "") -> str:
        messages = build_messages(request, feedback)
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer([prompt], return_tensors="pt").to(self.model.device)
        max_new_tokens = min(max(request.length * 2, 512), 2048)
        with self.torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.65,
                top_p=0.85,
                repetition_penalty=1.15,
            )
        generated = output[0][inputs.input_ids.shape[1] :]
        return self.tokenizer.decode(generated, skip_special_tokens=True).strip()


class StoryService:
    def __init__(self) -> None:
        self.backend = os.getenv("STORYGEN_BACKEND", "demo").lower()
        self.hf_generator = HFGenerator() if self.backend == "hf" else None

    def generate(self, request: StoryRequest) -> tuple[str, dict[str, Any], int]:
        feedback = ""
        story = ""
        report: dict[str, Any] = {}
        for attempt in range(1, 4):
            if self.hf_generator:
                story = self.hf_generator.generate(request, feedback)
            else:
                story = demo_generate(request, attempt)
            report = check_story(story, request)
            if report["通过质检"]:
                return story, report, attempt
            feedback = "；".join(report["问题"])
        return story, report, 3


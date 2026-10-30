"""Gradio 网页入口。运行：python app.py"""

import json
import os

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

import gradio as gr

from storygen import StoryRequest, StoryService


service = StoryService()


def generate_story(
    keywords: str,
    name: str,
    identity: str,
    personality: str,
    goal: str,
    genre: str,
    tone: str,
    length: int,
):
    try:
        request = StoryRequest.from_form(
            keywords,
            name,
            identity,
            personality,
            goal,
            genre,
            tone,
            length,
        )
        story, report, attempts = service.generate(request)
        status = f"生成后端：{service.backend}　尝试次数：{attempts}\n\n"
        status += "```json\n" + json.dumps(report, ensure_ascii=False, indent=2) + "\n```"
        return story, status
    except Exception as exc:
        return "", f"生成失败：{exc}"


with gr.Blocks(title="个性化故事生成器") as demo:
    gr.Markdown(
        "# 个性化故事生成器\n"
        "输入关键词和角色设定，生成一篇中文短故事。"
    )
    with gr.Row():
        with gr.Column():
            keywords = gr.Textbox(
                label="关键词",
                value="雨夜，旧车站，机器人，重逢",
                placeholder="用逗号分隔，建议3至6个",
            )
            name = gr.Textbox(label="角色姓名", value="陈安")
            identity = gr.Textbox(label="角色身份", value="人类机械修理师")
            personality = gr.Textbox(label="角色性格", value="沉默、善良、谨慎")
            goal = gr.Textbox(label="角色目标", value="寻找十年前失踪的朋友")
            genre = gr.Dropdown(
                ["童话", "科幻", "校园", "悬疑", "都市", "冒险"],
                value="科幻",
                label="故事类型",
            )
            tone = gr.Dropdown(
                ["温暖", "紧张", "幽默", "悲伤", "治愈"],
                value="温暖",
                label="情感基调",
            )
            length = gr.Slider(200, 600, value=300, step=50, label="目标字数")
            button = gr.Button("生成故事", variant="primary")
        with gr.Column():
            story = gr.Textbox(label="生成结果", lines=22)
            report = gr.Markdown()

    button.click(
        generate_story,
        inputs=[keywords, name, identity, personality, goal, genre, tone, length],
        outputs=[story, report],
    )


if __name__ == "__main__":
    demo.launch(
        server_name=os.getenv("STORYGEN_HOST", "127.0.0.1"),
        server_port=int(os.getenv("STORYGEN_PORT", "7860")),
    )


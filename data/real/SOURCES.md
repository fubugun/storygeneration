# 真实故事数据来源

本目录由 `collect_real_data.py` 生成，数据仅用于课程研究和模型实验。

## Jiann/STORAL

- 地址：https://huggingface.co/datasets/Jiann/STORAL
- 原始项目：https://github.com/thu-coai/MoralStory
- 内容：人工编写的中文寓言故事和故事寓意
- 用途：训练完整短故事结构和主题控制
- 注意：公开页面没有明确给出数据再发布许可证。课程实验中保留来源，不单独公开原始故事。

## SuperYuanAI/PACE-SFT-DATASETS

- 地址：https://huggingface.co/datasets/SuperYuanAI/PACE-SFT-DATASETS
- 许可证：Apache 2.0
- 内容：中文剧情续写、分析和评价数据
- 用途：只选择 `continuation` 数据，训练世界观和角色设定下的剧情续写
- 注意：数据由大模型生成，可能带有教师模型偏差。

## i0445/islm-stories

- 地址：https://huggingface.co/datasets/i0445/islm-stories
- 许可证：MIT
- 内容：面向语言学习的关键词控制故事
- 用途：只选择精选版本中的中文数据，训练关键词覆盖能力

## 使用原则

- 每条训练记录保留 `source` 和 `source_id`。
- 训练、验证、测试沿用原数据集划分。
- 全局去重，防止相同故事跨数据集或跨划分泄漏。
- 过滤明显不适合课堂展示的内容。
- 不使用来源不明的网络小说爬取数据。


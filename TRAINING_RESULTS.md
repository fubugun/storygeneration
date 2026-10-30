# Qwen3-4B 个性化故事生成微调结果

## 实验配置

- 基座模型：`Qwen/Qwen3-4B-Instruct-2507`
- 微调方式：4-bit QLoRA
- 训练数据：1200 条中文短故事
- 验证数据：403 条中文短故事
- 训练轮数：1
- 最大序列长度：768
- LoRA Rank：8
- LoRA Alpha：16
- 训练设备：Google Colab Tesla T4

## 训练结果

- 训练损失：2.498
- 验证损失：2.4228
- 训练耗时：28 分 11 秒
- 验证耗时：3 分 08 秒
- 训练速度：0.089 step/s
- 模型目录：`/content/drive/MyDrive/storygen_qwen3_lora_20261029`

训练和验证流程均正常完成。验证损失略低于训练损失，未出现明显发散。日志中的 `No metric eval_accuracy to plot` 是因为文本生成任务没有配置分类准确率指标，不影响模型使用。

## 已保存的文件

- LoRA 适配器权重及配置
- Tokenizer 配置与聊天模板
- `training_loss.png`
- `training_eval_loss.png`

## 推理测试输入

- 关键词：雨夜、旧车站、机器人、重逢
- 主角：陈安，沉默善良的机械修理师
- 类型：温暖科幻
- 篇幅：600 字左右

推理时需要同时加载 Qwen3-4B 基座模型和上述 LoRA 适配器。

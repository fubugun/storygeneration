# 个性化故事生成器

数字媒体技术课程设计项目。用户输入关键词、角色设定、故事类型和篇幅，系统生成中文短故事，并检查关键词覆盖、角色信息和故事结构。

## 项目内容

- `app.py`：Gradio网页
- `storygen.py`：提示词、故事生成、质检和重试
- `prepare_data.py`：把原始故事转成微调数据
- `collect_real_data.py`：下载、清洗并整理公开故事数据
- `make_colab_bundle.py`：将本地数据和配置打包供Colab上传
- `data/sample_stories.jsonl`：示例数据
- `training/qwen3_4b_lora.yaml`：Qwen3-4B的LoRA训练配置
- `test_storygen.py`：基础测试
- `colab_train.ipynb`：QLoRA训练、优化后推理和云端Gradio演示
- `storygen_colab_bundle.zip`：本地生成的Colab训练包（不提交到公开仓库）
- `TRAINING_RESULTS.md`：本次Colab训练指标
- `INFERENCE_EVALUATION.md`：首次真实模型生成结果分析

## 1. 先运行测试

项目核心逻辑不需要额外依赖：

```powershell
git clone https://github.com/fubugun/storygeneration.git
cd storygeneration
python -m unittest -v
```

## 2. 运行网页演示

安装Gradio：

```powershell
python -m pip install -r requirements.txt
python app.py
```

浏览器打开：`http://127.0.0.1:7860`

默认是 `demo` 模式，不需要GPU，适合先展示系统流程。

## 3. 准备训练数据

原始数据每行是一个JSON对象，至少包含 `story`，建议同时提供关键词和角色信息。

```powershell
python prepare_data.py --input data/sample_stories.jsonl --output data/processed
```

程序将输出：

- `data/processed/train.jsonl`
- `data/processed/validation.jsonl`
- `data/processed/test.jsonl`

正式训练时，将收集的数据整理成和 `sample_stories.jsonl` 相同的格式即可。

### 已收集的真实数据

运行：

```powershell
python -m pip install -r requirements-data.txt
python collect_real_data.py
```

当前已生成的数据位于 `data/real`：

- 训练集：4245条
- 验证集：529条
- 测试集：438条
- 总计：5212条

来源包括 STORAL、PACE-SFT 和 i+1 Story。详细许可和用途见 `data/real/SOURCES.md`。

公开仓库不包含完整故事正文。运行上述命令后，数据会在本地生成，并被 `.gitignore` 排除，避免重复发布来源许可证不明确的数据。

## 4. 微调Qwen3-4B

训练建议在Linux、实验室服务器或云GPU上进行。安装LLaMA-Factory后，把：

- `data/processed` 放到LLaMA-Factory的数据目录
- `training/dataset_info.json` 合并到其 `dataset_info.json`
- 使用 `training/qwen3_4b_lora.yaml` 启动训练

示例命令：

```bash
llamafactory-cli train training/qwen3_4b_lora.yaml
```

先用500条数据跑通，再扩大到完整数据集。

### 没有GPU时使用Colab

1. 在本地运行 `python collect_real_data.py`。
2. 运行 `python make_colab_bundle.py` 生成 `storygen_colab_bundle.zip`。
3. 打开 `colab_train.ipynb`，在Colab中选择T4 GPU。
4. 按提示上传刚生成的压缩包并运行后续单元格。

本次课程实验使用1200条训练数据训练1轮，LoRA结果保存在Google Drive的 `storygen_qwen3_lora_20261029` 文件夹。

已完成的训练结果：训练损失2.498，验证损失2.4228；训练耗时约28分钟，验证耗时约3分钟。损失曲线和LoRA适配器均已保存到上述Drive目录。

训练已经完成时，不需要再次运行训练单元。挂载Drive并运行“测试微调模型”单元即可；最后运行“启动课程演示网页”单元，会得到一个临时Gradio分享链接。

## 5. 接入真实模型

安装模型依赖：

```powershell
python -m pip install torch transformers accelerate peft bitsandbytes
```

设置环境变量后运行：

```powershell
$env:STORYGEN_BACKEND="hf"
$env:STORYGEN_MODEL="Qwen/Qwen3-4B-Instruct-2507"
$env:STORYGEN_ADAPTER="模型下载后的本地LoRA目录"
python app.py
```

没有LoRA权重时，可以不设置 `STORYGEN_ADAPTER`，此时运行原始模型作为对照。


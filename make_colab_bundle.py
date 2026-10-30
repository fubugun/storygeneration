"""将本地生成的数据和训练配置打包，供 Colab 上传使用。"""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "storygen_colab_bundle.zip"

FILES = {
    ROOT / "data" / "real" / "SOURCES.md": "real/SOURCES.md",
    ROOT / "data" / "real" / "stats.json": "real/stats.json",
    ROOT / "data" / "real" / "train.jsonl": "real/train.jsonl",
    ROOT / "data" / "real" / "validation.jsonl": "real/validation.jsonl",
    ROOT / "data" / "real" / "test.jsonl": "real/test.jsonl",
    ROOT / "training" / "dataset_info.json": "dataset_info.json",
    ROOT / "training" / "qwen3_4b_qlora_colab.yaml": "qwen3_4b_qlora_colab.yaml",
}


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in FILES if not path.exists()]
    if missing:
        raise SystemExit(
            "缺少训练数据，请先运行 python collect_real_data.py：\n- "
            + "\n- ".join(missing)
        )

    with ZipFile(OUTPUT, "w", compression=ZIP_DEFLATED) as archive:
        for source, archive_name in FILES.items():
            archive.write(source, archive_name)

    print(f"已生成：{OUTPUT}")


if __name__ == "__main__":
    main()


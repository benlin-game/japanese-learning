"""
副詞題庫擴充腳本
每個等級生成 25 個 JLPT 副詞
"""

import json
import sys
import time
from pathlib import Path
import google.generativeai as genai

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

GEMINI_API_KEY = (Path(__file__).parent / "gemini_key.txt").read_text(encoding="utf-8").strip()
ADVERB_COUNT = 100
SLEEP = 2.0
DATA_DIR = Path(__file__).parent / "docs" / "data"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")


def call_gemini(prompt: str) -> str:
    res = model.generate_content(prompt)
    return res.text.strip()


def extract_json_array(text: str) -> list:
    start = text.find("[")
    end = text.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError("找不到 JSON 陣列")
    return json.loads(text[start:end])


def generate_adverbs(level: str, existing: list) -> list:
    existing_words = [a["word"] for a in existing]
    exclude = "、".join(existing_words) if existing_words else "（無）"

    prompt = f"""你是日語教學專家。請列出 {ADVERB_COUNT} 個 JLPT {level} 程度的重要副詞。

排除以下已有副詞：{exclude}

每個副詞需包含：
- word：副詞（日文原字）
- reading：平假名讀音
- meaning：繁體中文意思（簡短）
- example：包含該副詞的自然日文例句
- example_meaning：例句繁體中文翻譯
- notes：使用說明或搭配注意事項（繁體中文，1句）

嚴格回覆以下 JSON 陣列格式，不加任何說明：
[
  {{
    "word": "副詞",
    "reading": "平假名",
    "meaning": "繁體中文意思",
    "example": "日文例句",
    "example_meaning": "例句中文翻譯",
    "notes": "使用說明"
  }}
]"""

    try:
        text = call_gemini(prompt)
        items = extract_json_array(text)
        return [a for a in items if a.get("word") not in existing_words]
    except Exception as e:
        print(f"  ⚠ 副詞生成失敗：{e}")
        return []


def process_level(level: str):
    print(f"\n{'='*40}")
    print(f"{level} 開始處理")

    json_path = DATA_DIR / f"{level.lower()}.json"
    data = json.loads(json_path.read_text(encoding="utf-8"))

    existing = data.get("adverb", [])
    need = ADVERB_COUNT - len(existing)

    if need <= 0:
        print(f"  副詞：已有 {len(existing)} 個，跳過")
    else:
        print(f"  副詞：現有 {len(existing)} 個，生成 {need} 個...")
        new_adverbs = generate_adverbs(level, existing)
        data["adverb"] = existing + new_adverbs
        print(f"  ✓ 副詞完成，共 {len(data['adverb'])} 個")

    time.sleep(SLEEP)

    json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  ✓ {level} 寫入完成")


def main():
    for level in ["N5", "N4", "N3", "N2", "N1"]:
        process_level(level)
    print("\n全部完成！記得 git add . && git commit && git push")


if __name__ == "__main__":
    main()

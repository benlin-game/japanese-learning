"""
擴充文法、漢字、JLPT 練習題腳本
目標：每個等級各 20 條文法、20 個漢字、20 題 JLPT 練習
"""

import json
import sys
import time
from pathlib import Path
import google.generativeai as genai

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

# ── 設定 ────────────────────────────────────
GEMINI_API_KEY = (Path(__file__).parent / "gemini_key.txt").read_text(encoding="utf-8").strip()
GRAMMAR_COUNT = 20
KANJI_COUNT = 20
PRACTICE_COUNT = 20
SLEEP = 2.0
DATA_DIR = Path(__file__).parent / "docs" / "data"
# ────────────────────────────────────────────

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


def generate_grammar(level: str, existing: list) -> list:
    existing_patterns = [g["pattern"] for g in existing]
    exclude = "、".join(existing_patterns[:10]) if existing_patterns else "（無）"

    prompt = f"""你是日語教學專家。請生成 {GRAMMAR_COUNT} 個 JLPT {level} 程度的文法句型。

排除以下已有句型：{exclude}

每個句型需包含：
- pattern：句型表示法（如 〜ている、〜によって）
- meaning：繁體中文意思（簡短）
- example：日文例句
- example_meaning：例句繁體中文翻譯
- notes：使用說明或注意事項（繁體中文，1～2句）

嚴格回覆以下 JSON 陣列格式，不加任何說明：
[
  {{
    "pattern": "〜句型",
    "meaning": "繁體中文意思",
    "example": "日文例句",
    "example_meaning": "例句中文翻譯",
    "notes": "使用說明"
  }}
]"""

    try:
        text = call_gemini(prompt)
        return extract_json_array(text)
    except Exception as e:
        print(f"  ⚠ 文法生成失敗：{e}")
        return []


def generate_kanji(level: str, existing: list) -> list:
    existing_kanji = [k["kanji"] for k in existing]
    exclude = "、".join(existing_kanji) if existing_kanji else "（無）"

    prompt = f"""你是日語教學專家。請列出 {KANJI_COUNT} 個 JLPT {level} 程度的重要漢字。

排除以下已有漢字：{exclude}

每個漢字需包含：
- kanji：漢字字元
- reading_on：音讀（片假名，多個用・分隔，沒有則填 —）
- reading_kun：訓讀（平假名，多個用・分隔，沒有則填 —）
- meaning：繁體中文意思
- examples：包含 2～3 個常見詞彙的陣列，格式「詞彙（讀音）中文意思」

嚴格回覆以下 JSON 陣列格式，不加任何說明：
[
  {{
    "kanji": "字",
    "reading_on": "音讀",
    "reading_kun": "訓讀",
    "meaning": "繁體中文意思",
    "examples": ["詞彙（讀音）中文意思", "詞彙（讀音）中文意思"]
  }}
]"""

    try:
        text = call_gemini(prompt)
        items = extract_json_array(text)
        # 去除已有的漢字
        return [k for k in items if k.get("kanji") not in existing_kanji]
    except Exception as e:
        print(f"  ⚠ 漢字生成失敗：{e}")
        return []


def generate_practice(level: str, vocab: list, grammar: list, kanji: list) -> list:
    # 從各類型取樣提供給 Gemini 出題
    v_sample = "、".join([v["word"] for v in vocab[:15]])
    g_sample = "、".join([g["pattern"] for g in grammar[:10]])
    k_sample = "、".join([k["kanji"] for k in kanji[:10]])

    prompt = f"""你是 JLPT 出題老師。請針對 {level} 程度出 {PRACTICE_COUNT} 題四選一選擇題，混合以下三種題型：
- 詞彙題（約 7 題）：考單字意思或用法
- 文法題（約 7 題）：考句型填空或辨別
- 漢字讀音題（約 6 題）：給漢字選正確讀音

參考單字：{v_sample}
參考文法：{g_sample}
參考漢字：{k_sample}

規則：
- 正確答案放在 options[0]（answer 固定為 0）
- type 填 "vocabulary"、"grammar" 或 "kanji"
- question 用日文
- explanation 用繁體中文說明

嚴格回覆以下 JSON 陣列格式，不加任何說明：
[
  {{
    "type": "vocabulary",
    "question": "日文題目",
    "options": ["正確答案", "錯誤1", "錯誤2", "錯誤3"],
    "answer": 0,
    "explanation": "繁體中文說明"
  }}
]"""

    try:
        import random
        text = call_gemini(prompt)
        items = extract_json_array(text)
        for item in items:
            opts = item.get("options", [])
            if len(opts) == 4:
                correct = opts[0]
                random.shuffle(opts)
                item["answer"] = opts.index(correct)
        return items
    except Exception as e:
        print(f"  ⚠ 練習題生成失敗：{e}")
        return []


def process_level(level: str):
    print(f"\n{'='*40}")
    print(f"{level} 開始處理")

    json_path = DATA_DIR / f"{level.lower()}.json"
    data = json.loads(json_path.read_text(encoding="utf-8"))

    existing_grammar = data.get("grammar", [])
    existing_kanji = data.get("kanji", [])
    existing_vocab = data.get("vocabulary", [])

    # ── 文法 ──
    need_grammar = GRAMMAR_COUNT - len(existing_grammar)
    if need_grammar > 0:
        print(f"  文法：現有 {len(existing_grammar)} 條，生成 {need_grammar} 條...")
        new_grammar = generate_grammar(level, existing_grammar)
        data["grammar"] = existing_grammar + new_grammar
        print(f"  ✓ 文法完成，共 {len(data['grammar'])} 條")
    else:
        print(f"  文法：已有 {len(existing_grammar)} 條，跳過")
    time.sleep(SLEEP)

    # ── 漢字 ──
    need_kanji = KANJI_COUNT - len(existing_kanji)
    if need_kanji > 0:
        print(f"  漢字：現有 {len(existing_kanji)} 個，生成 {need_kanji} 個...")
        new_kanji = generate_kanji(level, existing_kanji)
        data["kanji"] = existing_kanji + new_kanji
        print(f"  ✓ 漢字完成，共 {len(data['kanji'])} 個")
    else:
        print(f"  漢字：已有 {len(existing_kanji)} 個，跳過")
    time.sleep(SLEEP)

    # ── JLPT 練習 ──
    print(f"  JLPT 練習：生成 {PRACTICE_COUNT} 題（混合題型）...")
    new_practice = generate_practice(
        level, existing_vocab, data["grammar"], data["kanji"]
    )
    data["practice"] = new_practice
    print(f"  ✓ 練習題完成，共 {len(data['practice'])} 題")
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

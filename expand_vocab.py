"""
JLPT 題庫擴充腳本
來源：Bluskyo/JLPT_Vocabulary（單字 + 讀音）
補充：Gemini API（中文意思、例句、JLPT 練習題）
"""

import json
import time
import random
import sys
import urllib.request
from pathlib import Path
import google.generativeai as genai

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

# ── 設定區（修改這裡）────────────────────────────
GEMINI_API_KEY = "AIzaSyClkT9tu6m5fiYdXKSNy2PHHWifqPJigqQ"
WORDS_PER_LEVEL = 300  # 每個等級產生幾個單字
BATCH_SIZE = 10         # 每次 Gemini 呼叫處理幾個單字
SLEEP_BETWEEN_CALLS = 1.5  # 秒，避免 rate limit
# ──────────────────────────────────────────────

VOCAB_URL = "https://raw.githubusercontent.com/Bluskyo/JLPT_Vocabulary/main/data/vocab/results/JLPT_vocab_ALL.json"
DATA_DIR = Path(__file__).parent / "docs" / "data"
LEVEL_MAP = {1: "N1", 2: "N2", 3: "N3", 4: "N4", 5: "N5"}


def download_vocab() -> dict:
    print("下載單字清單...")
    with urllib.request.urlopen(VOCAB_URL, timeout=30) as res:
        data = json.loads(res.read().decode("utf-8"))
    print(f"  共 {len(data)} 個單字")
    return data


def group_by_level(raw: dict) -> dict[str, list[tuple[str, str]]]:
    groups: dict[str, list] = {f"N{i}": [] for i in range(1, 6)}
    for word, entries in raw.items():
        for entry in entries:
            key = LEVEL_MAP.get(entry.get("level"))
            if key:
                groups[key].append((word, entry["reading"]))
                break
    for k, v in groups.items():
        print(f"  {k}: {len(v)} 個")
    return groups


def call_gemini(model, prompt: str) -> str:
    res = model.generate_content(prompt)
    return res.text.strip()


def extract_json_array(text: str) -> list:
    start = text.find("[")
    end = text.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError("找不到 JSON 陣列")
    return json.loads(text[start:end])


def generate_vocab_batch(model, words: list[tuple[str, str]], level: str) -> list[dict]:
    word_list = "\n".join(f"{i+1}. {w}（{r}）" for i, (w, r) in enumerate(words))
    prompt = f"""你是日語教學專家。以下是 JLPT {level} 程度的日語單字，請為每個單字提供繁體中文意思、例句、例句讀音、例句中文翻譯。

必須嚴格回覆以下 JSON 陣列格式，不加任何說明文字：
[
  {{
    "word": "日文單字（原字）",
    "reading": "平假名讀音",
    "meaning": "繁體中文意思（簡短）",
    "example": "日文例句（自然口語）",
    "example_reading": "例句的完整平假名",
    "example_meaning": "例句繁體中文翻譯"
  }}
]

單字清單：
{word_list}"""

    try:
        text = call_gemini(model, prompt)
        items = extract_json_array(text)
        # 確保 word/reading 對得上（Gemini 有時會改字）
        for i, (word, reading) in enumerate(words):
            if i < len(items):
                items[i]["word"] = word
                items[i]["reading"] = reading
        return items
    except Exception as e:
        print(f"    ⚠ 批次失敗：{e}")
        return []


def generate_practice(model, vocab_items: list[dict], level: str) -> list[dict]:
    sample = vocab_items[:min(25, len(vocab_items))]
    word_list = "\n".join(
        f'{i+1}. {v["word"]}（{v["reading"]}）= {v["meaning"]}'
        for i, v in enumerate(sample)
    )
    prompt = f"""你是 JLPT 出題老師。根據以下 {level} 單字出 10 題四選一選擇題。

規則：
- 正確答案固定放在 options[0]（answer 固定是 0），我會自己打亂順序
- question 用日文出題（例：「○○」の意味はどれですか。）
- 三個錯誤選項要合理但不同（同詞性、相近難度的中文意思）
- explanation 用繁體中文簡短說明

必須嚴格回覆以下 JSON 陣列格式，不加任何說明：
[
  {{
    "type": "vocabulary",
    "question": "「單字」の意味はどれですか。",
    "options": ["正確答案", "錯誤1", "錯誤2", "錯誤3"],
    "answer": 0,
    "explanation": "繁體中文說明"
  }}
]

單字：
{word_list}"""

    try:
        text = call_gemini(model, prompt)
        items = extract_json_array(text)
        # 打亂選項並更新正確答案 index
        for item in items:
            opts = item.get("options", [])
            if len(opts) == 4:
                correct = opts[0]
                random.shuffle(opts)
                item["answer"] = opts.index(correct)
        return items
    except Exception as e:
        print(f"    ⚠ 練習題生成失敗：{e}")
        return []


def process_level(model, level: str, words: list[tuple[str, str]]) -> tuple[list, list]:
    words = words[:WORDS_PER_LEVEL]
    total_batches = (len(words) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"\n{level}：{len(words)} 個單字，{total_batches} 批次")

    vocab_items = []
    for i in range(0, len(words), BATCH_SIZE):
        batch = words[i:i + BATCH_SIZE]
        batch_no = i // BATCH_SIZE + 1
        print(f"  [{batch_no}/{total_batches}] 單字 {i+1}~{i+len(batch)}")
        result = generate_vocab_batch(model, batch, level)
        vocab_items.extend(result)
        time.sleep(SLEEP_BETWEEN_CALLS)

    print(f"  生成練習題...")
    practice_items = generate_practice(model, vocab_items, level)
    time.sleep(SLEEP_BETWEEN_CALLS)

    return vocab_items, practice_items


def main():
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    raw = download_vocab()
    groups = group_by_level(raw)

    for level in ["N5", "N4", "N3", "N2", "N1"]:
        new_vocab, new_practice = process_level(model, level, groups[level])

        json_path = DATA_DIR / f"{level.lower()}.json"
        existing = json.loads(json_path.read_text(encoding="utf-8"))

        existing["vocabulary"] = new_vocab
        existing["practice"] = new_practice

        json_path.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"  ✓ {level} 寫入 {len(new_vocab)} 單字 + {len(new_practice)} 練習題")

    print("\n完成！記得 git add . && git commit && git push")


if __name__ == "__main__":
    main()

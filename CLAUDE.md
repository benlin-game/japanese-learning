# 日本語學習網站 — 專案快速上手

## 專案概覽
靜態 SPA 日語學習網站，部署在 GitHub Pages。
- **Live URL**：https://benlin-game.github.io/japanese-learning/
- **Repo**：benlin-game/japanese-learning
- **本機預覽**：在 `docs/` 執行 `python -m http.server 8080`，開 `http://localhost:8080`

---

## 技術架構
- 純 HTML + Vanilla JS + Tailwind CSS CDN（無框架、無 build step）
- 資料：靜態 JSON，用 `fetch()` 載入（必須跑 HTTP server，不能直接開 file://）
- TTS：瀏覽器內建 Web Speech API（`speechSynthesis`，lang = `ja-JP`）
- 部署：GitHub Pages，serve 自 `/docs` 資料夾

---

## 檔案結構
```
japanese-learning/
├── docs/
│   ├── index.html          # 主程式（所有 UI + JS 都在這一個檔案）
│   └── data/
│       ├── n5.json
│       ├── n4.json
│       ├── n3.json
│       ├── n2.json
│       └── n1.json
├── expand_vocab.py         # 擴充單字（Bluskyo 資料集 + Gemini API）
├── expand_grammar_kanji.py # 擴充文法 / 漢字 / JLPT 練習題（Gemini API）
├── gemini_key.txt          # Gemini API Key（已加入 .gitignore，絕不 commit）
└── .gitignore
```

---

## JSON 資料結構
每個 `nx.json` 結構如下：
```json
{
  "vocabulary": [
    { "word": "日本語", "reading": "にほんご", "meaning": "日語",
      "example": "...", "example_reading": "...", "example_meaning": "..." }
  ],
  "grammar": [
    { "pattern": "〜ている", "meaning": "正在…", "example": "...",
      "example_meaning": "...", "notes": "..." }
  ],
  "kanji": [
    { "kanji": "山", "reading_on": "サン", "reading_kun": "やま",
      "meaning": "山", "examples": ["山（やま）山", "..."] }
  ],
  "practice": [
    { "type": "vocabulary", "question": "...", "options": ["A","B","C","D"],
      "answer": 0, "explanation": "..." }
  ]
}
```
各等級目標數量：文法 20+、漢字 20+、練習 20、單字 300

---

## 前端核心邏輯（index.html）

### State
```javascript
const state = {
  level, category, mode, data, cards, idx,
  flipped, correct, incorrect, quizAnswered,
  vocabOptions,   // 單字測驗的選項物件（含 word/reading/meaning）
  answeredIdx,    // Set：已計分的題目 index，防止來回重複計分
};
```

### 功能清單
| 功能 | 說明 |
|------|------|
| 等級切換 | N5～N1，切換自動重開 session |
| 類別切換 | 單字 / 文法 / 漢字 / JLPT練習 |
| 模式切換 | 字卡（翻牌）/ 測驗（四選一）|
| 隨機洗牌 | 每次 session 從 pool 隨機抽 50 題 |
| 上一張／上一題 | 可返回，`answeredIdx` 防止重複計分 |
| 語音播放 | 🔊 按鈕，Web Speech API，lang=ja-JP |

### 單字測驗特別邏輯
- 題目只顯示讀音（假名），附「查看漢字」按鈕點擊才展開
- 答題後四個選項都補上漢字（讀音）
- 選項建構用 `vocabOptions`（物件陣列）追蹤 word/reading

### 漢字測驗
- 題目：顯示漢字 + 中文意思
- 選項：平假名 / 片假名讀音（考讀音）

### 文法測驗
- 答題後 feedback 顯示例句 + 中文翻譯

---

## 擴充題庫腳本

### expand_vocab.py
- 下載 Bluskyo/JLPT_Vocabulary 單字資料集
- 用 Gemini API 補中文意思 + 例句
- 設定：`WORDS_PER_LEVEL = 300`，`BATCH_SIZE = 10`
- 只更新 `vocabulary` 和 `practice` 欄位

### expand_grammar_kanji.py
- 用 Gemini API 生成文法 / 漢字 / JLPT 練習題
- 設定：`GRAMMAR_COUNT = 20`，`KANJI_COUNT = 20`，`PRACTICE_COUNT = 20`
- 已達標的類別自動跳過（不重複生成）

### Gemini API Key
- 放在 `gemini_key.txt`（已 gitignore）
- 腳本內直接 hardcode key 字串（從 txt 讀取）
- 當前使用模型：`gemini-2.5-flash`

---

## 常見問題
- **沒聲音**：Windows 需安裝日語 TTS 語音包（設定 → 語音 → 新增語言 → 日本語）
- **fetch 失敗**：不能直接開 `index.html`，必須用 `python -m http.server 8080`
- **API key 過期**：換新 key 貼進 `gemini_key.txt` 並同步更新腳本內的字串

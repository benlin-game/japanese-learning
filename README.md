# 日本語學習 JLPT N5～N1

互動式日語學習網站，涵蓋 N5 到 N1 的單字、文法、漢字與 JLPT 題型練習。

## 功能

| 功能 | 說明 |
|---|---|
| 等級切換 | N5 / N4 / N3 / N2 / N1 |
| 學習類型 | 單字（含假名）、文法句型、漢字、JLPT 題型練習 |
| 單字卡模式 | 翻牌顯示讀音＋意思＋例句，標記知道 / 不知道 |
| 測驗模式 | 四選一選擇題，即時回饋與解說 |
| 隨機順序 | 打亂題目順序 |
| 結果統計 | 完成後顯示正確率 |

## 部署（GitHub Pages）

1. Push 到 GitHub
2. Settings → Pages → Source：`main` 分支 `/docs` 資料夾
3. 約 1 分鐘後生效

## 本地預覽

任意 HTTP server 皆可，例如：

```bash
cd docs
python -m http.server 8080
```

開啟 `http://localhost:8080`

## 新增內容

編輯 `docs/data/n5.json`（或其他等級），在對應陣列新增項目即可：

- `vocabulary`：單字
- `grammar`：文法句型
- `kanji`：漢字
- `practice`：JLPT 練習題

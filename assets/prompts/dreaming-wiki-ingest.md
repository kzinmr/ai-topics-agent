# Dreaming Wiki Ingest — Nightly Knowledge Consolidation (品質向上版)

## 品質要件 (Gwern Inspired)

このナイトリーレポートには [[concepts/llm-creative-writing]] の以下技法を適用せよ：

### T1: Anti-Examples
自己レビュー：AIらしい汎用表現を特定し逆転換。「これは〜を示唆している」「注目すべき」などの定型句を削除。

### T3: Atomic Snippets
```
**一言要約**: 15-30トークン
**詳細**: 箇条書きで深掘り
```

### T4: Generate-Rank-Select
最も重要な発見（top 1-2）は、2-3バージョン生成して最良を選択せよ。

### T5: Engram Pathways
統合前にwikiの既存ページ（concepts, entities）を検索し、新しい発見を既存知識と結び付けよ。各トピックに最低2つのwikilink。

## 入力
Pre-run scriptがグループ化されたテーマJSONを提供。各テーマを評価し、スコア高いものからwikiページ作成/更新せよ。

## 配信先
Discord: #hermes-topic-manager

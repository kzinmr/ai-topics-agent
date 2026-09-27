Run the hierarchy candidate detection script and present the results as a structured report.

Steps:
1. Run: `cd ~/ai-topics && python3 ~/.hermes/scripts/detect_hierarchy_candidates.py`
2. Read the output JSON from `~/.hermes/scripts/cache/hierarchy_report.json`
3. Present the results in Japanese as a concise report with:
   - 現在のフラットページ総数とサブディレクトリ数
   - 検出されたクラスタ（prefix / tag / link-cluster ごとに上位5件）
   - 階層化推奨（recommendations）を優先度付きで表示
   - 各推奨に対して、提案ディレクトリ名、対象ページ数、具体例3-5件
   - 判断が必要な ambiguous なケース（例: agent-* と agentic-* を統合すべきか）

Keep the report concise and actionable.

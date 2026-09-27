# 現行 Lucy の調査結果（2026-09-27）

調査対象は実行中 profile、ai-topics working tree、ホストの wrapper/compose/runbook、Hermes CLI/scheduler の実装。秘密ファイルの値は成果物に含めません。

## 実際の構成

- content source commit: `70068426828c4f690c3a5ae73ce33dfeea205a48`。working tree に未 commit の Wiki/skill 変更があり、これを削除・reset せず調査しました。
- 稼働 cron は30件、repository の jobs.json は28件。朝の6段階の時刻、hot-post の prompt/時刻、手動 backlog の停止状態などに drift。SSOT は live job の意図を抽出した本 repository の manifest に統一。
- Wiki Markdown 13,969ファイルを観測。収集 → immutable raw → triage → L2 synthesis → index/log/hooks という流れ。
- RSS は blogwatcher v0.0.2 の SQLite。X は xurl v1.1.0 + OAuth + processed IDs/cache。newsletter は Gmail IMAP unseen と Message-ID の二重 dedup。sitemap は sourceごとの processed URL。
- 同一 `.hermes/cron/output/<job-id>` の Markdown から次段が JSON を抽出する実装。cron の状態と job 定義が1ファイルに混在。
- 現 user の host crontab に実行行はありません。Docker gateway/native cron が主たる定期入口。wrapper 外の直接実行では ownership を壊す問題があり、入口統一を維持。
- Compose に個別の provider key、LAN endpoint、固定 UID、runtime paths が含まれるため、そのまま成果物へコピーせず、新しい配備設定と秘密設定へ分離。
- optional plugin は observability / achievements。gateway sessions、memory、kanban、browser caches は自動 Wiki の処理再開に必須ではありません。

## Script drift

| script | live vs Git working tree |
|---|---|
| check_new_skills.py | different |
| tag_audit.py | broken symlink |
| wiki_health.py | different |

live wiki_health.py は古く、--json の実装がありませんでした。新しい Git 版の JSON と命名検査を取り込み、canonical path と失敗伝播を修正。JSON 生成時に全 raw × L2 全文の不要な検索をしないよう変更しました。

## 修正した実行上の問題

- tag_audit.py の切れた profile symlink を実体 script として deploy。
- backlog の `cron.scheduler.run_job` 直接 import と固定 Hermes install path を廃止。通常の job として manual run。
- 三つの triage の response に COST_REPORT が混ざると JSON parse に失敗するため、構造化 response と実測 usage を別に保存。
- 失敗した collector が exit 0 + ok:false を返しても次の model を起動しない。
- RSS scrape に失敗した article は既読にしない。RSS total の二重カウントも修正。
- sitemap の取得上限外・取得失敗 URL を processed にしない。
- newsletter 0件でも空の新 checkpoint を保存。BODY.PEEK と COPY 成功確認を使用。
- raw article 再取得で既存 raw を上書きしない。
- 停止中 job を watchdog の異常に含めない。X account の2日起点 step に適した鮮度猶予。
- code/skill/prompt/SOUL の旧 path 修復手順は再評価。古い directory cleanup を canonical path へ単純置換せず廃止。
- skill helper に Python の拡張子で保存されていた Markdown があり、実行可能なコードに整理。
- API/model endpoint、配送先、認証、binary の場所は destination の設定として分離。

## 全ジョブ

時刻は UTC。false の job を勝手に再有効化しません。

| job | cron | enabled | script | dependencies |
|---|---|---|---|---|
| blog-triage | `20 10 * * *` | true | blog_checkpoint.py | blog-ingest |
| blog-wiki-ingest | `40 10 * * *` | true | blog_triage_checkpoint.py | blog-triage |
| blog-ingest | `0 10 * * *` | true | blog_ingest.py | — |
| check-skill-inventory | `0 16 * * 0` | true | check_new_skills.py | — |
| weekly-ai-digest | `0 0 * * 1` | true | agent only | — |
| dreaming-collect | `0 18 * * *` | true | dreaming_collect.py | — |
| dreaming-group | `10 18 * * *` | true | dreaming_checkpoint.py | dreaming-collect |
| dreaming-wiki-ingest | `20 18 * * *` | true | dreaming_group_checkpoint.py | dreaming-group |
| trending-topics | `0 12 * * *` | true | agent only | — |
| wiki-graph-analysis | `0 15 * * 5` | true | agent only | — |
| wiki-health | `0 17 * * *` | false | agent only | — |
| newsletter-ingest | `10 10 * * *` | true | process_email.py | — |
| newsletter-triage | `30 10 * * *` | true | newsletter_checkpoint.py | newsletter-ingest |
| newsletter-wiki-ingest | `50 10 * * *` | true | newsletter_triage_checkpoint.py | newsletter-triage |
| x-bookmarks-ingest | `30 11,23 * * *` | true | fetch_x_bookmarks.py | — |
| x-accounts-scan | `30 22 */2 * *` | true | fetch_x_accounts.py | — |
| skeleton-enrich-daily | `0 19 * * *` | true | agent only | — |
| wiki-health-plan | `10 17 * * *` | false | wiki_health.py | — |
| wiki-health-fix | `50 17 * * *` | true | wiki_health_json.py | — |
| ai-topics-slack-hot-posts | `30 0,12,18 * * *` | true | ai_topics_slack_hot_posts_context.py | — |
| active-crawl | `0 11 * * *` | true | agent only | — |
| sitemap-monitor | `0 6 * * *` | true | sitemap_monitor.py | — |
| tag-audit-weekly | `0 10 * * 1` | true | tag_audit.py | — |
| pipeline-watchdog | `0 0,6,12,18 * * *` | true | pipeline_watchdog.py | — |
| wiki-watchdog-fix | `35 17 * * *` | true | wiki_watchdog_fix_context.py | — |
| raw-backlog-ingest | `0 0,4,10,14,18,22 * * *` | false | raw_backlog_collect_cron.sh | — |
| jp-to-en-translation | `0 0 * * 0` | true | agent only | — |
| skill-drift-check | `0 10 * * 1` | true | agent only | — |
| llm-pricing-monitor | `0 10 * * 1` | true | agent only | — |
| hierarchy-candidate-detection | `0 15 * * 3` | true | agent only | — |

原本の file hash と抽出範囲は [source-inventory.json](source-inventory.json)。全個人 skill を vendor するのではなく、job が参照する14 skill と9 companion skill、その resources を抽出しています。

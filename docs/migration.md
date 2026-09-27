# Lucy migration / rollback

## Preconditions

本 repository を新ホストへ clone し、依存・harness・source tools をインストールします。
この作業で既存 Lucy の gateway / cron は切り替えていません。移行先は必ず別 profile。
Git 管理版だけでは実際の schedule/state を再現できないため、下記 snapshot を使います。

snapshot は認証を含みません。移すもの:

- `.hermes/processed_*.json`（メール、X、sitemap、raw の重複排除）
- `.hermes/cron/data`（triage/latest、archive、X cursor/cache）
- `.hermes/cron/output`（段階間の既存 `## Response` 互換出力）
- `.hermes/scripts/cache`、`.blogwatcher/blogwatcher.db`
- 新 runner の ledger/run/outbox（新構成間の移動の場合）
- `--include-content` 指定時は ai-topics working tree のファイル。`.git`、認証、生成 AGENTS.md は除外。

移さないもの:

- `.env`, `.git-credentials`, `.netrc`, `.xurl`, auth.json、provider credential pool、pi/Codex 認証
- Hermes config 全体、native cron の実行予約、sessions / gateway locks / PID
- venv、ホスト用 ELF binaries、cache、browser cookies、logs、optional plugin state

認証情報は secret manager 等で別途 provision。X OAuth は destination の xurl auth store を設定。
Git は destination profile の専用 credential helper / SSH 設定を使用。端末操作者の HOME に偶然あった認証を前提にしません。

## 1. リハーサル

以下は repository root で実行。source path は引数として明示し、運用 prompt に埋め込みません。

```sh
export AI_TOPICS_PYTHON="$PWD/.venv/bin/python"
# source profile の実体パスを指定
bin/ai-topics-agent --profile "$SOURCE_PROFILE" snapshot "$PWD/backups/lucy-rehearsal.tar.gz" --include-content
bin/ai-topics-agent --profile "$DEST_PROFILE" init --clone
bin/ai-topics-agent --profile "$DEST_PROFILE" restore "$PWD/backups/lucy-rehearsal.tar.gz" --rehearsal
bin/ai-topics-agent --profile "$DEST_PROFILE" doctor
bin/ai-topics-agent --profile "$DEST_PROFILE" run blog-wiki-ingest --dry-run
```

`SOURCE_PROFILE` / `DEST_PROFILE` は運用者が選んだ別 directory。両方を先に shell 変数として設定します。
`--rehearsal` は稼働中 source の snapshot に対する明示指定。SQLite は online backup API により WAL の committed transaction を含めますが、複数 JSON/Wiki ファイルの同一時点整合性は保証しません。

destination の `local.json` / `secrets.json` と harness のモデル設定を記入。まず outbox のまま、隔離した content clone で検証します。任意の model smoke test でも元 Wiki に push しないよう、rehearsal repository の push URL を検証用 repository に設定するか無効にします。

```sh
# Rehearsal では公開前に push を遮断
 git -C "$DEST_PROFILE/ai-topics" remote set-url --push origin DISABLED_FOR_REHEARSAL
```

## 2. 本切替

1. 旧ホストの **Lucy の writer のみ** を止めます。旧 deploy root で `docker compose stop hermes-lucy`。Nana や共有 LLM proxy は停止対象ではありません。host runtime は該当 user service を止めます。進行中の Wiki 編集も完了させます。
2. `git status` を確認。未 commit の追加・変更は `--include-content` で捕捉します。追跡済みファイルの未 commit の削除も manifest に記録し、destination clone に反映します。切替前に `git diff` を照合してください。旧 profile はそのまま保管。
3. 全 writer 停止を確認して `snapshot ... --quiesced --include-content`。この flag は停止確認の operator assertion で、自動停止はしません。
4. リハーサルとは別の空 profile に `init --clone` → `restore <bundle>`。checksums、archive path、特別ファイル、許可対象、size limit を検査後に復元します。既存 runtime state の上書きは拒否。
5. 秘密設定・認証を provision、Git の push destination、モデル endpoint、delivery route を確認。endpoint が旧 Docker DNS/LAN を指していれば新ホストの値に置き換える。
6. `doctor` を確認。`status` には旧実行の成功/失敗を引き継ぎます。古い失敗を成功に変えません。
7. 必要なら `run blog-ingest` → `run blog-triage` → `run blog-wiki-ingest` のように上流から再開。既存 source dedup/processed state を引き継ぐため全データを再収集しません。
8. Wiki diff と checkpoint を確認し、新 scheduler **ひとつだけ** を起動。旧 gateway/native cron は引き続き停止。新 profile の native jobs.json は空です。

restore は旧 profile root と旧 container root を構造化 JSON の **path値** に限って移し替えます。URL・記事本文・原文は書き換えません。JSON を含む旧 cron response も移し替え、mtime を維持します。過去の自由文ログに残る旧パスは証跡として残し、現在の操作には使いません。

## 3. Rollback

新 scheduler を止め、旧ホストを再開する前に、新稼働中に増えた Wiki と source state を確認してください。

- 本切替前または新環境が読み取り検証のみ: 旧 Lucy を再開すれば元の状態に戻せます。
- 新環境が既にメール取得/内容編集/配信を行った: Wiki commits を旧 content clone に反映し、新 snapshot の dedup/checkpoint/RSS DB を空の復旧 profile に戻して旧 harness で起動する方法を推奨。旧 profile に state を無条件上書きしない。
- 通知は取り消されません。配信の run ID と outbox を照合して重複を避けます。

旧、新の2つの scheduler を同じ Wiki に同時接続しないこと。Hermes の native scheduler へ戻す場合は、新 runner の schedule claim と互換性がないため、旧 definitions と次回予定時刻の再設定が必要です。新 runner の harness だけ Hermes に戻すほうが状態を維持できます。

## 定常運用

- 更新: Git pull → tests → `sync-assets`。local drift を自動上書きしない。
- 手動 backlog: `RAW_BACKLOG_COUNT=10 bin/ai-topics-agent run raw-backlog-ingest`。disabled は定時実行の設定で、手動 run は可能。まず `RAW_BACKLOG_DRY_RUN=1 bin/ai-topics-agent exec bash "$HERMES_PROFILE_ROOT/.hermes/scripts/raw_backlog_collect_cron.sh"` で選択を確認。
- 実行中断: `status` → run artifacts を確認 → `recover <run-id>` →必要な job を手動 run。
- 配信再試行: `outbox --deliver`。Wiki job は再実行しない。
- 長期停止: catch-up 上限超過は停止。失った時間帯を調べ、手動実行または `reset-cursor` を選ぶ。
- バックアップ: writer 停止後 snapshot。秘密設定の backup は別系統。

# 検証記録（2026-09-27）

## Automated tests

`PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v`

**30 tests passed**（98.675秒）。対象:

- 30-job manifest / path / schedule の検証、UTC cron day OR/step semantics
- profile writer lock、同一 tick の重複排除、disabled native scheduler の検査
- no_agent / wakeAgent=false / empty output、script exit failure、JSON ok:false
- JSON response、実際の既存 blog_triage_checkpoint.py への `## Response` handoff
- 古い dependency の拒否、managed-asset drift の保護
- Hermes wrapper の HOME/引数転送（空白を含む path）
- pi/Codex プロトコルの完了・拒否・失敗・EOF・対話要求・timeout（独立した fake process）
- 配信失敗と Wiki 成功の分離、秘密値の redaction、親 harness 設定の非継承
- SQLite WAL の committed data、別 path への checkpoint relocation、秘密設定の除外
- rehearsal の明示指定、restore 上書き防止、archive traversal 拒否、追跡済み削除の保存
- RSS 未取得 article の未読保持、sitemap の未取得 URL の未処理保持、raw 不変性
- newsletter 0件時の checkpoint 更新、health JSON が不要な全文走査をしないこと

全 Python assets を compileall。job validation、skill local reference 0件欠落、公開ツリーの秘密値/path scan 0件。
CI に同じ検査を配置しています。

## Real-data rehearsal

本番の live profile は読み取りのみ。非公開 `.local/` に snapshot と復元先を作成しました。
稼働中 source なので snapshot の consistency は **rehearsal**。cutover に使える一貫 snapshot と主張しません。

| 検査 | 結果 |
|---|---|
| snapshot → 空の destination profile へ restore | 21,412ファイル復元成功 |
| Wiki health JSON | 有効な構造化出力、実測2.110秒 |
| health の L2 範囲 | entities 935 / concepts 2,101 / comparisons 35 = 3,071 |
| raw/articles | 9,945 |
| blog checkpoint | 19候補、19件すべて移行先の raw が存在 |
| newsletter checkpoint | 100候補、100件すべて移行先の raw が存在 |

旧 live health script は --json を無視して Markdown を出したため、最初の JSON 検証は失敗。
新しい repository 版を取り込み、JSON branch と時間のかかる Markdown scan を分離した後に再検証しています。

## Runtime / deployment

- Codex CLI 0.157.1 のローカル JSON schema と実装フィールドを照合。
- 実際の Codex app server の initialize 成功（host / container）。モデル呼び出しなし。
- 実際の pi 0.87.1 の RPC get_state 成功（container）。モデル呼び出しなし。
- pi/Codex image と Hermes image の両方をビルド成功。
- 両 image を network none / UID:GID 1000:1000 / tmpfs profile で起動し、init と30-job validate に成功。
- Hermes variant で `bin/hermes-lucy` → oneshot 対応 CLI の help 起動を確認。
- Compose の標準版 / Hermes override と、生成した systemd user service を構文検証。

Docker の一度目の再ビルドでは既存 build cache の parent snapshot 不整合が発生。
他の image/cache を削除せず、新しい tag と no-cache build で成功を確認しました。
Hermes base の venv に pip がなかったため、runner を別 uv venv に分離し、Hermes 自身の依存を変更しない形でビルドしました。

## 未実施の acceptance

モデル認証を使った本番記事生成、IMAP/X の live 取得、Discord/Telegram 送信、Git content push はこの検証で実行していません。実データを使ったのは復元・path・read-only collectors の検証です。モデルによる記事品質、service quota、provider 固有設定は destination の認証設定後に隔離 Wiki と outbox で確認してください。

本番 Lucy の scheduler 切替と Nana への適用は行っていません。新しいコード・運用定義・migration 手順の成果物はこの repository に完結しています。リハーサル snapshot、実行ログ、認証、Wiki 内容は Git に含めません。

# Harness migration

| 機能 | Hermes | pi | Codex app server | 所有者 |
|---|---|---|---|---|
| schedule / no_agent / dependencies | 共通 | 共通 | 共通 | runner |
| pre-run script / HOME | 共通 | 共通 | 共通 | runner |
| skill preload | Markdown 注入 | Markdown 注入 | Markdown 注入 | assets + runner |
| shell/file/edit | 組み込み tool | 組み込み tool | 組み込み tool | harness |
| 検索/取得 | native web または CLI | wiki-search / fetch CLI | native web または CLI | optional integration |
| delegated subagent | 任意 | 逐次代替 | 任意 | optimization |
| checkpoint / job output / usage | 共通 | 共通 | 共通 | runner |
| Discord/Telegram delivery | 共通 outbox | 共通 outbox | 共通 outbox | runner + delivery command |
| gateway / session / memory / model fallback | 独自機能 | 独自設定 | 独自設定 | harness に残す |
| observability | 任意 plugin | 任意 integration | 任意 integration | run artifacts が共通の基礎 |

## Hermes

元環境の CLI は v0.15.1、image revision `79f7e7a1e9d83ecc75144ddfb1406c2037c9e476`。
実機 `--help` の `--oneshot`（最終回答のみ stdout）を使用します。呼び出しは必ず
`bin/hermes-lucy` → `bin/hermes-profile` を経由。旧 `cron.scheduler.run_job` import は不要です。
独立 runner の子として同じ container/host 内で動かすため adapter は host mode。
外側からの手動 profile 操作は Docker を既定とする wrapper を使用します。

Provider/base URL/fallback/tools は destination の `~/.hermes/config.yaml` と認証で設定。
既存 gateway を一緒に使う場合も native cron は無効化し、Wiki の同時編集を避けます。
Hermes oneshot の権限は CLI 自体の動作に従うため、専用 profile/container で運用します。

## pi

`pi --mode rpc --no-session` に JSONL `prompt` を送り、`response` の成功を確認して
`agent_settled` まで読む実装です。`agent_end` の後にも retry がありうるため、そこで成功と判定しません。
stdout と stderr を別々に読み、期限切れ・途中終了・対話 UI 要求をエラーにします。
[上流 RPC 仕様](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/rpc.md) に基づきます。

Container は `@earendil-works/pi-coding-agent@0.87.1` を固定。
provider/model は local.json の command argv に `--provider` / `--model` を追加。
provider key は secrets.json、subscription auth は destination の pi auth store に設定します。
pi 自体は sandbox 境界ではないため、必要なら container/OS による隔離を利用します。

## Codex app server

`codex app-server` に `initialize` / `initialized`、`thread/start`、`turn/start` を送り、
`item/completed` の回答と `turn/completed` の成功を確認します。workspaceWrite の writable roots を
profile に設定。無人実行で解決できない server request は拒否して失敗にします。
[公式 app-server 仕様](https://developers.openai.com/codex/app-server/) と、実機
`codex-cli 0.157.1` の `generate-json-schema` を照合しました。

Container の Codex は 0.157.1 固定。destination profile の `~/.codex` に認証/config を設定。
`CODEX_HOME` を使う場合は別の専用認証領域を明示し、操作者の個人設定を無意識に継承しないでください。
`local.json` の adapter に model を指定可能。モデル名をこの repository の共通定義に埋め込みません。

## 切替の手順

1. 同じ復元済み profile の state/Wiki を維持し、scheduler を止める。
2. destination harness と source tool の認証・検索 capability を設定。
3. local.json の `harness` と adapter を変更。元 local.json は非公開にバックアップ。
4. `doctor --job <name>`、`run <name> --dry-run`。まず隔離 Wiki/ローカル outbox で代表1ジョブを実行。
5. 内容・差分・checkpoint の成功を確認し、schedule を再開。

模型応答・tool選択・要約品質はハーネスやモデルによって変わります。プロトコル互換と生成内容の同等品質は別の検証です。認証を伴う実ジョブの acceptance は destination のモデル・取得先で行ってください。既存会話履歴を別ハーネスの session として変換するものではありません。

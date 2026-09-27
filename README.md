# ai-topics-agent

Lucy の AI 情報収集・LLM Wiki 運用を、ホストとエージェントハーネスから分離した実行基盤です。
Wiki 本体・原文・feed 定義は [ai-topics](https://github.com/kzinmr/ai-topics)、運用コード・ジョブ・prompt・skill・配備手順はこの repository が管理します。Nana は対象外です。

- 現行 Lucy の **30ジョブ（有効27・停止3）** を `config/jobs.json` に移行。UTC 時刻と停止状態を保持。
- **Hermes / pi RPC / Codex app server** のアダプターを実装。同じ collector・prompt・checkpoint・scheduler を使用。
- profile 単位の書き込みロック、永続的な定時実行 claim、依存段階の成功・鮮度チェック、timeout、実行履歴、独立した配信 outbox。
- host / Docker 用 wrapper、依存 lock、初期化、drift 検出、認証情報を除いた snapshot / restore。
- Hermes の内部 Python API に依存しません。既存 `.hermes/cron/data` 等は **ディスク形式の互換性** として維持しています。

全体像と既存実装の問題は [調査結果](docs/audit.md)、契約は [設計](docs/architecture.md)、切替は [移行手順](docs/migration.md)、各ハーネスの依存は [対応表](docs/harnesses.md)、実施済み検証は [検証記録](docs/validation.md) を参照してください。

## 最初に試す

Linux / WSL、Python 3.12 以上、Git が必要です。host と同じ profile を使い、POSIX flock に対応するローカル filesystem 上で実行します。Windows は WSL / Docker を利用してください。

```sh
git clone https://github.com/kzinmr/ai-topics-agent.git
cd ai-topics-agent
uv sync --frozen --extra collectors
export AI_TOPICS_PYTHON="$PWD/.venv/bin/python"
export HERMES_PROFILE_ROOT="$PWD/profiles/lucy"
bin/ai-topics-agent validate
bin/ai-topics-agent init --clone
bin/ai-topics-agent run blog-triage --dry-run
```

`uv` を使わない場合:

```sh
python3 -m venv .venv
.venv/bin/pip install --require-hashes -r requirements.lock
.venv/bin/pip install --no-deps -e .
```

`init` は既存の Hermes profile への上書きを拒否します。既存データを移す場合は [移行手順](docs/migration.md) の新規 profile を使用します。`--clone` なしでは空の作業領域だけ作るため、実運用には Wiki の clone/restore が必要です。

## 設定と起動

1. `profiles/lucy/.ai-topics-agent/local.json` で harness を選びます。初期値は Hermes。`config/{local,codex,pi}.example.json` が例です。
2. 必要な値を `config/secrets.example.json` から profile の `.ai-topics-agent/secrets.json` に記入し、`chmod 600` にします。認証情報は Git に入れません。
3. RSS / X を使う場合は Go を用意し、`tools/install-source-tools` で target OS/architecture 向けに固定版をビルド。新規 RSS DB には `bin/ai-topics-agent exec python3 "$HERMES_PROFILE_ROOT/.hermes/scripts/import_opml.py"` を実行します。既存 DB の restore 時は再登録不要です。
4. モデルと Git の認証を destination profile に設定します。`doctor` は設定の存在を検査し、認証成功は実際の接続で確認します。
5. `bin/ai-topics-agent doctor`、対象ジョブの `run ... --dry-run` を確認後、必要なジョブを `run <name>`、常時実行を `serve` で開始します。

```sh
# Hermes の操作は必ず repository wrapper 経由
HERMES_RUNTIME=host bin/hermes-lucy --help
HERMES_RUNTIME=host bin/hermes-lucy setup

# 本文の処理とは独立した配信 queue（初期設定はローカル保存）
bin/ai-topics-agent outbox
bin/ai-topics-agent status
```

配信を有効にする場合は `local.json` の route に
`{"kind":"command","command":["wiki-deliver"]}` を設定します。`operations` と `hot-posts` は Discord、`digest` は Telegram。宛先・token は秘密設定に置きます。配信失敗だけを再試行するコマンドは `outbox --deliver` です。例の送信先は空です。

## 配備

Docker の初期化・認証・profile mount と、systemd user service の生成は [配備手順](docs/deployment.md) を参照してください。独自ネットワーク、Cloudflare Tunnel、特定 LLM proxy は必須ではありません。

## 開発・検証

```sh
uv run --frozen --extra collectors python -m unittest discover -s tests -v
uv run --frozen python -m compileall -q src assets tools
bin/ai-topics-agent validate
python3 tools/check-public-tree.py
```

`assets/` は Lucy から抽出後に refactor した運用資産です。元ファイルの hash は `docs/source-inventory.json` に記録。`tools/extract_lucy.py` は再調査用の片方向 exporter で、出力は別の空ディレクトリに取りレビューします。現在の assets を上書きして再生成する用途ではありません。

変更を profile に反映する際は `sync-assets` を実行します。profile 上で編集された管理対象ファイルがあれば上書きを拒否します。Wiki の `AGENTS.md` は新しい運用契約に置き換え、clone 時の旧版を profile の非公開 state に保存します。

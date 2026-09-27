# Deployment

## Host

Linux/WSL + Python 3.12+。`uv sync --frozen --extra collectors` または README の hash-locked pip 手順。
Go 1.26.2 は固定版 source tools のビルド時のみ必要。`tools/install-source-tools` は
blogwatcher v0.0.2 / xurl v1.1.0 を destination architecture 向けに作ります。

Codex/pi を使う場合は Node 24 と、それぞれ固定版をインストール:

```sh
npm install -g @openai/codex@0.157.1
npm install -g @earendil-works/pi-coding-agent@0.87.1
```

Hermes は対応する oneshot CLI をインストールし、local.json の `adapters.hermes.executable` に設定。
既存 image と同じ版を使う場合は後述の Hermes Docker variant が source provenance を固定します。
Provider、fallback、検索、認証は destination profile の設定。暗黙の host gateway/proxy を必要としません。

user service の例（生成後に自分で配置・起動）:

```sh
tools/render-systemd --profile "$HERMES_PROFILE_ROOT" --python "$PWD/.venv/bin/python" > /tmp/ai-topics-lucy.service
systemd-analyze verify /tmp/ai-topics-lucy.service
mkdir -p ~/.config/systemd/user
cp /tmp/ai-topics-lucy.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now ai-topics-lucy.service
```

unit のパスは render 時の実パス。別ホストで再生成します。logout 後も動かす場合の user lingering はホスト管理者が設定。古い cron と並走させません。

## Docker: pi / Codex

base image digest、Go modules、Python hash lock、harness version を固定しています。

```sh
export LUCY_PROFILE_DIR="$PWD/profiles/lucy"
export AGENT_UID="$(id -u)"
export AGENT_GID="$(id -g)"
mkdir -p "$LUCY_PROFILE_DIR"
docker compose -f deploy/compose.yaml build
# init だけ実行。scheduler はまだ開始しない。
docker compose -f deploy/compose.yaml run --rm lucy init --clone
cp config/codex.example.json "$LUCY_PROFILE_DIR/.ai-topics-agent/local.json"
# pi の場合は config/pi.example.json を使用。
```

認証や RSS DB 登録は一時 container の `exec` サブコマンドで行えます。これは runner が profile 環境を与える操作であり、外部からの直接 `docker exec ... hermes ...` は使いません。

```sh
docker compose -f deploy/compose.yaml run --rm lucy exec codex login
# or: docker compose -f deploy/compose.yaml run --rm lucy exec pi
# secrets.json / Git / X auth / RSS feed registration を設定した後:
docker compose -f deploy/compose.yaml run --rm lucy doctor
docker compose -f deploy/compose.yaml up -d
```

Compose は既存 Lucy/Nana の container 名・network・volume に接続しません。
UID/GID は host directory の所有者を指定。起動時の再帰 chown は行いません。
同一の host profile を異なる runtime で使うときは、稼働中 scheduler を止めてから切替えます。
source scripts は canonical path を使い、restore は他ホストから来た checkpoint 内の path値を変換します。

**既に host で生成済みの絶対パス checkpoint を同じ profile のまま Docker に mount する場合**も、snapshot を別の新 profile に restore する方式で runtime path を再配置してください。単純な mount 切替だけでは checkpoint の path値は更新されません。Docker 内で restore を実行すると destination の container path に変換されます。

## Docker: Hermes

```sh
docker compose -f deploy/compose.yaml -f deploy/compose.hermes.yaml build
# init / restore / doctor も同じ2つの -f を付ける
```

ローカルに存在する公開 upstream image の digest を base に固定し、独立 runner を entrypoint にしています。
Hermes gateway/s6 を scheduler として起動しません。Hermes は runner の子として oneshot 実行します。
外部から Hermes CLI を実行する際は:

```sh
export HERMES_DOCKER_CONTAINER=ai-topics-agent-lucy
bin/hermes-lucy config check
```

この variant でのモデル setup は同じ wrapper、または host mode の wrapper を container 内から使用。
Hermes-specific config は profile に残り、Wiki ロジックと別に更新できます。

## Optional services

旧環境の serial LLM gate は特定 backend の同時推論制限のためのものです。新 runner は Wiki writer を直列化しますが、他アプリも同じ backend を使うなら proxy/queue は依然として別途必要です。
Cloudflare Tunnel、dashboard、messaging gateway、Camofox/agent-browser、o11y plugin、Replicate proxy は optional。必要な場合だけ別 service とし、接続先を local config/environment に設定します。

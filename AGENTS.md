# Development contract

This repository owns Lucy's operational code; ai-topics owns content and source
selection. Keep runtime assumptions out of assets. Canonical paths are ~/wiki
and ~/.hermes/scripts. Profile HOME is set only by the runner/wrappers. All
Hermes commands must go through bin/hermes-lucy or bin/hermes-profile.

Do not import Hermes modules into src/ai_topics_agent. Keep scheduling, state,
delivery and source collection independent of harness transports. Do not replace
state migrations with wholesale profile copies; credentials, binaries and native
scheduler state have separate lifecycles.

Validate changes with the unittest suite, compileall, validate, check-skill-links
and check-public-tree. Use temporary profiles for tests. Never run collectors or
notification transports against production as an incidental test. Do not stage
.local, profiles, backups, credentials or generated run output.

When changing the path contract, update wrappers, deployment, prompts, skills,
SOUL and migration documentation together. Asset changes deploy with sync-assets;
local drift must be reconciled explicitly. Keep Nana unchanged until a separate
migration is requested.

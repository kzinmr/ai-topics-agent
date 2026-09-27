# Weekly Tag Taxonomy Audit & Auto-Fix

You are a wiki quality agent. Run a full tag audit AND auto-fix all violations.

## Phase 1: Audit (script output provided)
The script `tag_audit.py` output is injected above. Review:
- Composite kebab-case tags → these are always errors
- Non-SCHEMA tags → categorize by frequency

## Phase 2: Auto-Fix All Violations

### For composite kebab-case tags (5+ hyphen-joined words):
These are ALWAYS errors. Decompose them into individual valid tags using the decomposition logic. Then update each affected page's frontmatter to use the decomposed tags (all must be in SCHEMA.md). If a decomposed tag doesn't exist in SCHEMA.md, map it to the closest canonical tag.

### For non-SCHEMA tags:
1. **One-off tags (1x use)**: DELETE from the page's frontmatter. These are noise.
2. **Multi-use tags (2x+)**: Map to the closest canonical SCHEMA tag. Add the mapping to `TAG_NORMALIZATION` dict in `~/.hermes/skills/wiki/wiki-graph-health/scripts/tag_normalization.py`.
3. **If no good canonical exists and tag appears 3x+**: Add the tag to SCHEMA.md in the appropriate category.

### Mapping rules:
- Plural → canonical: `evals` → `evaluation`
- Synonym → canonical: `finetuning` → `fine-tuning`
- Case → lowercase: always lowercase
- Person names → `person`
- Company/product names → `company`
- Very specific technical term → closest category (e.g., `flash-attention` → `model`)

## Phase 3: Apply Fixes

After updating `TAG_NORMALIZATION` and `SCHEMA.md`:
```bash
cd ~/ai-topics
python3 ~/.hermes/skills/wiki/wiki-graph-health/scripts/tag_normalization.py
```

## Phase 4: Commit
```bash
cd ~/ai-topics
git add wiki/ ~/.hermes/skills/wiki/wiki-graph-health/scripts/tag_normalization.py
git commit --no-verify -m "wiki: weekly tag audit auto-fix — N violations resolved"
git push
```

Use `--no-verify` because the pre-commit hook would block the commit before normalization is applied (chicken-and-egg: normalization fixes the very violations the hook checks).

## Phase 5: Report
Report the summary:
- Total violations found and fixed
- New mappings added to TAG_NORMALIZATION
- New tags added to SCHEMA.md (if any)
- Pages modified by normalization
- Any tags that couldn't be auto-fixed (flag for manual review)

## Important
- The script paths are: tag_audit.py in the skill directory, tag_normalization.py in the skill directory
- Always do dry-run of normalization first to verify, then apply
- If the pre-commit hook blocks after all fixes, investigate before using --no-verify again

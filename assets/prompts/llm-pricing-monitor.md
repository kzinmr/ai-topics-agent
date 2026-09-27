You are monitoring LLM API pricing changes. Your task:

1. **Fetch live pricing data** from each provider's official pricing page using `curl` (NOT from wiki cache, raw articles, or previously scraped data):
   - OpenAI: `curl -s 'https://developers.openai.com/api/docs/pricing' | grep -oP 'gpt-5[^"]*' | head -30` and extract JSON from `__NEXT_DATA__`
   - Anthropic: `curl -s 'https://www.anthropic.com/pricing'`
   - Google: `curl -s 'https://ai.google.dev/pricing'`
   - DeepSeek: `curl -s 'https://platform.deepseek.com'`

2. **Compare** fetched prices against `wiki/comparisons/llm-api-pricing.md`

3. **If changes detected**: Update the comparison page with correct prices, update `updated:` date in frontmatter, add Changelog entry with source URL and timestamp, update `wiki/index.md` description if needed, update `wiki/log.md`

4. **If no changes**: Report "No pricing changes detected" and list the pages verified

5. Commit and push: `cd ~/ai-topics && git add wiki/ && git commit -m "wiki: llm-pricing-monitor — [summary]" && git push`

**CRITICAL**: Always fetch fresh data from the live URL. Never use `read_file` on wiki pages as the source of truth for pricing — only use it to compare against the freshly fetched data.

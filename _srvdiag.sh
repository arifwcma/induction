#!/usr/bin/env bash
set -e
cd /home/ssm-user/apps/induction
PSQL() { docker compose exec -T induction-postgres psql -U induction -d induction -t -A -c "$1"; }

echo "=== PROMPT_LEN_AND_AIIMS (len | has_AIIMS)"
PSQL "select length(prompt) || ' | ' || (position('AIIMS' in prompt) > 0) from system_prompt_config;"
echo "=== CLAUSE_COUNT"
PSQL "select count(*) from clause;"
echo "=== APPENDIX_C_UNITS"
PSQL "select count(*) from clause where breadcrumb ilike '%appendix c%';"
echo "=== CLAUSE_1_5"
PSQL "select clause_number || ' :: ' || left(title, 60) from clause where clause_number = '1.5';"
echo "=== EFFECTIVE_LLM_ENV (blank = default openai)"
grep -E '^(LLM_PROVIDER|FAST_LLM_PROVIDER|FAST_CHAT_MODEL|ANTHROPIC_CHAT_MODEL)=' .env || echo "(none set)"
echo "=== ANTHROPIC_KEY_PRESENT"
grep -c '^ANTHROPIC_API_KEY=.' .env || true

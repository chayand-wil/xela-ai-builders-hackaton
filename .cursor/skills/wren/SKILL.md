---
name: wren
description: "Wren CLI for AI agents — a semantic SQL layer over 22+ databases (Postgres, MySQL, BigQuery, Snowflake, Spark, …). The actual workflow guides live inside the `wren` CLI itself; this is just a discovery stub. Use whenever the user asks a data question (how many, show me, top N, compare, trend, breakdown, metric, revenue, customers, orders), wants to install / set up Wren Engine, connect a new database, connect SaaS data via dlt (HubSpot, Stripe, Salesforce, GitHub, Slack), generate or regenerate an MDL project from a database schema, enrich a project with business context (enum meanings, units, cubes like ARR / DAU / churn), or turn a project's context layer into a shareable GenBI web app / dashboard and deploy it to Vercel or Cloudflare. Triggers: 'install wren', 'set up wren engine', 'connect database to wren', 'connect SaaS to wren', 'load hubspot / stripe / salesforce data', 'generate mdl', 'scaffold wren project', 'enrich wren context', 'augment my project', 'add cubes', 'build a dashboard', 'make a shareable analytics app', 'deploy my context layer as a web app', 'genbi app', 'wren onboarding', 'wren usage', 'wren generate mdl', 'wren dlt connector', 'wren enrich context', 'wren genbi'."
license: Apache-2.0
allowed-tools: Bash(wren:*)
---

# Wren CLI

Discovery stub instalado desde la carpeta local `C:\Users\pablo\Downloads\WrenAI-main`.
Las guías viven en el CLI (`pip install wrenai` o editable desde `WrenAI-main/core/wren`).

En EduGuate IA: Wren es capa semántica (MDL + contexto). Las cifras del producto salen de `src/analytics` (DuckDB parametrizado). El LLM no ejecuta SQL libre contra el Parquet.

```bash
wren skills list
wren skills get onboarding
wren skills get usage
wren skills get generate-mdl
wren docs connection-info duckdb
```

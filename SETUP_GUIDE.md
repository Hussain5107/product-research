# Product Research Setup Guide

This repository contains an automated Amazon product research system designed for low-cost operation:

- GitHub Actions runs the research engine daily at 05:00 UTC, which is 09:00 in Asia/Dubai.
- Python collects configured product data from CSV/sample sources until authorized Amazon data access is connected.
- Gemini analyzes opportunities using structured JSON and strict no-invention rules.
- Deterministic code calculates profitability.
- Supabase stores products, runs, results, suppliers, and profit scenarios.
- The dashboard is static and can be hosted on InfinityFree.

## 1. Gemini API Key

Create a Gemini API key in Google AI Studio. Add it to GitHub Actions Secrets as `GEMINI_API_KEY`.

Set `GEMINI_MODEL` as a GitHub Actions variable if you want a model other than `gemini-1.5-flash`.

## 2. Supabase Project

Create a Supabase project, then run `supabase/migrations/001_initial_schema.sql` in the SQL editor.

Add these GitHub Actions Secrets:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

Use the service-role key only in GitHub Actions or other secure backend environments. Do not put it in dashboard files.

## 3. Dashboard Configuration

Copy `dashboard/config.example.js` to `dashboard/config.js` and fill in:

- `supabaseUrl`
- `supabaseAnonKey`

Only use the public anon key in the browser. The migration enables read access for authenticated users. Configure Supabase Auth according to your preferred login method before production use.

## 4. GitHub Actions

Workflow location:

`.github/workflows/daily-amazon-research.yml`

It supports:

- Daily scheduled run at `0 5 * * *`
- Manual `workflow_dispatch`
- Report artifacts in CSV and XLSX
- Concurrency protection to avoid overlapping runs

GitHub cron settings are stored in the workflow file. Editing schedule preferences in Supabase does not automatically change GitHub's cron schedule.

## 5. Manual Research

Use GitHub Actions -> Daily Amazon Product Research -> Run workflow.

Inputs:

- marketplace
- products_per_run
- categories

A secure browser button for triggering GitHub Actions requires a backend endpoint. InfinityFree static hosting should not expose GitHub tokens, so the safe initial implementation uses GitHub's manual workflow trigger.

The dashboard includes a Manual Research panel with the workflow link and fields to help choose dispatch inputs. It intentionally does not call the GitHub API from the browser.

## 6. Amazon Data

The current system does not scrape Amazon or bypass anti-bot controls. It supports:

- Sample fixture mode for development
- CSV import through `python -m product_research.cli --csv path/to/products.csv`
- Future authorized connector implementations

Required CSV fields:

- `name`
- `price`

Optional fields:

- `asin`
- `category`
- `product_url`
- `reviews`
- `rating`
- `bsr`

Files included:

- `data/amazon_import_template.csv`
- `data/sample_products.csv`

## 7. Supplier Research

Supplier connectors currently generate search links for Alibaba, 1688, and Made-in-China. They mark supplier details as `requires_quote` until quotations or authorized API data are imported.

## 8. InfinityFree Deployment

Upload the contents of `dashboard/` to your InfinityFree site, including a real `config.js`.

InfinityFree should only host the dashboard. It should not run scheduled jobs or hold service-role credentials.

## 9. Local Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m product_research.cli
pytest
```

Default mode is `sample`, so local runs do not consume Gemini quota or require Supabase.

## 10. Reports

Each run writes:

- `reports/daily_product_research_report.csv`
- `reports/daily_product_research_report.xlsx`

GitHub Actions uploads these as private workflow artifacts.

## 11. Troubleshooting

- Gemini quota exhausted: the engine falls back to low-confidence analysis and records the limitation.
- Supabase missing: reports still generate locally, but storage is disabled.
- Missing supplier costs: profit scenarios are marked incomplete.
- Live Amazon unavailable: import verified CSV data or connect an authorized data provider.


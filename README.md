# Product Research

Automated Amazon product research workspace for identifying marketplace opportunities, supplier leads, profitability scenarios, and AI-assisted recommendations.

The first implementation is intentionally conservative: it does not scrape Amazon or invent supplier data. It supports sample data and CSV import now, with extension points for authorized Amazon and supplier data providers later.

## What Is Included

- Python research engine
- Gemini analysis with structured JSON validation and fallback handling
- Deterministic profitability calculator
- Supplier search-link generation marked as requiring quotation
- Supabase schema with RLS
- Daily GitHub Actions workflow at 09:00 UAE time
- CSV and Excel report generation
- Static dashboard suitable for InfinityFree hosting
- Automated tests

See `SETUP_GUIDE.md` for setup and deployment.

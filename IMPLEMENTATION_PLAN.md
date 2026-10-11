# ProductHunter AI Implementation Plan

Last updated: 2026-10-10

## Current Workspace Assessment

The existing workspace is a partial Phase 1 application, not an empty project. It contains:

- Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn-style UI primitives, Recharts, and Lucide icons in `frontend/`.
- FastAPI, SQLAlchemy async models, Alembic, Redis/PostgreSQL service definitions, connector stubs, AI provider settings, dashboard APIs, product APIs, research run APIs, watchlist APIs, comparison APIs, and deterministic financial calculations in `backend/`.
- Docker Compose for PostgreSQL and Redis.
- Windows and Unix startup scripts.

The workspace is not currently a Git repository, so change history and branch-based review are unavailable.

## Existing Functionality

| Area | Status | Notes |
| --- | --- | --- |
| Local app shell | Partially implemented | Dashboard and navigation exist; app routes are limited. |
| Database schema | Partially implemented | Initial schema covers products, suppliers, research runs, observations, competitors, and financial scenarios. It does not yet cover global shopping comparisons, price alerts, promotions, reports, audit logs, or integration configuration persistence. |
| Research connectors | Planned / stubs | Connectors declare capabilities and configuration state but do not retrieve live Amazon, supplier, social, or trends data. |
| Financial calculator | Implemented and tested | Deterministic unit economics service exists and now has focused tests. |
| Product comparison | Partially implemented | Basic candidate and financial comparison endpoints exist. Sensitivity output now uses real backend calculations. |
| Global Deal Finder | Partially implemented | Deterministic manual-offer ranking and landed-cost calculation have been added. Live marketplace retrieval and checkout/shipping verification remain planned. |
| AI provider settings | Partially implemented | Server-side settings abstraction exists; provider calls are limited. |
| Automation | Planned / concept | Research status fields exist, but durable queued jobs, cancellation, retries, and schedules are not implemented. |
| Tests | Initial coverage | Focused tests now cover financial and global-deal calculations. Broader API, DB, frontend, and integration tests remain needed. |

## Reference Repository Review

| Repository | License / Reuse Position | Useful Ideas | Decision |
| --- | --- | --- | --- |
| `Umair706/amazon-omniscient` | All rights reserved; do not copy code. | Modular product research concepts, scoring workflow, MCP-style tools. | Learn from architecture only. |
| `nexscope-ai/Amazon-Skills` | MIT license. | Agent-style Amazon research skills, keyword/review/listing/PPC decomposition. | Adapt concepts where compliant; avoid claiming live data without credentials. |
| `sourabh0020/Amazon-Product-Sales-Analysis` | MIT license. | Data cleaning, statistical exploration, charts. | Adapt analytics patterns for imported datasets. |
| `omkarcloud/amazon-scraper` | MIT license. | Broad Amazon scraping coverage and examples. | Defer direct adoption pending compliance/security review; do not treat as official Amazon API. |
| `drawrowfly/amazon-product-api` | MIT license. | Product/search/review API shape and JSON output ideas. | Defer direct adoption pending maintenance and access-method review. |

## Data Access Limitations

ProductHunter AI must not fabricate marketplace or supplier facts. Until credentials or permitted data sources are configured:

- Amazon product prices, BSR, reviews, shipping eligibility, import fees, and discounts are unavailable unless manually imported or user supplied.
- Supplier costs, warehouse status, inventory, and shipping estimates are unavailable unless entered manually or retrieved through authorized supplier APIs.
- Google Trends, TikTok, Instagram, YouTube Shorts, Pinterest, Reddit, and ad-library signals require compliant connectors or manual imports.
- Global Deal Finder can rank submitted offers deterministically, but it cannot verify checkout totals without a supported source.

## Priority Order

1. Strengthen Phase 1 foundations:
   - Expand automated tests for existing services and APIs.
   - Add missing schema tables for global deal comparisons, exchange rates, promotions, saved deals, price alerts, integration configurations, and audit logs.
   - Add frontend pages for Product Finder, Profit Calculator, Global Deal Finder, Settings, Integrations, and Research History using real backend states.

2. Build compliant data ingestion:
   - Add connector health details, request logs, evidence records, rate-limit handling, and cache tables.
   - Support manual CSV/JSON imports for Amazon listings, supplier offers, reviews, and exchange rates.
   - Add official/licensed connector configuration screens before live data retrieval.

3. Amazon research module:
   - Implement ASIN/product input normalization.
   - Store marketplace listings, BSR observations, review summaries, keyword evidence, and competitor records.
   - Add scoring that reports missing fields and confidence.

4. Shopify supplier module:
   - Implement supplier platform adapters only where authorized APIs or exports are available.
   - Add US warehouse verification states and evidence timestamps.
   - Compare Amazon-to-Shopify economics using deterministic calculations.

5. Global Deal Finder:
   - Persist comparison sessions and offers.
   - Add exchange-rate connector.
   - Add manual and provider-backed shipping quote evidence.
   - Rank top five qualifying offers and separate similar/incomplete items.

6. Automation and reporting:
   - Add Redis-backed workers and scheduler.
   - Implement retry, cancellation, progress, and error inspection.
   - Add PDF, Excel, CSV, and JSON exports.

## Immediate Development Completed In This Run

- Added deterministic Global Deal Finder manual-offer ranking service.
- Added `/global-deals/rank-manual-offers` API endpoint.
- Fixed missing `HTTPException` import in comparison API.
- Replaced placeholder comparison sensitivity output with calculated sensitivity rows.
- Added backend tests for global deals and financial calculations.
- Added this implementation plan.

## Next Recommended Phase

Continue Phase 1 by adding persistent Global Deal Finder tables and a frontend page for manual offer entry. This creates a full usable personal-shopping workflow before live marketplace integrations are attempted.

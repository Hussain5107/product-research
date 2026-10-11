from __future__ import annotations

import asyncio
import sys
from contextlib import asynccontextmanager

# psycopg async mode cannot use Windows' default ProactorEventLoop; force the
# selector loop before uvicorn creates it (uvicorn loads this module first).
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.root import router as root_router
from app.api.settings_api import router as settings_router
from app.api.research_api import router as research_router
from app.api.products_api import router as products_router
from app.api.compare_api import router as compare_router
from app.api.watchlist_api import router as watchlist_router
from app.api.integrations_api import router as integrations_router
from app.api.dashboard_api import router as dashboard_router
from app.api.global_deals_api import router as global_deals_router
from app.api.suppliers_api import router as suppliers_router
from app.api.imports_api import router as imports_router
from app.api.email_api import router as email_router
from app.api.automation_api import router as automation_router
from app.api.exports_api import router as exports_router
from app.api.link_research_api import router as link_research_router
from app.api.category_research_api import router as category_research_router
from app.settings import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # shutdown


app = FastAPI(
    title="ProductHunter AI",
    description="AI-powered e-commerce product research platform for Amazon USA, Shopify USA, and future Middle East marketplaces.",
    version="0.1.0",
    lifespan=lifespan,
)

if settings.app_env == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(root_router)
app.include_router(settings_router)
app.include_router(research_router)
app.include_router(products_router)
app.include_router(compare_router)
app.include_router(watchlist_router)
app.include_router(integrations_router)
app.include_router(dashboard_router)
app.include_router(global_deals_router)
app.include_router(suppliers_router)
app.include_router(imports_router)
app.include_router(email_router)
app.include_router(automation_router)
app.include_router(exports_router)
app.include_router(link_research_router)
app.include_router(category_research_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "app": "ProductHunter AI"}

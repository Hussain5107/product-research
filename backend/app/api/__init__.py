from fastapi import APIRouter

from app.api.dashboard_api import router as dashboard_router
from app.api.compare_api import router as compare_router
from app.api.discovery_api import router as discovery_router
from app.api.email_api import router as email_router
from app.api.exports_api import router as exports_router
from app.api.imports_api import router as imports_router
from app.api.global_deals_api import router as global_deals_router
from app.api.link_research_api import router as link_research_router
from app.api.product_comparison_api import router as product_comparison_router
from app.api.products_api import router as products_router
from app.api.profit_calculator_api import router as profit_calculator_router
from app.api.research_api import router as research_router
from app.api.settings_api import router as settings_router
from app.api.suppliers_api import router as suppliers_router
from app.api.watchlist_api import router as watchlist_router

api = APIRouter()

api.include_router(settings_router, prefix="/settings", tags=["settings"])
api.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api.include_router(discovery_router, prefix="/discovery", tags=["discovery"])
api.include_router(supplier_finder_router := APIRouter(prefix="/supplier-finder", tags=["supplier-finder"]))
supplier_finder_router.include_router(suppliers_router)
api.include_router(link_research_router, prefix="/link-research", tags=["link-research"])
api.include_router(watchlist_router, prefix="/watchlist", tags=["watchlist"])
api.include_router(research_router, prefix="/research", tags=["research"])
api.include_router(imports_router, prefix="/imports", tags=["imports"])
api.include_router(global_deals_router, prefix="/global-deals", tags=["global-deals"])
api.include_router(compare_router, prefix="/compare", tags=["compare"])
api.include_router(product_comparison_router, prefix="/compare", tags=["compare"])
api.include_router(profit_calculator_router, prefix="/profit-calculator", tags=["profit-calculator"])
api.include_router(products_router, prefix="/products", tags=["products"])
api.include_router(exports_router, prefix="/exports", tags=["exports"])
api.include_router(email_router, prefix="/email", tags=["email"])

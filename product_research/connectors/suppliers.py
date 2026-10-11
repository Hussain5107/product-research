from __future__ import annotations

from urllib.parse import quote_plus

from product_research.models import ProductCandidate, SupplierLead


SUPPORTED_PLATFORMS = ["Alibaba", "1688", "AliExpress", "Made-in-China", "CJdropshipping"]


class SupplierConnector:
    """Generates supplier leads without claiming unavailable verification."""

    def find_leads(self, product: ProductCandidate) -> list[SupplierLead]:
        query = quote_plus(product.name)
        return [
            SupplierLead("Search Alibaba suppliers", "Alibaba", f"https://www.alibaba.com/trade/search?SearchText={query}", None, None, "requires_quote", "Manual quotation required."),
            SupplierLead("Search 1688 suppliers", "1688", f"https://s.1688.com/selloffer/offer_search.htm?keywords={query}", None, None, "requires_quote", "Chinese-language sourcing; verify export terms."),
            SupplierLead("Search Made-in-China suppliers", "Made-in-China", f"https://www.made-in-china.com/products-search/hot-china-products/{query}.html", None, None, "requires_quote", "Manual supplier verification required."),
        ]


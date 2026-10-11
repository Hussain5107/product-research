"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { fetchApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import {
  AlertCircle,
  CheckCircle,
  Clock,
  ExternalLink,
  Factory,
  Filter,
  Flame,
  Globe,
  Lightbulb,
  Loader2,
  Mail,
  MessageCircle,
  Package,
  Rocket,
  Search,
  ShieldCheck,
  ShoppingBag,
  SlidersHorizontal,
  TrendingUp,
} from "lucide-react";

type SearchMode =
  | "automatic_discovery"
  | "best_sellers"
  | "new_innovations"
  | "viral_web_finder"
  | "supplier_finder"
  | "analyze_specific_product";

const SEARCH_MODES: Array<{
  value: SearchMode;
  label: string;
  icon: typeof Search;
  query: string;
  note: string;
}> = [
  {
    value: "automatic_discovery",
    label: "Find New Products",
    icon: Search,
    query: "Find profitable Amazon and Shopify product opportunities",
    note: "General product discovery",
  },
  {
    value: "best_sellers",
    label: "Best Sellers",
    icon: ShoppingBag,
    query: "Find best selling products with low competition and supplier availability",
    note: "Amazon, marketplaces, and category leaders",
  },
  {
    value: "new_innovations",
    label: "New Innovations",
    icon: Rocket,
    query: "Find newly introduced innovative consumer products with e-commerce potential",
    note: "Launches, trade sites, and product-news sources",
  },
  {
    value: "viral_web_finder",
    label: "Viral Products",
    icon: Flame,
    query: "Find viral products from TikTok Instagram YouTube Shorts Reddit and product discovery websites",
    note: "Social proof and web trend signals",
  },
  {
    value: "supplier_finder",
    label: "Find Suppliers",
    icon: Factory,
    query: "Find suppliers, distributors, wholesalers, manufacturers, and dropshipping sources",
    note: "Supplier search and outreach prep",
  },
  {
    value: "analyze_specific_product",
    label: "Validate Product",
    icon: ShieldCheck,
    query: "",
    note: "ASIN, URL, keyword, or product idea",
  },
];

const QUICK_SUGGESTIONS = [
  "Home organization",
  "Pet accessories",
  "Car accessories",
  "Beauty devices",
  "Outdoor camping",
  "Tech gadgets",
  "Eco friendly",
  "Kitchen tools",
];

const CATEGORIES = [
  "All Categories",
  "Home & Kitchen",
  "Pet Supplies",
  "Beauty Accessories",
  "Automotive",
  "Electronics Accessories",
  "Health & Wellness",
  "Travel",
  "Fitness",
  "Tools",
  "Outdoor",
];

const DISCOVERY_SOURCES = [
  { name: "Amazon Best Sellers", status: "Configure", kind: "Marketplace" },
  { name: "Amazon Movers & Shakers", status: "Configure", kind: "Marketplace" },
  { name: "TikTok / TikTok Shop", status: "Planned", kind: "Social trend" },
  { name: "Instagram Reels", status: "Planned", kind: "Social trend" },
  { name: "YouTube Shorts", status: "Planned", kind: "Social trend" },
  { name: "Reddit", status: "Planned", kind: "Community signal" },
  { name: "Google Trends", status: "Configure", kind: "Demand signal" },
  { name: "Product discovery websites", status: "Planned", kind: "New products" },
  { name: "CJdropshipping", status: "Configure", kind: "Supplier" },
  { name: "Zendrop / Spocket", status: "Configure", kind: "Supplier" },
  { name: "Syncee / Doba / HyperSKU", status: "Configure", kind: "Supplier" },
  { name: "Alibaba / AliExpress", status: "Planned", kind: "Supplier" },
  { name: "US wholesalers", status: "Manual import", kind: "Supplier" },
];

const OPPORTUNITY_RULES = [
  "Low competition niches",
  "Growing search and social attention",
  "Supplier or distributor evidence",
  "Attractive contribution margin",
  "Amazon and Shopify channel fit",
];

interface ProductResult {
  id: number;
  name: string;
  category?: string | null;
  brand?: string | null;
  product_url?: string | null;
  image_url?: string | null;
  supplier_cost: string;
  shipping_cost: string;
  suggested_retail_price: string;
  us_warehouse_verified: boolean;
  trend_classification: string;
  viral_potential: string;
  primary_competition_level: string;
  status: string;
  region_code?: string | null;
}

export default function DiscoveryPage() {
  const router = useRouter();
  const [mode, setMode] = useState<SearchMode>("automatic_discovery");
  const [query, setQuery] = useState("");
  const [filtersOpen, setFiltersOpen] = useState(true);
  const [researching, setResearching] = useState(false);
  const [products, setProducts] = useState<ProductResult[]>([]);
  const [productsLoading, setProductsLoading] = useState(false);
  const [filters, setFilters] = useState({
    category: "All Categories",
    platform: "Both (Amazon & Shopify)",
    priceRange: "Any Price",
    monthlyRevenue: "Any",
    competition: "Any",
    supplierRegion: "US warehouse preferred",
  });

  const activeMode = useMemo(
    () => SEARCH_MODES.find((item) => item.value === mode) || SEARCH_MODES[0],
    [mode]
  );

  useEffect(() => {
    loadProducts();
  }, []);

  async function loadProducts() {
    setProductsLoading(true);
    try {
      const data = await fetchApi<ProductResult[]>("/products/list?limit=24");
      setProducts(data);
    } catch (error) {
      console.error("Product load failed", error);
    } finally {
      setProductsLoading(false);
    }
  }

  const selectMode = (value: SearchMode) => {
    const selected = SEARCH_MODES.find((item) => item.value === value);
    setMode(value);
    if (selected?.query) {
      setQuery(selected.query);
    }
  };

  const startResearch = useCallback(async () => {
    const cleanQuery = query.trim() || activeMode.query;
    if (!cleanQuery) return;

    setResearching(true);
    try {
      const params = new URLSearchParams({
        name: activeMode.label,
        description: cleanQuery,
        marketplace: filters.platform.startsWith("Amazon")
          ? "amazon"
          : filters.platform.startsWith("Shopify")
            ? "shopify"
            : "both",
        region_code: "US",
        mode,
        user_query: cleanQuery,
        categories: filters.category === "All Categories" ? "" : filters.category,
        source_names: "",
      });

      const result = await fetchApi<{ run_id: number; status: string }>(
        `/research/start?${params.toString()}`,
        { method: "POST" }
      );
      router.push(`/research-history/${result.run_id}`);
    } catch (error) {
      console.error("Research start failed", error);
    } finally {
      setResearching(false);
    }
  }, [activeMode, filters.category, filters.platform, mode, query, router]);

  return (
    <div className="-m-6 min-h-full bg-slate-50 p-4 text-slate-950 md:p-6">
      <div className="mx-auto grid max-w-[1500px] gap-4 xl:grid-cols-[1fr_300px]">
        <section className="space-y-4">
          <div className="overflow-hidden rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50 via-white to-violet-100 shadow-sm">
            <div className="grid gap-6 p-6 lg:grid-cols-[1fr_360px] lg:p-8">
              <div className="space-y-5">
                <Badge className="w-fit bg-indigo-100 text-indigo-700 hover:bg-indigo-100">
                  Product Finder
                </Badge>
                <div className="space-y-3">
                  <h1 className="max-w-3xl text-3xl font-bold tracking-tight text-slate-950 md:text-5xl">
                    Find Winning Products for Amazon & Shopify
                  </h1>
                  <p className="max-w-2xl text-base text-slate-600 md:text-lg">
                    Search product trends, supplier sources, best sellers, viral signals, and
                    innovation pages from one research workspace.
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {["Research", "Analyze", "Find suppliers", "Prepare outreach"].map((item) => (
                    <span
                      key={item}
                      className="rounded-full border border-white/70 bg-white/80 px-3 py-1 text-xs font-medium text-indigo-700 shadow-sm"
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>

              <div className="relative hidden min-h-[210px] lg:block">
                <div className="absolute right-10 top-8 h-40 w-56 rounded-2xl border border-sky-100 bg-white/70 shadow-lg" />
                <div className="absolute right-20 top-14 flex h-20 w-20 items-center justify-center rounded-2xl bg-white text-5xl font-bold shadow-lg">
                  a
                </div>
                <div className="absolute right-4 top-14 flex h-16 w-16 items-center justify-center rounded-2xl bg-white shadow-lg">
                  <ShoppingBag className="h-9 w-9 text-emerald-500" />
                </div>
                <div className="absolute bottom-10 right-28 flex items-end gap-2">
                  {[44, 70, 96, 126].map((height, index) => (
                    <div
                      key={height}
                      className="w-7 rounded-t-md bg-gradient-to-t from-indigo-600 to-sky-300 shadow-sm"
                      style={{ height }}
                    >
                      <span className="sr-only">Growth bar {index + 1}</span>
                    </div>
                  ))}
                </div>
                <TrendingUp className="absolute right-24 top-10 h-12 w-12 rotate-12 text-sky-500" />
              </div>
            </div>
          </div>

          <Card className="border-slate-200 bg-white shadow-sm">
            <CardContent className="space-y-4 p-4">
              <div className="grid gap-2 md:grid-cols-3 xl:grid-cols-6">
                {SEARCH_MODES.map((item) => {
                  const Icon = item.icon;
                  const active = item.value === mode;
                  return (
                    <Button
                      key={item.value}
                      type="button"
                      variant={active ? "default" : "outline"}
                      onClick={() => selectMode(item.value)}
                      className={
                        active
                          ? "h-auto justify-start gap-2 rounded-xl bg-indigo-600 py-3 text-left text-white hover:bg-indigo-700"
                          : "h-auto justify-start gap-2 rounded-xl border-slate-200 bg-slate-50 py-3 text-left text-slate-700 hover:bg-white"
                      }
                    >
                      <Icon className="h-4 w-4 shrink-0" />
                      <span className="truncate text-sm">{item.label}</span>
                    </Button>
                  );
                })}
              </div>

              <div className="grid gap-3 lg:grid-cols-[1fr_190px]">
                <div className="relative">
                  <Search className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
                  <Input
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="Enter a niche, product idea, supplier type, or problem..."
                    className="h-12 rounded-xl border-slate-200 bg-white pl-12 text-slate-900 placeholder:text-slate-400"
                  />
                </div>
                <Button
                  onClick={startResearch}
                  disabled={researching || !(query.trim() || activeMode.query)}
                  className="h-12 rounded-xl bg-indigo-600 text-white hover:bg-indigo-700"
                >
                  {researching ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Searching
                    </>
                  ) : (
                    <>
                      Research Products
                      <ExternalLink className="ml-2 h-4 w-4" />
                    </>
                  )}
                </Button>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-medium text-slate-500">Quick suggestions:</span>
                {QUICK_SUGGESTIONS.map((item) => (
                  <Button
                    key={item}
                    variant="outline"
                    size="sm"
                    onClick={() => setQuery(item)}
                    className="h-8 rounded-full border-indigo-100 bg-indigo-50/60 px-3 text-xs text-indigo-700 hover:bg-indigo-100"
                  >
                    {item}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-sm">
            <CardContent className="space-y-4 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-semibold text-slate-950">
                  <Filter className="h-5 w-5" />
                  Filters
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setFiltersOpen((value) => !value)}
                  className="text-indigo-700"
                >
                  <SlidersHorizontal className="mr-2 h-4 w-4" />
                  More Filters
                </Button>
              </div>

              {filtersOpen && (
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
                  <FilterSelect
                    label="Category"
                    value={filters.category}
                    options={CATEGORIES}
                    onChange={(value) => setFilters({ ...filters, category: value })}
                  />
                  <FilterSelect
                    label="Platform"
                    value={filters.platform}
                    options={["Both (Amazon & Shopify)", "Amazon", "Shopify"]}
                    onChange={(value) => setFilters({ ...filters, platform: value })}
                  />
                  <FilterSelect
                    label="Price Range"
                    value={filters.priceRange}
                    options={["Any Price", "$15-$30", "$30-$60", "$60-$120"]}
                    onChange={(value) => setFilters({ ...filters, priceRange: value })}
                  />
                  <FilterSelect
                    label="Monthly Revenue"
                    value={filters.monthlyRevenue}
                    options={["Any", "$5k+", "$20k+", "$50k+"]}
                    onChange={(value) => setFilters({ ...filters, monthlyRevenue: value })}
                  />
                  <FilterSelect
                    label="Competition"
                    value={filters.competition}
                    options={["Any", "Low", "Moderate", "High"]}
                    onChange={(value) => setFilters({ ...filters, competition: value })}
                  />
                  <FilterSelect
                    label="Supplier Region"
                    value={filters.supplierRegion}
                    options={["US warehouse preferred", "US only", "Global", "Manufacturer direct"]}
                    onChange={(value) => setFilters({ ...filters, supplierRegion: value })}
                  />
                </div>
              )}
            </CardContent>
          </Card>

          <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
            <Card className="border-slate-200 bg-white shadow-sm">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <CardTitle className="text-xl text-slate-950">Recommended Products</CardTitle>
                    <p className="mt-1 text-sm text-slate-500">
                      Stored product candidates with pricing, supplier evidence status, and channel fit.
                    </p>
                  </div>
                  <Badge variant="secondary" className="bg-slate-100 text-slate-600">
                    {productsLoading ? "Loading" : `${products.length} saved`}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                {products.length === 0 ? (
                  <div className="grid gap-3 md:grid-cols-3">
                    {[
                      {
                        icon: Package,
                        title: "Product evidence",
                        body: "Listings, trends, prices, reviews, and source URLs will appear here.",
                      },
                      {
                        icon: Factory,
                        title: "Supplier details",
                        body: "Supplier URL, MOQ, warehouse, cost, delivery, and contact fields.",
                      },
                      {
                        icon: Mail,
                        title: "Outreach draft",
                        body: "Email and WhatsApp contact fields stay separate until you configure them.",
                      },
                    ].map((item) => {
                      const Icon = item.icon;
                      return (
                        <div key={item.title} className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                          <Icon className="h-5 w-5 text-indigo-600" />
                          <h3 className="mt-3 font-semibold text-slate-950">{item.title}</h3>
                          <p className="mt-1 text-sm text-slate-500">{item.body}</p>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                    {products.map((product) => (
                      <article key={product.id} className="rounded-xl border border-slate-100 bg-slate-50 p-3">
                        <div className="aspect-[4/3] overflow-hidden rounded-lg bg-white">
                          {product.image_url ? (
                            <img
                              src={product.image_url}
                              alt={product.name}
                              className="h-full w-full object-cover"
                            />
                          ) : (
                            <div className="flex h-full items-center justify-center">
                              <Package className="h-10 w-10 text-indigo-300" />
                            </div>
                          )}
                        </div>
                        <div className="mt-3 space-y-2">
                          <div className="flex items-start justify-between gap-2">
                            <h3 className="line-clamp-2 font-semibold text-slate-950">{product.name}</h3>
                            <Badge variant={product.viral_potential === "high" ? "warning" : "secondary"}>
                              {product.viral_potential}
                            </Badge>
                          </div>
                          <p className="text-xs text-slate-500">{product.category || "Uncategorized"}</p>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            <MetricPill label="Cost" value={`$${Number(product.supplier_cost).toFixed(2)}`} />
                            <MetricPill label="Sell" value={`$${Number(product.suggested_retail_price).toFixed(2)}`} />
                            <MetricPill label="Trend" value={product.trend_classification} />
                            <MetricPill label="Competition" value={product.primary_competition_level} />
                          </div>
                          <div className="flex gap-2">
                            {product.product_url && (
                              <Button asChild variant="outline" size="sm" className="h-8 flex-1">
                                <a href={product.product_url} target="_blank" rel="noreferrer">
                                  View Source
                                </a>
                              </Button>
                            )}
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-8 flex-1"
                              onClick={() => router.push(`/products/${product.id}`)}
                            >
                              Details
                            </Button>
                          </div>
                        </div>
                      </article>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="border-slate-200 bg-white shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg text-slate-950">
                  <MessageCircle className="h-5 w-5 text-emerald-500" />
                  Supplier Outreach
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <StatusRow icon={Mail} label="Email sending" status="Needs setup" />
                <StatusRow icon={MessageCircle} label="WhatsApp contacts" status="Capture only" />
                <StatusRow icon={Factory} label="Supplier database" status="Planned" />
                <div className="rounded-xl bg-amber-50 p-3 text-amber-800">
                  <div className="flex gap-2">
                    <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                    <p>
                      Emails should be sent only after you connect your mailbox and approve each
                      message. WhatsApp numbers will be stored as supplier contact evidence.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        <aside className="space-y-4">
          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg text-slate-950">
                <TrendingUp className="h-5 w-5 text-indigo-600" />
                Auto Search Lanes
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {SEARCH_MODES.slice(1, 5).map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.value}
                    onClick={() => selectMode(item.value)}
                    className="flex w-full items-center gap-3 rounded-xl border border-slate-100 bg-slate-50 p-3 text-left transition hover:border-indigo-200 hover:bg-indigo-50"
                  >
                    <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-white text-indigo-600 shadow-sm">
                      <Icon className="h-4 w-4" />
                    </span>
                    <span>
                      <span className="block text-sm font-semibold text-slate-950">{item.label}</span>
                      <span className="block text-xs text-slate-500">{item.note}</span>
                    </span>
                  </button>
                );
              })}
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg text-slate-950">
                <Lightbulb className="h-5 w-5 text-amber-500" />
                Market Opportunities
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {OPPORTUNITY_RULES.map((item) => (
                <div key={item} className="flex items-center gap-3 text-sm text-slate-600">
                  <CheckCircle className="h-5 w-5 text-emerald-500" />
                  <span>{item}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg text-slate-950">
                <Globe className="h-5 w-5 text-sky-500" />
                Source Coverage
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {DISCOVERY_SOURCES.map((source) => (
                <div
                  key={source.name}
                  className="flex items-center justify-between gap-3 rounded-lg bg-slate-50 px-3 py-2"
                >
                  <div>
                    <p className="text-sm font-medium text-slate-800">{source.name}</p>
                    <p className="text-xs text-slate-500">{source.kind}</p>
                  </div>
                  <Badge
                    variant={source.status === "Configure" ? "warning" : "secondary"}
                    className={source.status === "Planned" ? "bg-slate-100 text-slate-600" : ""}
                  >
                    {source.status}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg text-slate-950">
                <Clock className="h-5 w-5 text-slate-500" />
                Recent Searches
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {QUICK_SUGGESTIONS.slice(0, 5).map((item) => (
                <button
                  key={item}
                  onClick={() => setQuery(item)}
                  className="flex w-full items-center gap-2 rounded-lg bg-slate-50 px-3 py-2 text-left text-sm text-slate-700 hover:bg-indigo-50"
                >
                  <Clock className="h-4 w-4 text-slate-400" />
                  {item.toLowerCase()}
                </button>
              ))}
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}

function FilterSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium text-slate-500">{label}</label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="h-11 rounded-xl border-slate-200 bg-white text-slate-900">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem key={option} value={option}>
              {option}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

function StatusRow({
  icon: Icon,
  label,
  status,
}: {
  icon: typeof Mail;
  label: string;
  status: string;
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2">
      <span className="flex items-center gap-2 text-slate-700">
        <Icon className="h-4 w-4 text-indigo-600" />
        {label}
      </span>
      <Badge variant="secondary" className="bg-white text-slate-600">
        {status}
      </Badge>
    </div>
  );
}

function MetricPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-white px-2 py-1.5">
      <p className="text-[10px] font-medium uppercase text-slate-400">{label}</p>
      <p className="truncate font-semibold text-slate-800">{value}</p>
    </div>
  );
}

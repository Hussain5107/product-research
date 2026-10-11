"use client";

import { useMemo, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  Clipboard,
  Loader2,
  PackageSearch,
  Upload,
  Search,
  Sparkles,
  Star,
} from "lucide-react";
import { fetchApi } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";

interface ResearchLane {
  name: string;
  mission: string;
}

interface ResearchProduct {
  name: string;
  buyer_problem: string;
  uae_angle: string;
  score: number;
  shipping_difficulty: string;
  return_risk: string;
  supplier_keywords: string[];
}

interface SupplierSearch {
  platform: string;
  query: string;
  vetting: string;
}

interface CategoryResearchPlan {
  status: string;
  ai: {
    configured: boolean;
    provider?: string;
    model?: string;
    message?: string;
  };
  research_lanes: ResearchLane[];
  top_products: ResearchProduct[];
  supplier_searches: SupplierSearch[];
  copy_prompt: string;
  report_markdown: string;
  next_actions: string[];
}

interface ImportedWorkbook {
  filename: string;
  sheets: { name: string; rows: number }[];
  products: ImportedProduct[];
  suppliers: ImportedSupplier[];
  unit_economics: ImportedEconomics[];
  summary: {
    product_count: number;
    supplier_count: number;
    economics_count: number;
    top_product?: ImportedProduct | null;
    best_bundle?: ImportedEconomics | null;
  };
}

interface ImportedProduct {
  rank?: number;
  product: string;
  subcategory?: string;
  buyer_problem?: string;
  uae_use_case?: string;
  retail_low_aed?: number;
  retail_high_aed?: number;
  china_buy_low_aed?: number;
  china_buy_high_aed?: number;
  shipping?: string;
  return_risk?: string;
  competition?: string;
  differentiation?: string;
  ad_hook?: string;
  search_leads?: string;
  score?: number;
  launch_priority?: string;
}

interface ImportedSupplier {
  tier?: string;
  supplier: string;
  platform?: string;
  best_product_fit?: string;
  public_signals?: string;
  reliability_note?: string;
  first_inquiry?: string;
  url?: string;
}

interface ImportedEconomics {
  offer: string;
  retail_incl_vat?: number;
  product_cost?: number;
  inbound?: number;
  paid_cac?: number;
  contribution_aed?: number;
  contribution_margin?: number;
  max_break_even_cac?: number;
}

const DEFAULT_NOTES =
  "Focus on outdoor camping, desert picnic, car camping, glamping, portable comfort, lighting, water, storage, and products suitable for UAE Shopify dropshipping or small MOQ stock.";

export default function CategoryResearchPage() {
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  const [importing, setImporting] = useState(false);
  const [imported, setImported] = useState<ImportedWorkbook | null>(null);
  const [plan, setPlan] = useState<CategoryResearchPlan | null>(null);
  const [form, setForm] = useState({
    category: "Outdoor camping, desert picnic, car camping, and glamping",
    target_market: "UAE and GCC",
    source_market: "China",
    store_platform: "Shopify",
    product_count: "30",
    notes: DEFAULT_NOTES,
  });

  const aiStatus = useMemo(() => {
    if (!plan) return "Not generated yet";
    return plan.ai.configured ? `${plan.ai.provider || "AI"} configured` : plan.ai.message || "AI not configured";
  }, [plan]);

  async function generatePlan() {
    setLoading(true);
    setError("");
    setCopied(false);
    try {
      const data = await fetchApi<CategoryResearchPlan>("/category-research/plan", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          product_count: Number(form.product_count || 30),
        }),
      });
      setPlan(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate category research plan.");
    } finally {
      setLoading(false);
    }
  }

  async function copyPrompt() {
    if (!plan) return;
    await navigator.clipboard.writeText(plan.copy_prompt);
    setCopied(true);
  }

  async function importWorkbook(file: File | null) {
    if (!file) return;
    setImporting(true);
    setError("");
    try {
      const content_base64 = await fileToBase64(file);
      const data = await fetchApi<ImportedWorkbook>("/category-research/import-workbook", {
        method: "POST",
        body: JSON.stringify({
          filename: file.name,
          content_base64,
        }),
      });
      setImported(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not import workbook.");
    } finally {
      setImporting(false);
    }
  }

  return (
    <div className="-m-6 min-h-full bg-slate-50 p-4 text-slate-950 md:p-6">
      <div className="mx-auto grid max-w-[1400px] gap-4 xl:grid-cols-[minmax(0,1fr)_420px]">
        <section className="space-y-4">
          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <Badge className="bg-indigo-100 text-indigo-700 hover:bg-indigo-100">
              UAE Category Research Agent
            </Badge>
            <h1 className="mt-3 text-2xl font-bold tracking-tight md:text-4xl">
              Research UAE dropshipping categories from China suppliers.
            </h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-600 md:text-base">
              This is the first active agent. It turns one category into focused research lanes,
              product shortlists, China supplier searches, UAE positioning, and Shopify next steps.
            </p>
          </div>

          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <PackageSearch className="h-5 w-5 text-indigo-600" />
                Research brief
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3 md:grid-cols-2">
                <Field label="Category">
                  <Input value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })} />
                </Field>
                <Field label="Target market">
                  <Input value={form.target_market} onChange={(event) => setForm({ ...form, target_market: event.target.value })} />
                </Field>
                <Field label="Source market">
                  <Input value={form.source_market} onChange={(event) => setForm({ ...form, source_market: event.target.value })} />
                </Field>
                <Field label="Store platform">
                  <Input value={form.store_platform} onChange={(event) => setForm({ ...form, store_platform: event.target.value })} />
                </Field>
              </div>

              <Field label="Product ideas requested">
                <Input
                  type="number"
                  min="10"
                  max="50"
                  value={form.product_count}
                  onChange={(event) => setForm({ ...form, product_count: event.target.value })}
                />
              </Field>

              <Field label="Research notes">
                <Textarea
                  className="min-h-[130px]"
                  value={form.notes}
                  onChange={(event) => setForm({ ...form, notes: event.target.value })}
                />
              </Field>

              {error && (
                <div className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                  {error}
                </div>
              )}

              <Button onClick={generatePlan} disabled={loading} className="w-full bg-indigo-600 text-white hover:bg-indigo-700">
                {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Sparkles className="mr-2 h-4 w-4" />}
                Run Category Agent
              </Button>
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Upload className="h-5 w-5 text-indigo-600" />
                Import research workbook
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-slate-600">
                Upload the Excel output from your web research AI. The agent will extract the product scorecard,
                supplier shortlist, and unit economics into this workspace.
              </p>
              <Input
                type="file"
                accept=".xlsx"
                disabled={importing}
                onChange={(event) => importWorkbook(event.target.files?.[0] || null)}
              />
              {importing && (
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Importing workbook...
                </div>
              )}
            </CardContent>
          </Card>

          {plan && (
            <>
              <Card className="border-slate-200 bg-white shadow-sm">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Search className="h-5 w-5 text-indigo-600" />
                    Research lanes
                  </CardTitle>
                </CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-2">
                  {plan.research_lanes.map((lane) => (
                    <div key={lane.name} className="rounded-lg bg-slate-50 p-3">
                      <p className="font-semibold text-slate-950">{lane.name}</p>
                      <p className="mt-1 text-sm text-slate-600">{lane.mission}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card className="border-slate-200 bg-white shadow-sm">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Star className="h-5 w-5 text-amber-500" />
                    Starter product shortlist
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {plan.top_products.map((product) => (
                    <div key={product.name} className="rounded-lg border border-slate-200 p-3">
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div>
                          <p className="font-semibold text-slate-950">{product.name}</p>
                          <p className="mt-1 text-sm text-slate-600">{product.uae_angle}</p>
                        </div>
                        <Badge variant={product.score >= 8 ? "success" : "warning"}>{product.score}/10</Badge>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2 text-xs">
                        <Badge variant="soft">Shipping: {product.shipping_difficulty}</Badge>
                        <Badge variant="soft">Returns: {product.return_risk}</Badge>
                      </div>
                      <p className="mt-2 text-xs text-slate-500">
                        Search: {product.supplier_keywords.join(" | ")}
                      </p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </>
          )}

          {imported && (
            <>
              <Card className="border-slate-200 bg-white shadow-sm">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Star className="h-5 w-5 text-amber-500" />
                    Imported product scorecard
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {imported.products.slice(0, 12).map((product) => (
                    <div key={`${product.rank}-${product.product}`} className="rounded-lg border border-slate-200 p-3">
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div>
                          <p className="font-semibold text-slate-950">
                            {product.rank ? `${product.rank}. ` : ""}{product.product}
                          </p>
                          <p className="mt-1 text-sm text-slate-600">{product.uae_use_case}</p>
                        </div>
                        <Badge variant={(product.score || 0) >= 8.5 ? "success" : "warning"}>
                          {product.score || "n/a"}/10
                        </Badge>
                      </div>
                      <div className="mt-3 grid gap-2 text-xs md:grid-cols-4">
                        <MiniMetric label="Retail" value={moneyRange(product.retail_low_aed, product.retail_high_aed)} />
                        <MiniMetric label="China Cost" value={moneyRange(product.china_buy_low_aed, product.china_buy_high_aed)} />
                        <MiniMetric label="Shipping" value={product.shipping || "n/a"} />
                        <MiniMetric label="Returns" value={product.return_risk || "n/a"} />
                      </div>
                      {product.ad_hook && (
                        <p className="mt-2 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
                          Hook: {product.ad_hook}
                        </p>
                      )}
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card className="border-slate-200 bg-white shadow-sm">
                <CardHeader>
                  <CardTitle className="text-lg">Bundle economics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {imported.unit_economics.slice(0, 8).map((item) => (
                    <div key={item.offer} className="grid gap-2 rounded-lg bg-slate-50 p-3 text-sm md:grid-cols-[1fr_90px_90px_90px]">
                      <span className="font-medium text-slate-950">{item.offer}</span>
                      <span>Retail {formatMoney(item.retail_incl_vat)}</span>
                      <span>Profit {formatMoney(item.contribution_aed)}</span>
                      <span>{formatPercent(item.contribution_margin)}</span>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </>
          )}
        </section>

        <aside className="space-y-4">
          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg">Output</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-lg bg-slate-50 p-3 text-sm">
                <p className="font-semibold text-slate-900">AI status</p>
                <p className="mt-1 text-slate-600">{aiStatus}</p>
              </div>

              {!plan ? (
                <div className="space-y-2 text-sm text-slate-600">
                  <CheckItem text="Research lanes like the other AI workflow" />
                  <CheckItem text="Product shortlist with UAE-specific angles" />
                  <CheckItem text="Supplier search queries for China platforms" />
                  <CheckItem text="Copy prompt for Codex or another AI tool" />
                </div>
              ) : (
                <>
                  <Button variant="outline" className="w-full" onClick={copyPrompt}>
                    <Clipboard className="mr-2 h-4 w-4" />
                    {copied ? "Copied Prompt" : "Copy AI Research Prompt"}
                  </Button>

                  <Separator />

                  <div className="space-y-2">
                    <p className="font-semibold text-slate-950">Supplier searches</p>
                    {plan.supplier_searches.map((search) => (
                      <div key={`${search.platform}-${search.query}`} className="rounded-lg bg-slate-50 p-3 text-sm">
                        <p className="font-medium text-slate-900">{search.platform}</p>
                        <p className="mt-1 font-mono text-xs text-indigo-700">{search.query}</p>
                        <p className="mt-1 text-xs text-slate-600">{search.vetting}</p>
                      </div>
                    ))}
                  </div>

                  <Separator />

                  <div className="space-y-2">
                    <p className="font-semibold text-slate-950">Next actions</p>
                    {plan.next_actions.map((action) => (
                      <CheckItem key={action} text={action} />
                    ))}
                  </div>
                </>
              )}

              {imported && (
                <>
                  <Separator />
                  <div className="space-y-2">
                    <p className="font-semibold text-slate-950">Imported workbook</p>
                    <p className="text-sm text-slate-600">{imported.filename}</p>
                    <div className="grid grid-cols-3 gap-2 text-center">
                      <SummaryBox label="Products" value={imported.summary.product_count} />
                      <SummaryBox label="Suppliers" value={imported.summary.supplier_count} />
                      <SummaryBox label="Models" value={imported.summary.economics_count} />
                    </div>
                    {imported.summary.best_bundle && (
                      <div className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-900">
                        <p className="font-semibold">Best bundle</p>
                        <p>{imported.summary.best_bundle.offer}</p>
                        <p>{formatPercent(imported.summary.best_bundle.contribution_margin)} contribution margin</p>
                      </div>
                    )}
                  </div>

                  <Separator />

                  <div className="space-y-2">
                    <p className="font-semibold text-slate-950">Supplier leads</p>
                    {imported.suppliers.slice(0, 5).map((supplier) => (
                      <div key={`${supplier.supplier}-${supplier.best_product_fit}`} className="rounded-lg bg-slate-50 p-3 text-sm">
                        <p className="font-medium text-slate-900">{supplier.supplier}</p>
                        <p className="text-xs text-slate-500">{supplier.platform} - {supplier.best_product_fit}</p>
                        <p className="mt-1 text-xs text-slate-600">{supplier.first_inquiry}</p>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {plan && (
            <Card className="border-indigo-200 bg-indigo-50 shadow-sm">
              <CardContent className="space-y-2 p-4 text-sm text-indigo-950">
                <p className="font-semibold">Workflow</p>
                <p>Run the copied prompt in a web research AI for live evidence. Next, we can connect this agent directly to web search and saved product tables.</p>
              </CardContent>
            </Card>
          )}
        </aside>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium text-slate-700">{label}</label>
      {children}
    </div>
  );
}

function CheckItem({ text }: { text: string }) {
  return (
    <div className="flex gap-2 text-sm text-slate-600">
      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
      <span>{text}</span>
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-50 p-2">
      <p className="font-semibold uppercase text-slate-400">{label}</p>
      <p className="mt-1 text-slate-700">{value}</p>
    </div>
  );
}

function SummaryBox({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg bg-slate-50 p-2">
      <p className="text-lg font-bold text-slate-950">{value}</p>
      <p className="text-[11px] text-slate-500">{label}</p>
    </div>
  );
}

function fileToBase64(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

function moneyRange(low?: number, high?: number) {
  if (!low && !high) return "n/a";
  if (low && high) return `AED ${low}-${high}`;
  return formatMoney(low || high);
}

function formatMoney(value?: number) {
  if (value === undefined || value === null) return "n/a";
  return `AED ${Math.round(value)}`;
}

function formatPercent(value?: number) {
  if (value === undefined || value === null) return "n/a";
  const percent = value > 1 ? value : value * 100;
  return `${percent.toFixed(1)}%`;
}

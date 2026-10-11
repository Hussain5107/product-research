"use client";

import { cloneElement, isValidElement, useId, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  ClipboardCheck,
  DollarSign,
  ExternalLink,
  HelpCircle,
  Link2,
  Loader2,
  Package,
  Save,
  Sparkles,
  Truck,
} from "lucide-react";
import { fetchApi } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";

interface LinkResearchResult {
  product_id?: number | null;
  name: string;
  url: string;
  fetch_status: string;
  ai: {
    configured: boolean;
    provider?: string;
    analysis?: Record<string, unknown> | null;
  };
  financials: Record<string, string | null>;
  recommendation: {
    rating: string;
    reason: string;
    decision?: string;
    confidence?: string;
    why?: string[];
    risks?: string[];
    missing_proof?: string[];
    next_steps?: string[];
    supplier_questions?: string[];
    positioning_angle?: string;
  };
  note: string;
}

const DEFAULT_PROMPT =
  "Verify this product for UAE ecommerce. Tell me if I should work on it, avoid it, or shortlist it. Check supplier quality, differentiation, profitability, delivery risk, competition, demand proof, and exactly what I must verify next.";

const SUPPLIER_CHECK_TEMPLATE = `1688 / supplier quality check:
- Product type:
- Supplier name:
- Factory or trading company:
- Years on platform:
- Rating / repeat buyer proof:
- Price range:
- MOQ:
- Main specs shown:
- Battery capacity:
- Charging type:
- Material claims:
- Certifications:
- Shipping / delivery:
- What looks different from basic sellers:
- Concerns I noticed:`;

const WATER_PUMP_TEMPLATE = `Water bottle pump quality checklist:
- Foldable spout: yes/no
- Type-C charging: yes/no
- Measured dispensing modes: yes/no
- LED battery display: yes/no
- Battery: 1200mAh minimum, 1800-2000mAh preferred
- Food-grade silicone tube: yes/no
- 304 stainless steel outlet: yes/no
- Fits UAE 19L / 5-gallon bottle neck: yes/no
- Quiet motor / noise claim: yes/no
- Spare tube included: yes/no
- Arabic/English packaging possible: yes/no
- Warranty / replacement support: yes/no`;

export default function ProductVerifierPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<LinkResearchResult | null>(null);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    url: "",
    goal_prompt: DEFAULT_PROMPT,
    product_name: "",
    category: "",
    supplier_name: "",
    supplier_platform: "",
    supplier_cost: "",
    shipping_cost: "",
    processing_fee: "",
    suggested_retail_price: "",
    delivery_estimate_days: "",
    warehouse_origin: "",
    notes: "",
  });

  function appendNotes(text: string) {
    setForm((current) => ({
      ...current,
      notes: [current.notes.trim(), text].filter(Boolean).join("\n\n"),
    }));
  }

  async function analyze() {
    setLoading(true);
    setResult(null);
    setError("");
    try {
      const data = await fetchApi<LinkResearchResult>("/link-research/analyze-guided", {
        method: "POST",
        body: JSON.stringify({
          mode: "create",
          url: form.url,
          goal_prompt: form.goal_prompt,
          product_name: form.product_name || null,
          category: form.category || null,
          supplier_name: form.supplier_name || null,
          supplier_platform: form.supplier_platform || "manual_entry",
          supplier_cost: Number(form.supplier_cost || 0),
          shipping_cost: Number(form.shipping_cost || 0),
          processing_fee: Number(form.processing_fee || 0),
          suggested_retail_price: Number(form.suggested_retail_price || 0),
          delivery_estimate_days: form.delivery_estimate_days ? Number(form.delivery_estimate_days) : null,
          warehouse_origin: form.warehouse_origin || null,
          notes: form.notes || null,
        }),
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not analyze this product.");
    } finally {
      setLoading(false);
    }
  }

  const decision = result?.recommendation.decision || result?.recommendation.rating;
  const verdictVariant =
    result?.recommendation.rating === "strong"
      ? "success"
      : result?.recommendation.rating === "weak"
        ? "danger"
        : "warning";

  return (
    <div className="-m-6 min-h-full bg-slate-50 p-4 text-slate-950 md:p-6">
      <div className="mx-auto grid max-w-[1400px] gap-4 xl:grid-cols-[minmax(0,1fr)_420px]">
        <section className="space-y-4">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <Badge className="bg-indigo-100 text-indigo-700 hover:bg-indigo-100">
              Product Verifier
            </Badge>
            <h1 className="mt-3 text-2xl font-bold tracking-tight md:text-4xl">
              Paste any product link. Get a clear decision.
            </h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-600 md:text-base">
              Use this when Amazon, 1688, TikTok, Taobao, or supplier pages are messy or blocked.
              Paste the link, copy the visible listing details into evidence, and get a practical
              work / shortlist / avoid decision.
            </p>
          </div>

          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Link2 className="h-5 w-5 text-indigo-600" />
                Product link and instructions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Field label="Product or store link">
                <Input
                  placeholder="https://..."
                  value={form.url}
                  onChange={(event) => setForm({ ...form, url: event.target.value })}
                />
              </Field>

              <Field label="What should AI decide for you?">
                <Textarea
                  className="min-h-[100px]"
                  value={form.goal_prompt}
                  onChange={(event) => setForm({ ...form, goal_prompt: event.target.value })}
                />
              </Field>

              <div className="grid gap-3 md:grid-cols-2">
                <Field label="Product name">
                  <Input
                    placeholder="Optional, but helpful"
                    value={form.product_name}
                    onChange={(event) => setForm({ ...form, product_name: event.target.value })}
                  />
                </Field>
                <Field label="Category">
                  <Input
                    placeholder="Home, pet, beauty, fitness..."
                    value={form.category}
                    onChange={(event) => setForm({ ...form, category: event.target.value })}
                  />
                </Field>
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <DollarSign className="h-5 w-5 text-emerald-600" />
                Costs and selling price
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3 md:grid-cols-4">
                <Field label="Product cost">
                  <Input
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="0.00"
                    value={form.supplier_cost}
                    onChange={(event) => setForm({ ...form, supplier_cost: event.target.value })}
                  />
                </Field>
                <Field label="Shipping">
                  <Input
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="0.00"
                    value={form.shipping_cost}
                    onChange={(event) => setForm({ ...form, shipping_cost: event.target.value })}
                  />
                </Field>
                <Field label="Other fees">
                  <Input
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="0.00"
                    value={form.processing_fee}
                    onChange={(event) => setForm({ ...form, processing_fee: event.target.value })}
                  />
                </Field>
                <Field label="Selling price">
                  <Input
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="0.00"
                    value={form.suggested_retail_price}
                    onChange={(event) => setForm({ ...form, suggested_retail_price: event.target.value })}
                  />
                </Field>
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Truck className="h-5 w-5 text-sky-600" />
                Supplier proof
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3 md:grid-cols-2">
                <Field label="Supplier">
                  <Input
                    placeholder="CJdropshipping, AliExpress, Alibaba..."
                    value={form.supplier_name}
                    onChange={(event) => setForm({ ...form, supplier_name: event.target.value })}
                  />
                </Field>
                <Field label="Platform">
                  <Input
                    placeholder="Supplier platform"
                    value={form.supplier_platform}
                    onChange={(event) => setForm({ ...form, supplier_platform: event.target.value })}
                  />
                </Field>
                <Field label="Warehouse origin">
                  <Input
                    placeholder="China, US warehouse, UAE..."
                    value={form.warehouse_origin}
                    onChange={(event) => setForm({ ...form, warehouse_origin: event.target.value })}
                  />
                </Field>
                <Field label="Delivery days">
                  <Input
                    type="number"
                    min="0"
                    placeholder="7"
                    value={form.delivery_estimate_days}
                    onChange={(event) => setForm({ ...form, delivery_estimate_days: event.target.value })}
                  />
                </Field>
              </div>

              <Field label="Paste visible page text, competitor notes, reviews, supplier terms, or anything you copied">
                <div className="mb-2 flex flex-wrap gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => appendNotes(SUPPLIER_CHECK_TEMPLATE)}
                  >
                    Add 1688 supplier check
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => appendNotes(WATER_PUMP_TEMPLATE)}
                  >
                    Add water pump quality checklist
                  </Button>
                </div>
                <Textarea
                  className="min-h-[170px]"
                  placeholder="Paste copied product details here. For 1688, copy title, price, MOQ, supplier name, years/rating, specs, shipping notes, and any images/spec text you can see."
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

              <Button
                onClick={analyze}
                disabled={loading || !form.url.trim()}
                className="h-11 w-full bg-indigo-600 text-white hover:bg-indigo-700"
              >
                {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Sparkles className="mr-2 h-4 w-4" />}
                Verify Product
              </Button>
            </CardContent>
          </Card>
        </section>

        <aside className="space-y-4">
          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <ClipboardCheck className="h-5 w-5 text-indigo-600" />
                Decision
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {!result ? (
                <div className="space-y-3 text-sm text-slate-600">
                  <p>The result will show a direct verdict, not just raw data.</p>
                  <ChecklistItem text="Should I work on this product?" />
                  <ChecklistItem text="What proof is missing?" />
                  <ChecklistItem text="What should I ask the supplier?" />
                  <ChecklistItem text="What is the next action?" />
                </div>
              ) : (
                <>
                  <div className="space-y-2">
                    <Badge variant={verdictVariant}>{decision}</Badge>
                    <h2 className="text-xl font-bold text-slate-950">{result.name}</h2>
                    <p className="text-sm text-slate-600">{result.recommendation.reason}</p>
                    <a
                      href={result.url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-sm text-indigo-600"
                    >
                      Open source link
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <Metric label="Margin" value={`${result.financials.contribution_margin_after_advertising || "0"}%`} />
                    <Metric label="Net/unit" value={`$${result.financials.net_per_unit_before_fixed || "0"}`} />
                  </div>

                  <VerdictList title="Why" items={result.recommendation.why} icon={CheckCircle2} />
                  <VerdictList title="Risks" items={result.recommendation.risks} icon={AlertCircle} />
                  <VerdictList title="Missing Proof" items={result.recommendation.missing_proof} icon={HelpCircle} />
                  <VerdictList title="Next Steps" items={result.recommendation.next_steps} icon={Package} />
                  <VerdictList title="Ask Supplier" items={result.recommendation.supplier_questions} icon={Truck} />

                  {result.recommendation.positioning_angle && (
                    <div className="rounded-lg bg-slate-50 p-3 text-sm">
                      <p className="font-semibold text-slate-900">Positioning angle</p>
                      <p className="mt-1 text-slate-600">{result.recommendation.positioning_angle}</p>
                    </div>
                  )}

                  {result.product_id && (
                    <Button asChild variant="outline" className="w-full">
                      <a href={`/products/${result.product_id}`}>
                        <Save className="mr-2 h-4 w-4" />
                        View Saved Product
                      </a>
                    </Button>
                  )}
                </>
              )}
            </CardContent>
          </Card>

          <Card className="border-amber-200 bg-amber-50 shadow-sm">
            <CardContent className="space-y-2 p-4 text-sm text-amber-900">
              <p className="font-semibold">Best workflow</p>
              <p>For blocked sites like 1688: paste the link, click the checklist button, then fill only the facts you can see from the page.</p>
              <Separator className="bg-amber-200" />
              <p>The app will judge the supplier from your evidence and tell you what is missing before you order samples.</p>
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  const id = useId();
  const control = isValidElement<{ id?: string }>(children)
    ? cloneElement(children, { id: children.props.id || id })
    : children;

  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="text-sm font-medium text-slate-700">{label}</label>
      {control}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-50 p-3">
      <p className="text-[11px] font-semibold uppercase text-slate-400">{label}</p>
      <p className="mt-1 font-bold text-slate-950">{value}</p>
    </div>
  );
}

function ChecklistItem({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-2">
      <CheckCircle2 className="h-4 w-4 text-emerald-500" />
      <span>{text}</span>
    </div>
  );
}

function VerdictList({
  title,
  items,
  icon: Icon,
}: {
  title: string;
  items?: string[];
  icon: typeof CheckCircle2;
}) {
  if (!items || items.length === 0) return null;
  return (
    <div className="space-y-2">
      <p className="flex items-center gap-2 text-sm font-semibold text-slate-900">
        <Icon className="h-4 w-4 text-indigo-600" />
        {title}
      </p>
      <ul className="space-y-1.5 text-sm text-slate-600">
        {items.map((item) => (
          <li key={item} className="rounded-lg bg-slate-50 px-3 py-2">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

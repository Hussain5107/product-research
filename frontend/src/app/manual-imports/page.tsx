"use client";

import { useState } from "react";
import { CheckCircle, Database, FileJson, FileSpreadsheet, Upload } from "lucide-react";
import { fetchApi } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

type ImportTarget = "products" | "suppliers";
type ImportFormat = "csv" | "json";

interface ImportResult {
  created_count: number;
  skipped_count: number;
  created: Array<{ id: number; name: string }>;
  skipped: Array<{ row: number; reason: string }>;
}

const PRODUCT_CSV = `name,category,supplier_cost,shipping_cost,suggested_retail_price,trend_classification,viral_potential,competition,source_url
Portable Mini Vacuum Cleaner,Home & Kitchen,8.50,3.20,29.99,growing,medium,low,https://example.com/product`;

const SUPPLIER_CSV = `supplier_name,platform,website_url,email,whatsapp,country,us_warehouse_capable,supports_shopify,notes
Sample Supplier,Alibaba,https://example.com,sales@example.com,+15551234567,USA,true,true,Manual lead from supplier research`;

export default function ManualImportsPage() {
  const [target, setTarget] = useState<ImportTarget>("products");
  const [format, setFormat] = useState<ImportFormat>("csv");
  const [sourceName, setSourceName] = useState("manual_import");
  const [sourceUrl, setSourceUrl] = useState("");
  const [content, setContent] = useState(PRODUCT_CSV);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);

  function changeTarget(next: ImportTarget) {
    setTarget(next);
    setContent(next === "products" ? PRODUCT_CSV : SUPPLIER_CSV);
    setResult(null);
  }

  function changeFormat(next: ImportFormat) {
    setFormat(next);
    setResult(null);
    if (next === "json") {
      setContent(
        target === "products"
          ? JSON.stringify(
              [
                {
                  name: "Portable Mini Vacuum Cleaner",
                  category: "Home & Kitchen",
                  supplier_cost: 8.5,
                  shipping_cost: 3.2,
                  suggested_retail_price: 29.99,
                  trend_classification: "growing",
                  viral_potential: "medium",
                  competition: "low",
                  source_url: "https://example.com/product",
                },
              ],
              null,
              2
            )
          : JSON.stringify(
              [
                {
                  supplier_name: "Sample Supplier",
                  platform: "Alibaba",
                  website_url: "https://example.com",
                  email: "sales@example.com",
                  whatsapp: "+15551234567",
                  country: "USA",
                  us_warehouse_capable: true,
                  supports_shopify: true,
                  notes: "Manual lead from supplier research",
                },
              ],
              null,
              2
            )
      );
    } else {
      setContent(target === "products" ? PRODUCT_CSV : SUPPLIER_CSV);
    }
  }

  async function runImport() {
    setLoading(true);
    setResult(null);
    try {
      const data = await fetchApi<ImportResult>(`/imports/${target}`, {
        method: "POST",
        body: JSON.stringify({
          format,
          content,
          source_name: sourceName || "manual_import",
          source_url: sourceUrl || null,
        }),
      });
      setResult(data);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="-m-6 min-h-full bg-slate-50 p-4 text-slate-950 md:p-6">
      <div className="mx-auto max-w-[1200px] space-y-4">
        <section className="rounded-2xl border border-indigo-100 bg-gradient-to-br from-white via-indigo-50 to-sky-50 p-6 shadow-sm">
          <Badge className="bg-indigo-100 text-indigo-700 hover:bg-indigo-100">Manual Imports</Badge>
          <h1 className="mt-3 text-3xl font-bold tracking-tight md:text-4xl">
            Import product candidates and supplier leads
          </h1>
          <p className="mt-2 max-w-3xl text-slate-600">
            Paste CSV or JSON from your own research, supplier lists, product webpages, or spreadsheets.
            Imported records are marked as user supplied with source details.
          </p>
        </section>

        <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Upload className="h-5 w-5 text-indigo-600" />
                Import Data
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3 md:grid-cols-2">
                <Segmented
                  label="Import target"
                  value={target}
                  options={[
                    { value: "products", label: "Products" },
                    { value: "suppliers", label: "Suppliers" },
                  ]}
                  onChange={(value) => changeTarget(value as ImportTarget)}
                />
                <Segmented
                  label="Format"
                  value={format}
                  options={[
                    { value: "csv", label: "CSV" },
                    { value: "json", label: "JSON" },
                  ]}
                  onChange={(value) => changeFormat(value as ImportFormat)}
                />
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <Input
                  placeholder="Source name e.g. Alibaba research list"
                  value={sourceName}
                  onChange={(event) => setSourceName(event.target.value)}
                />
                <Input
                  placeholder="Source URL optional"
                  value={sourceUrl}
                  onChange={(event) => setSourceUrl(event.target.value)}
                />
              </div>

              <Textarea
                value={content}
                onChange={(event) => setContent(event.target.value)}
                className="min-h-[360px] font-mono text-sm"
              />

              <Button
                onClick={runImport}
                disabled={loading || !content.trim()}
                className="w-full bg-indigo-600 text-white hover:bg-indigo-700"
              >
                <Database className="mr-2 h-4 w-4" />
                {loading ? "Importing..." : `Import ${target}`}
              </Button>
            </CardContent>
          </Card>

          <aside className="space-y-4">
            <Card className="border-slate-200 bg-white shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  {format === "csv" ? (
                    <FileSpreadsheet className="h-5 w-5 text-emerald-600" />
                  ) : (
                    <FileJson className="h-5 w-5 text-sky-600" />
                  )}
                  Expected Fields
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-slate-600">
                {target === "products" ? (
                  <>
                    <Field name="name" required />
                    <Field name="category" />
                    <Field name="supplier_cost" />
                    <Field name="shipping_cost" />
                    <Field name="suggested_retail_price" />
                    <Field name="source_url" />
                  </>
                ) : (
                  <>
                    <Field name="supplier_name" required />
                    <Field name="platform" />
                    <Field name="website_url" />
                    <Field name="email" />
                    <Field name="whatsapp" />
                    <Field name="us_warehouse_capable" />
                  </>
                )}
              </CardContent>
            </Card>

            <Card className="border-slate-200 bg-white shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <CheckCircle className="h-5 w-5 text-emerald-600" />
                  Import Result
                </CardTitle>
              </CardHeader>
              <CardContent>
                {!result ? (
                  <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">
                    Import results will appear here.
                  </p>
                ) : (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-2">
                      <Metric label="Created" value={String(result.created_count)} />
                      <Metric label="Skipped" value={String(result.skipped_count)} />
                    </div>
                    <div className="space-y-2">
                      {result.created.slice(0, 8).map((item) => (
                        <div key={`${item.id}-${item.name}`} className="rounded-lg bg-emerald-50 px-3 py-2 text-sm">
                          {item.name}
                        </div>
                      ))}
                    </div>
                    {result.skipped.length > 0 && (
                      <div className="space-y-2">
                        {result.skipped.map((item) => (
                          <div key={`${item.row}-${item.reason}`} className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
                            Row {item.row}: {item.reason}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </aside>
        </div>
      </div>
    </div>
  );
}

function Segmented({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: Array<{ value: string; label: string }>;
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-2">
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <div className="grid grid-cols-2 gap-2 rounded-xl bg-slate-100 p-1">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={
              value === option.value
                ? "rounded-lg bg-white px-3 py-2 text-sm font-semibold text-indigo-700 shadow-sm"
                : "rounded-lg px-3 py-2 text-sm font-medium text-slate-600"
            }
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function Field({ name, required = false }: { name: string; required?: boolean }) {
  return (
    <div className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2">
      <code className="text-xs text-slate-700">{name}</code>
      {required && <Badge variant="warning">Required</Badge>}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-slate-50 p-3">
      <p className="text-xs font-medium uppercase text-slate-400">{label}</p>
      <p className="mt-1 text-2xl font-bold text-slate-950">{value}</p>
    </div>
  );
}

"use client";

import { useState } from "react";
import { Calculator, Tag, TrendingUp, AlertCircle, RefreshCw } from "lucide-react";
import { fetchApi } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";

interface SensitivityRow {
  cac: string;
  contribution_after_advertising: string;
  contribution_margin_after_advertising: string;
}

interface CalcResult {
  landed_cost: string;
  variable_cost: string;
  profit_per_unit: string;
  margin_percent: string;
  break_even_cac: string;
  break_even_roas: string | null;
  sensitivity: SensitivityRow[];
}

interface SavedProduct {
  id: number;
  name: string;
  category?: string | null;
  supplier_cost: string;
  shipping_cost: string;
  suggested_retail_price: string;
  status: string;
  created_at: string | null;
}

const DEFAULTS = {
  supplierCost: 4.5,
  shippingCost: 1.2,
  packagingCost: 0.5,
  otherCost: 0,
  sellingPrice: 20,
  marketplaceFeeRate: 0,
  marketplaceFeeFixed: 0,
  paymentFeeRate: 0.029,
  paymentFeeFixed: 0.3,
  expectedReturnRate: 0.05,
  adCostCac: 5,
};

export default function ProfitCalculatorPage() {
  const [inputs, setInputs] = useState(DEFAULTS);
  const [saved, setSaved] = useState<SavedProduct[]>([]);
  const [result, setResult] = useState<CalcResult | null>(null);
  const [savedOpen, setSavedOpen] = useState(true);
  const [saving, setSaving] = useState(false);

  async function calc() {
    const body = {
      supplier_cost: Number(inputs.supplierCost || 0),
      shipping_cost: Number(inputs.shippingCost || 0),
      packaging_cost: Number(inputs.packagingCost || 0),
      other_cost: Number(inputs.otherCost || 0),
      selling_price: Number(inputs.sellingPrice || 0),
      marketplace_fee_rate: Number(inputs.marketplaceFeeRate || 0),
      marketplace_fee_fixed: Number(inputs.marketplaceFeeFixed || 0),
      payment_fee_rate: Number(inputs.paymentFeeRate || 0),
      payment_fee_fixed: Number(inputs.paymentFeeFixed || 0),
      expected_return_rate: Number(inputs.expectedReturnRate || 0),
      ad_cost_cac: Number(inputs.adCostCac || 0),
    };
    setResult(await fetchApi<CalcResult>("/profit-calculator/", { method: "POST", body: JSON.stringify(body) }));
  }

  async function refreshSaved() {
    setSaved(await fetchApi<SavedProduct[]>("/profit-calculator/list"));
  }

  async function save() {
    if (!result) return;
    setSaving(true);
    try {
      const body = {
        product_name: saved.length > 0 ? saved[0].name : "Manual profit calculation",
        supplier_cost: Number(inputs.supplierCost || 0),
        shipping_cost: Number(inputs.shippingCost || 0),
        packaging_cost: Number(inputs.packagingCost || 0),
        other_cost: Number(inputs.otherCost || 0),
        selling_price: Number(inputs.sellingPrice || 0),
        marketplace_fee_rate: Number(inputs.marketplaceFeeRate || 0),
        payment_fee_rate: Number(inputs.paymentFeeRate || 0),
        payment_fee_fixed: Number(inputs.paymentFeeFixed || 0),
        expected_return_rate: Number(inputs.expectedReturnRate || 0),
        ad_cost_cac: Number(inputs.adCostCac || 0),
        result,
      };
      await fetchApi("/profit-calculator/save", { method: "POST", body: JSON.stringify(body) });
      await refreshSaved();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="-m-6 min-h-full bg-slate-50 p-4 text-slate-950 md:p-6">
      <div className="mx-auto max-w-[1200px] space-y-4">
        <section className="rounded-2xl border border-indigo-100 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Profit Calculator</h1>
              <p className="mt-1 text-slate-600">Local deterministic calculations. No paid API required.</p>
            </div>
            <Button variant="outline" size="sm" onClick={refreshSaved}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh saved
            </Button>
          </div>
        </section>

        <div className="grid gap-4 lg:grid-cols-[1fr_340px]">
          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Calculator className="h-5 w-5 text-indigo-600" />
                Inputs
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600">Landed cost split</label>
                  <Input type="number" min={0} step={0.01} placeholder="0.00" value={inputs.supplierCost} onChange={(e) => setInputs({ ...inputs, supplierCost: Number(e.target.value) })} />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600">Shipping</label>
                  <Input type="number" min={0} step={0.01} placeholder="0.00" value={inputs.shippingCost} onChange={(e) => setInputs({ ...inputs, shippingCost: Number(e.target.value) })} />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600">Packaging</label>
                  <Input type="number" min={0} step={0.01} placeholder="0.00" value={inputs.packagingCost} onChange={(e) => setInputs({ ...inputs, packagingCost: Number(e.target.value) })} />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600">Other cost</label>
                  <Input type="number" min={0} step={0.01} placeholder="0.00" value={inputs.otherCost} onChange={(e) => setInputs({ ...inputs, otherCost: Number(e.target.value) })} />
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600">Selling price ($)</label>
                  <Input type="number" min={0} step={0.01} placeholder="0.00" value={inputs.sellingPrice} onChange={(e) => setInputs({ ...inputs, sellingPrice: Number(e.target.value) })} />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600">Marketplace fee %</label>
                  <Input type="number" min={0} step={0.01} placeholder="0.00" value={inputs.marketplaceFeeRate} onChange={(e) => setInputs({ ...inputs, marketplaceFeeRate: Number(e.target.value) })} />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600">Marketplace fee $ fixed</label>
                  <Input type="number" min={0} step={0.01} placeholder="0.00" value={inputs.marketplaceFeeFixed} onChange={(e) => setInputs({ ...inputs, marketplaceFeeFixed: Number(e.target.value) })} />
                </div>
              </div>

              <Separator />

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600">Payment fee %</label>
                  <Input type="number" min={0} step={0.001} placeholder="2.90%" value={inputs.paymentFeeRate} onChange={(e) => setInputs({ ...inputs, paymentFeeRate: Number(e.target.value) })} />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600">Payment fee $ fixed</label>
                  <Input type="number" min={0} step={0.01} placeholder="0.30" value={inputs.paymentFeeFixed} onChange={(e) => setInputs({ ...inputs, paymentFeeFixed: Number(e.target.value) })} />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600">Expected return %</label>
                  <Input type="number" min={0} step={0.001} placeholder="5.00%" value={inputs.expectedReturnRate} onChange={(e) => setInputs({ ...inputs, expectedReturnRate: Number(e.target.value) })} />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600">Ad cost / CAC ($)</label>
                  <Input type="number" min={0} step={0.01} placeholder="0.00" value={inputs.adCostCac} onChange={(e) => setInputs({ ...inputs, adCostCac: Number(e.target.value) })} />
                </div>
              </div>

              <Button onClick={calc} className="w-full bg-indigo-600 text-white hover:bg-indigo-700">
                <RefreshCw className="mr-2 h-4 w-4" />
                Calculate
              </Button>
            </CardContent>
          </Card>

          <aside className="space-y-4">
            <Card className="border-slate-200 bg-white shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg">Results</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {result ? (
                  <>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <Metric label="Landed cost" value={`$${Number(result.landed_cost).toFixed(2)}`} />
                      <Metric label="Variable cost" value={`$${Number(result.variable_cost).toFixed(2)}`} />
                      <Metric label="Profit / unit" value={`$${Number(result.profit_per_unit).toFixed(2)}`} />
                      <Metric label="Margin %" value={`${Number(result.margin_percent).toFixed(2)}%`} />
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <Metric label="Break-even CAC" value={`$${Number(result.break_even_cac).toFixed(2)}`} />
                      <Metric label="Break-even ROAS" value={result.break_even_roas ? `$${Number(result.break_even_roas).toFixed(2)}` : "n/a"} />
                    </div>
                    <div className="mt-3">
                      <p className="text-xs font-medium uppercase text-slate-400">Sensitivity: ad cost / CAC</p>
                      <div className="space-y-1 text-xs">
                        {result.sensitivity.map((s) => (
                          <div key={s.cac} className="flex justify-between">
                            <span>${Number(s.cac).toFixed(2)}</span>
                            <span className="font-medium text-slate-900">{Number(s.contribution_margin_after_advertising).toFixed(2)}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <Button onClick={save} className="w-full" disabled={saving}>
                      {saving ? "Saving..." : "Save to history"}
                    </Button>
                  </>
                ) : (
                  <p className="text-sm text-slate-500">Enter costs and selling price, then click Calculate.</p>
                )}
              </CardContent>
            </Card>

            <Card className="border-slate-200 bg-white shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg">Saved history ({saved.length})</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                {saved.map((p) => (
                  <div key={p.id} className="rounded-xl bg-slate-50 p-2">
                    <p className="font-medium text-slate-900">{p.name}</p>
                    <p className="text-xs text-slate-500">{p.category || "N/A"} · {new Date(p.created_at || "").toLocaleDateString()}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          </aside>
        </div>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-slate-50 p-3">
      <p className="text-xs font-medium uppercase text-slate-400">{label}</p>
      <p className="mt-1 font-semibold text-slate-900">{value}</p>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, ExternalLink, Factory, Package, TrendingUp } from "lucide-react";
import { fetchApi } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ProductDetail {
  id: number;
  name: string;
  description?: string | null;
  category?: string | null;
  brand?: string | null;
  product_url?: string | null;
  image_url?: string | null;
  supplier_cost: string;
  shipping_cost: string;
  suggested_retail_price: string;
  trend_classification: string;
  viral_potential: string;
  primary_competition_level: string;
  status: string;
  region_code?: string | null;
  suppliers: Array<{
    id: number;
    supplier_name?: string | null;
    supplier_platform?: string | null;
    supplier_url?: string | null;
    supplier_product_url?: string | null;
    purchase_cost: string;
    shipping_cost: string;
    processing_fee?: string;
    currency_code: string;
    warehouse_origin?: string | null;
    warehouse_verified: boolean;
    warehouse_verification_status?: string;
    warehouse_verification_note?: string | null;
    stock_available: boolean;
    stock_quantity?: string | null;
    processing_time_days?: number | null;
    delivery_estimate_days?: number | null;
    shipping_service?: string | null;
    destination_zip?: string | null;
    evidence_status?: string;
    verification_timestamp?: string | null;
    supports_returns?: boolean;
    return_policy_note?: string | null;
    us_warehouse_capable?: boolean;
    us_warehouse_note?: string | null;
    reliability_status?: string;
    reliability_note?: string | null;
  }>;
  sources: Array<{
    id: number;
    source_name: string;
    source_url?: string | null;
    data_classification: string;
    raw_value?: string | null;
    notes?: string | null;
    retrieval_timestamp?: string | null;
  }>;
}

export default function ProductDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [product, setProduct] = useState<ProductDetail | null>(null);

  useEffect(() => {
    if (!params.id) return;
    fetchApi<ProductDetail>(`/products/detail/${params.id}`)
      .then(setProduct)
      .catch((error) => console.error("Product detail load failed", error));
  }, [params.id]);

  if (!product) {
    return (
      <div className="-m-6 min-h-full bg-slate-50 p-6 text-slate-950">
        <p className="rounded-xl bg-white p-4 text-sm text-slate-500">Loading product...</p>
      </div>
    );
  }

  return (
    <div className="-m-6 min-h-full bg-slate-50 p-4 text-slate-950 md:p-6">
      <div className="mx-auto max-w-[1200px] space-y-4">
        <Button variant="ghost" onClick={() => router.push("/discovery")} className="text-slate-600">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Product Finder
        </Button>

        <section className="grid gap-4 lg:grid-cols-[360px_1fr]">
          <Card className="border-slate-200 bg-white shadow-sm">
            <CardContent className="p-4">
              <div className="aspect-square overflow-hidden rounded-xl bg-slate-50">
                {product.image_url ? (
                  <img src={product.image_url} alt={product.name} className="h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full items-center justify-center">
                    <Package className="h-16 w-16 text-indigo-300" />
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <div className="flex flex-wrap gap-2">
                <Badge variant="secondary">{product.status}</Badge>
                <Badge variant={product.viral_potential === "high" ? "warning" : "secondary"}>
                  {product.viral_potential} viral potential
                </Badge>
              </div>
              <CardTitle className="text-3xl">{product.name}</CardTitle>
              <p className="text-sm text-slate-500">{product.category || "Uncategorized"}</p>
            </CardHeader>
            <CardContent className="space-y-4">
              {product.description && <p className="text-slate-600">{product.description}</p>}
              <div className="grid gap-3 sm:grid-cols-4">
                <Metric label="Supplier cost" value={`$${Number(product.supplier_cost).toFixed(2)}`} />
                <Metric label="Shipping" value={`$${Number(product.shipping_cost).toFixed(2)}`} />
                <Metric label="Selling price" value={`$${Number(product.suggested_retail_price).toFixed(2)}`} />
                <Metric label="Competition" value={product.primary_competition_level} />
              </div>
              {product.product_url && (
                <Button asChild className="bg-indigo-600 text-white hover:bg-indigo-700">
                  <a href={product.product_url} target="_blank" rel="noreferrer">
                    Open Source
                    <ExternalLink className="ml-2 h-4 w-4" />
                  </a>
                </Button>
              )}
            </CardContent>
          </Card>
        </section>

        <div className="grid gap-4 lg:grid-cols-2">
          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Factory className="h-5 w-5 text-indigo-600" />
                Supplier Offers
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {product.suppliers.length === 0 ? (
                <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">No supplier offers linked yet.</p>
              ) : (
                product.suppliers.map((supplier) => (
                  <div key={supplier.id} className="rounded-xl bg-slate-50 p-3">
                    <p className="font-semibold">{supplier.supplier_name}</p>
                    <p className="text-sm text-slate-500">
                      {supplier.currency_code} {Number(supplier.purchase_cost).toFixed(2)} cost,
                      {" "}{supplier.delivery_estimate_days ?? "unknown"} delivery days
                    </p>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <TrendingUp className="h-5 w-5 text-emerald-600" />
                Evidence Sources
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {product.sources.length === 0 ? (
                <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">No evidence sources attached yet.</p>
              ) : (
                product.sources.map((source) => (
                  <div key={source.id} className="rounded-xl bg-slate-50 p-3">
                    <p className="font-semibold">{source.source_name}</p>
                    <p className="text-sm text-slate-500">{source.data_classification}</p>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
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

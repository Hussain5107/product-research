"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchApi } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Building2,
  BarChart3,
  CheckCircle,
  DollarSign,
  ExternalLink,
  Factory,
  Mail,
  MessageCircle,
  PackageSearch,
  Plus,
  RefreshCcw,
  Send,
  ShieldCheck,
  Truck,
} from "lucide-react";

interface Supplier {
  id: number;
  name: string;
  platform: string;
  website_url?: string | null;
  supports_shopify: boolean;
  us_warehouse_capable: boolean;
  reliability_status: string;
  contact_count: number;
  outreach_count: number;
}

interface SupplierDetail extends Supplier {
  contacts: SupplierContact[];
  outreach: OutreachDraft[];
  supplier_products: SupplierProduct[];
}

interface SupplierContact {
  id: number;
  contact_name?: string | null;
  role_title?: string | null;
  email?: string | null;
  whatsapp?: string | null;
  phone?: string | null;
  country?: string | null;
  verification_status: string;
}

interface OutreachDraft {
  id: number;
  channel: string;
  status: string;
  subject?: string | null;
  message_body: string;
  negotiation_goal?: string | null;
}

interface SupplierProduct {
  id: number;
  supplier_id: number;
  supplier_name?: string | null;
  supplier_platform?: string | null;
  supplier_product_name?: string | null;
  supplier_product_url?: string | null;
  purchase_cost: number;
  shipping_cost: number;
  processing_fee: number;
  total_landed_cost: number;
  currency_code: string;
  warehouse_origin?: string | null;
  warehouse_verified: boolean;
  stock_available: boolean;
  stock_quantity?: string | null;
  delivery_estimate_days?: number | null;
  shipping_service?: string | null;
  evidence_status: string;
  recommendation_score: number;
  recommendation_reasons: string[];
}

interface SupplierComparison {
  count: number;
  recommended: SupplierProduct | null;
  products: SupplierProduct[];
}

export default function SupplierFinderPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selected, setSelected] = useState<SupplierDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [drafting, setDrafting] = useState(false);
  const [comparison, setComparison] = useState<SupplierComparison | null>(null);
  const [supplierForm, setSupplierForm] = useState({
    name: "",
    platform: "manual_entry",
    website_url: "",
    us_warehouse_capable: false,
    supports_shopify: true,
    reliability_note: "",
  });
  const [contactForm, setContactForm] = useState({
    contact_name: "",
    role_title: "",
    email: "",
    whatsapp: "",
    phone: "",
    country: "",
    source_url: "",
    notes: "",
  });
  const [productForm, setProductForm] = useState({
    supplier_product_name: "",
    supplier_product_url: "",
    purchase_cost: "0",
    shipping_cost: "0",
    processing_fee: "0",
    currency_code: "USD",
    warehouse_origin: "",
    warehouse_verified: false,
    stock_available: false,
    stock_quantity: "",
    delivery_estimate_days: "",
    shipping_service: "",
  });
  const [comparisonQuery, setComparisonQuery] = useState("");
  const [goal, setGoal] = useState(
    "negotiate product cost, sample order, MOQ, US warehouse availability, and shipping time"
  );

  const selectedSupplier = useMemo(
    () => suppliers.find((supplier) => supplier.id === selectedId) || null,
    [selectedId, suppliers]
  );

  useEffect(() => {
    loadSuppliers();
    loadComparison();
  }, []);

  useEffect(() => {
    if (selectedId) {
      loadSupplier(selectedId);
    } else {
      setSelected(null);
    }
  }, [selectedId]);

  async function loadSuppliers() {
    setLoading(true);
    try {
      const data = await fetchApi<Supplier[]>("/suppliers/list");
      setSuppliers(data);
      if (!selectedId && data.length > 0) {
        setSelectedId(data[0].id);
      }
    } finally {
      setLoading(false);
    }
  }

  async function loadSupplier(id: number) {
    const data = await fetchApi<SupplierDetail>(`/suppliers/${id}`);
    setSelected(data);
  }

  async function createSupplier() {
    if (!supplierForm.name.trim()) return;
    setCreating(true);
    try {
      const supplier = await fetchApi<Supplier>("/suppliers/create", {
        method: "POST",
        body: JSON.stringify({
          ...supplierForm,
          website_url: supplierForm.website_url || null,
          reliability_note: supplierForm.reliability_note || null,
        }),
      });
      setSupplierForm({
        name: "",
        platform: "manual_entry",
        website_url: "",
        us_warehouse_capable: false,
        supports_shopify: true,
        reliability_note: "",
      });
      await loadSuppliers();
      setSelectedId(supplier.id);
    } finally {
      setCreating(false);
    }
  }

  async function addContact() {
    if (!selectedId) return;
    if (!contactForm.email && !contactForm.whatsapp && !contactForm.phone) return;
    await fetchApi(`/suppliers/${selectedId}/contacts`, {
      method: "POST",
      body: JSON.stringify({
        ...contactForm,
        source_url: contactForm.source_url || null,
        data_classification: "user_supplied",
        verification_status: "unverified",
      }),
    });
    setContactForm({
      contact_name: "",
      role_title: "",
      email: "",
      whatsapp: "",
      phone: "",
      country: "",
      source_url: "",
      notes: "",
    });
    await loadSupplier(selectedId);
    await loadSuppliers();
  }

  async function createDraft() {
    if (!selectedId) return;
    setDrafting(true);
    try {
      await fetchApi(`/suppliers/${selectedId}/outreach/draft`, {
        method: "POST",
        body: JSON.stringify({
          channel: "email",
          negotiation_goal: goal,
          contact_id: selected?.contacts?.[0]?.id ?? null,
          requested_terms: {
            product_catalog: true,
            unit_cost: true,
            moq: true,
            us_warehouse: true,
            sample_price: true,
            delivery_time: true,
          },
        }),
      });
      await loadSupplier(selectedId);
      await loadSuppliers();
    } finally {
      setDrafting(false);
    }
  }

  async function addSupplierProduct() {
    if (!selectedId) return;
    if (!productForm.supplier_product_name.trim()) return;
    await fetchApi(`/suppliers/${selectedId}/products`, {
      method: "POST",
      body: JSON.stringify({
        supplier_product_name: productForm.supplier_product_name,
        supplier_product_url: productForm.supplier_product_url || null,
        purchase_cost: Number(productForm.purchase_cost || 0),
        shipping_cost: Number(productForm.shipping_cost || 0),
        processing_fee: Number(productForm.processing_fee || 0),
        currency_code: productForm.currency_code || "USD",
        warehouse_origin: productForm.warehouse_origin || null,
        warehouse_verified: productForm.warehouse_verified,
        stock_available: productForm.stock_available,
        stock_quantity: productForm.stock_quantity || null,
        delivery_estimate_days: productForm.delivery_estimate_days
          ? Number(productForm.delivery_estimate_days)
          : null,
        shipping_service: productForm.shipping_service || null,
        evidence_status: "user_supplied",
      }),
    });
    setProductForm({
      supplier_product_name: "",
      supplier_product_url: "",
      purchase_cost: "0",
      shipping_cost: "0",
      processing_fee: "0",
      currency_code: "USD",
      warehouse_origin: "",
      warehouse_verified: false,
      stock_available: false,
      stock_quantity: "",
      delivery_estimate_days: "",
      shipping_service: "",
    });
    await loadSupplier(selectedId);
    await loadComparison();
  }

  async function loadComparison() {
    const query = comparisonQuery.trim()
      ? `?product_query=${encodeURIComponent(comparisonQuery.trim())}`
      : "";
    const data = await fetchApi<SupplierComparison>(`/suppliers/products/compare${query}`);
    setComparison(data);
  }

  return (
    <div className="-m-6 min-h-full bg-slate-50 p-4 text-slate-950 md:p-6">
      <div className="mx-auto max-w-[1500px] space-y-4">
        <section className="rounded-2xl border border-indigo-100 bg-gradient-to-br from-white via-indigo-50 to-sky-50 p-6 shadow-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <Badge className="bg-indigo-100 text-indigo-700 hover:bg-indigo-100">
                Supplier Finder
              </Badge>
              <h1 className="mt-3 text-3xl font-bold tracking-tight md:text-4xl">
                Build supplier leads, contacts, and negotiation drafts
              </h1>
              <p className="mt-2 max-w-3xl text-slate-600">
                Store supplier details from CJdropshipping, Zendrop, Spocket, Alibaba,
                AliExpress, US wholesalers, manufacturers, and manual web research.
              </p>
            </div>
            <div className="grid gap-2 sm:grid-cols-3">
              <Metric icon={Factory} label="Suppliers" value={String(suppliers.length)} />
              <Metric
                icon={MessageCircle}
                label="Contacts"
                value={String(suppliers.reduce((total, item) => total + item.contact_count, 0))}
              />
              <Metric
                icon={Mail}
                label="Drafts"
                value={String(suppliers.reduce((total, item) => total + item.outreach_count, 0))}
              />
            </div>
          </div>
        </section>

        <div className="grid gap-4 xl:grid-cols-[420px_1fr]">
          <section className="space-y-4">
            <Card className="border-slate-200 bg-white shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Plus className="h-5 w-5 text-indigo-600" />
                  Add Supplier Lead
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Input
                  placeholder="Supplier name"
                  value={supplierForm.name}
                  onChange={(event) => setSupplierForm({ ...supplierForm, name: event.target.value })}
                />
                <div className="grid gap-3 sm:grid-cols-2">
                  <Input
                    placeholder="Platform e.g. Alibaba, Zendrop"
                    value={supplierForm.platform}
                    onChange={(event) =>
                      setSupplierForm({ ...supplierForm, platform: event.target.value })
                    }
                  />
                  <Input
                    placeholder="Website URL"
                    value={supplierForm.website_url}
                    onChange={(event) =>
                      setSupplierForm({ ...supplierForm, website_url: event.target.value })
                    }
                  />
                </div>
                <Textarea
                  placeholder="Reliability notes, warehouse notes, product fit..."
                  value={supplierForm.reliability_note}
                  onChange={(event) =>
                    setSupplierForm({ ...supplierForm, reliability_note: event.target.value })
                  }
                />
                <div className="grid gap-2 sm:grid-cols-2">
                  <label className="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-sm">
                    <input
                      type="checkbox"
                      checked={supplierForm.supports_shopify}
                      onChange={(event) =>
                        setSupplierForm({ ...supplierForm, supports_shopify: event.target.checked })
                      }
                    />
                    Shopify capable
                  </label>
                  <label className="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-sm">
                    <input
                      type="checkbox"
                      checked={supplierForm.us_warehouse_capable}
                      onChange={(event) =>
                        setSupplierForm({
                          ...supplierForm,
                          us_warehouse_capable: event.target.checked,
                        })
                      }
                    />
                    US warehouse
                  </label>
                </div>
                <Button
                  onClick={createSupplier}
                  disabled={creating || !supplierForm.name.trim()}
                  className="w-full bg-indigo-600 text-white hover:bg-indigo-700"
                >
                  {creating ? <RefreshCcw className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
                  Save Supplier
                </Button>
              </CardContent>
            </Card>

            <Card className="border-slate-200 bg-white shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center justify-between text-lg">
                  <span className="flex items-center gap-2">
                    <PackageSearch className="h-5 w-5 text-indigo-600" />
                    Supplier Leads
                  </span>
                  <Button variant="ghost" size="icon" onClick={loadSuppliers}>
                    <RefreshCcw className={loading ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {suppliers.length === 0 ? (
                  <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">
                    No supplier leads yet. Add your first supplier above.
                  </p>
                ) : (
                  suppliers.map((supplier) => (
                    <button
                      key={supplier.id}
                      onClick={() => setSelectedId(supplier.id)}
                      className={
                        selectedId === supplier.id
                          ? "w-full rounded-xl border border-indigo-200 bg-indigo-50 p-3 text-left"
                          : "w-full rounded-xl border border-slate-100 bg-slate-50 p-3 text-left hover:bg-indigo-50"
                      }
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-semibold text-slate-950">{supplier.name}</p>
                          <p className="text-xs text-slate-500">{supplier.platform}</p>
                        </div>
                        <Badge variant={supplier.us_warehouse_capable ? "success" : "secondary"}>
                          {supplier.us_warehouse_capable ? "US capable" : "Unverified"}
                        </Badge>
                      </div>
                      <div className="mt-2 flex gap-2 text-xs text-slate-500">
                        <span>{supplier.contact_count} contacts</span>
                        <span>{supplier.outreach_count} drafts</span>
                      </div>
                    </button>
                  ))
                )}
              </CardContent>
            </Card>
          </section>

          <section className="space-y-4">
            <Card className="border-slate-200 bg-white shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Building2 className="h-5 w-5 text-indigo-600" />
                  Selected Supplier
                </CardTitle>
              </CardHeader>
              <CardContent>
                {!selectedSupplier ? (
                  <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">
                    Select or add a supplier to manage contacts and outreach.
                  </p>
                ) : (
                  <div className="space-y-4">
                    <div className="flex flex-col justify-between gap-3 rounded-xl bg-slate-50 p-4 md:flex-row md:items-start">
                      <div>
                        <h2 className="text-2xl font-bold">{selectedSupplier.name}</h2>
                        <p className="text-sm text-slate-500">{selectedSupplier.platform}</p>
                        {selectedSupplier.website_url && (
                          <a
                            href={selectedSupplier.website_url}
                            target="_blank"
                            rel="noreferrer"
                            className="mt-2 inline-flex items-center gap-1 text-sm text-indigo-600"
                          >
                            Open supplier website
                            <ExternalLink className="h-3.5 w-3.5" />
                          </a>
                        )}
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Badge variant={selectedSupplier.supports_shopify ? "success" : "secondary"}>
                          Shopify {selectedSupplier.supports_shopify ? "yes" : "unknown"}
                        </Badge>
                        <Badge variant={selectedSupplier.us_warehouse_capable ? "success" : "warning"}>
                          US warehouse {selectedSupplier.us_warehouse_capable ? "capable" : "unverified"}
                        </Badge>
                      </div>
                    </div>

                    <div className="grid gap-4 lg:grid-cols-2">
                      <Card className="border-slate-100 bg-slate-50 shadow-none">
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2 text-base">
                            <MessageCircle className="h-4 w-4 text-emerald-600" />
                            Add Contact
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          <div className="grid gap-3 sm:grid-cols-2">
                            <Input
                              placeholder="Contact name"
                              value={contactForm.contact_name}
                              onChange={(event) =>
                                setContactForm({ ...contactForm, contact_name: event.target.value })
                              }
                            />
                            <Input
                              placeholder="Role/title"
                              value={contactForm.role_title}
                              onChange={(event) =>
                                setContactForm({ ...contactForm, role_title: event.target.value })
                              }
                            />
                          </div>
                          <Input
                            placeholder="Email"
                            value={contactForm.email}
                            onChange={(event) =>
                              setContactForm({ ...contactForm, email: event.target.value })
                            }
                          />
                          <div className="grid gap-3 sm:grid-cols-2">
                            <Input
                              placeholder="WhatsApp"
                              value={contactForm.whatsapp}
                              onChange={(event) =>
                                setContactForm({ ...contactForm, whatsapp: event.target.value })
                              }
                            />
                            <Input
                              placeholder="Phone"
                              value={contactForm.phone}
                              onChange={(event) =>
                                setContactForm({ ...contactForm, phone: event.target.value })
                              }
                            />
                          </div>
                          <div className="grid gap-3 sm:grid-cols-2">
                            <Input
                              placeholder="Country"
                              value={contactForm.country}
                              onChange={(event) =>
                                setContactForm({ ...contactForm, country: event.target.value })
                              }
                            />
                            <Input
                              placeholder="Source URL"
                              value={contactForm.source_url}
                              onChange={(event) =>
                                setContactForm({ ...contactForm, source_url: event.target.value })
                              }
                            />
                          </div>
                          <Textarea
                            placeholder="Contact notes"
                            value={contactForm.notes}
                            onChange={(event) =>
                              setContactForm({ ...contactForm, notes: event.target.value })
                            }
                          />
                          <Button onClick={addContact} className="w-full bg-emerald-600 text-white hover:bg-emerald-700">
                            <MessageCircle className="mr-2 h-4 w-4" />
                            Save Contact
                          </Button>
                        </CardContent>
                      </Card>

                      <Card className="border-slate-100 bg-slate-50 shadow-none">
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2 text-base">
                            <Mail className="h-4 w-4 text-indigo-600" />
                            Negotiation Draft
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          <Textarea
                            value={goal}
                            onChange={(event) => setGoal(event.target.value)}
                            className="min-h-28"
                          />
                          <Button
                            onClick={createDraft}
                            disabled={drafting}
                            className="w-full bg-indigo-600 text-white hover:bg-indigo-700"
                          >
                            {drafting ? <RefreshCcw className="mr-2 h-4 w-4 animate-spin" /> : <Send className="mr-2 h-4 w-4" />}
                            Create Draft Email
                          </Button>
                          <p className="text-xs text-slate-500">
                            Drafts are saved only inside the app. Nothing is emailed until email
                            integration and explicit send approval are added.
                          </p>
                        </CardContent>
                      </Card>

                      <Card className="border-slate-100 bg-slate-50 shadow-none lg:col-span-2">
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2 text-base">
                            <Truck className="h-4 w-4 text-sky-600" />
                            Supplier Product Offer
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          <div className="grid gap-3 lg:grid-cols-[1.4fr_1fr]">
                            <Input
                              placeholder="Product/SKU name"
                              value={productForm.supplier_product_name}
                              onChange={(event) =>
                                setProductForm({
                                  ...productForm,
                                  supplier_product_name: event.target.value,
                                })
                              }
                            />
                            <Input
                              placeholder="Product URL"
                              value={productForm.supplier_product_url}
                              onChange={(event) =>
                                setProductForm({
                                  ...productForm,
                                  supplier_product_url: event.target.value,
                                })
                              }
                            />
                          </div>
                          <div className="grid gap-3 sm:grid-cols-4">
                            <Input
                              placeholder="Unit cost"
                              type="number"
                              min="0"
                              value={productForm.purchase_cost}
                              onChange={(event) =>
                                setProductForm({ ...productForm, purchase_cost: event.target.value })
                              }
                            />
                            <Input
                              placeholder="Shipping"
                              type="number"
                              min="0"
                              value={productForm.shipping_cost}
                              onChange={(event) =>
                                setProductForm({ ...productForm, shipping_cost: event.target.value })
                              }
                            />
                            <Input
                              placeholder="Fee"
                              type="number"
                              min="0"
                              value={productForm.processing_fee}
                              onChange={(event) =>
                                setProductForm({ ...productForm, processing_fee: event.target.value })
                              }
                            />
                            <Input
                              placeholder="Currency"
                              value={productForm.currency_code}
                              onChange={(event) =>
                                setProductForm({ ...productForm, currency_code: event.target.value })
                              }
                            />
                          </div>
                          <div className="grid gap-3 sm:grid-cols-3">
                            <Input
                              placeholder="Warehouse origin"
                              value={productForm.warehouse_origin}
                              onChange={(event) =>
                                setProductForm({ ...productForm, warehouse_origin: event.target.value })
                              }
                            />
                            <Input
                              placeholder="Delivery days"
                              type="number"
                              min="0"
                              value={productForm.delivery_estimate_days}
                              onChange={(event) =>
                                setProductForm({
                                  ...productForm,
                                  delivery_estimate_days: event.target.value,
                                })
                              }
                            />
                            <Input
                              placeholder="Shipping service"
                              value={productForm.shipping_service}
                              onChange={(event) =>
                                setProductForm({ ...productForm, shipping_service: event.target.value })
                              }
                            />
                          </div>
                          <div className="grid gap-2 sm:grid-cols-3">
                            <label className="flex items-center gap-2 rounded-xl bg-white px-3 py-2 text-sm">
                              <input
                                type="checkbox"
                                checked={productForm.warehouse_verified}
                                onChange={(event) =>
                                  setProductForm({
                                    ...productForm,
                                    warehouse_verified: event.target.checked,
                                  })
                                }
                              />
                              Warehouse verified
                            </label>
                            <label className="flex items-center gap-2 rounded-xl bg-white px-3 py-2 text-sm">
                              <input
                                type="checkbox"
                                checked={productForm.stock_available}
                                onChange={(event) =>
                                  setProductForm({
                                    ...productForm,
                                    stock_available: event.target.checked,
                                  })
                                }
                              />
                              Stock available
                            </label>
                            <Input
                              placeholder="Stock quantity / MOQ"
                              value={productForm.stock_quantity}
                              onChange={(event) =>
                                setProductForm({ ...productForm, stock_quantity: event.target.value })
                              }
                            />
                          </div>
                          <Button
                            onClick={addSupplierProduct}
                            disabled={!productForm.supplier_product_name.trim()}
                            className="w-full bg-sky-600 text-white hover:bg-sky-700"
                          >
                            <DollarSign className="mr-2 h-4 w-4" />
                            Save Product Offer
                          </Button>
                        </CardContent>
                      </Card>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {selected && (
              <div className="grid gap-4 lg:grid-cols-2">
                <Card className="border-slate-200 bg-white shadow-sm lg:col-span-2">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <Truck className="h-5 w-5 text-sky-600" />
                      Product Offers From This Supplier
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {selected.supplier_products.length === 0 ? (
                      <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">
                        No product offers saved yet.
                      </p>
                    ) : (
                      selected.supplier_products.map((product) => (
                        <div key={product.id} className="rounded-xl bg-slate-50 p-3">
                          <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
                            <div>
                              <p className="font-semibold">{product.supplier_product_name}</p>
                              <p className="text-sm text-slate-500">
                                Landed cost: {product.currency_code} {product.total_landed_cost.toFixed(2)}
                              </p>
                            </div>
                            <Badge variant={product.recommendation_score >= 75 ? "success" : "secondary"}>
                              Score {product.recommendation_score}
                            </Badge>
                          </div>
                          <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-600">
                            <span>Unit {product.purchase_cost.toFixed(2)}</span>
                            <span>Ship {product.shipping_cost.toFixed(2)}</span>
                            <span>{product.delivery_estimate_days ?? "?"} days</span>
                            <span>{product.stock_available ? "In stock" : "Stock unverified"}</span>
                          </div>
                        </div>
                      ))
                    )}
                  </CardContent>
                </Card>

                <Card className="border-slate-200 bg-white shadow-sm">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <ShieldCheck className="h-5 w-5 text-emerald-600" />
                      Contacts
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {selected.contacts.length === 0 ? (
                      <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">
                        No contacts saved yet.
                      </p>
                    ) : (
                      selected.contacts.map((contact) => (
                        <div key={contact.id} className="rounded-xl bg-slate-50 p-3">
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="font-semibold">{contact.contact_name || "Unnamed contact"}</p>
                              <p className="text-xs text-slate-500">{contact.role_title || "Role unknown"}</p>
                            </div>
                            <Badge variant="secondary">{contact.verification_status}</Badge>
                          </div>
                          <div className="mt-2 space-y-1 text-sm text-slate-600">
                            {contact.email && <p>Email: {contact.email}</p>}
                            {contact.whatsapp && (
                              <p>
                                WhatsApp:{" "}
                                <a className="text-emerald-600" href={`https://wa.me/${contact.whatsapp.replace(/[^0-9]/g, "")}`} target="_blank" rel="noreferrer">
                                  {contact.whatsapp}
                                </a>
                              </p>
                            )}
                            {contact.phone && <p>Phone: {contact.phone}</p>}
                          </div>
                        </div>
                      ))
                    )}
                  </CardContent>
                </Card>

                <Card className="border-slate-200 bg-white shadow-sm">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <Mail className="h-5 w-5 text-indigo-600" />
                      Draft Outreach
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {selected.outreach.length === 0 ? (
                      <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">
                        No drafts yet.
                      </p>
                    ) : (
                      selected.outreach.map((draft) => (
                        <div key={draft.id} className="rounded-xl bg-slate-50 p-3">
                          <div className="flex items-center justify-between gap-3">
                            <p className="font-semibold">{draft.subject}</p>
                            <Badge variant="warning">{draft.status}</Badge>
                          </div>
                          <pre className="mt-3 max-h-56 overflow-auto whitespace-pre-wrap rounded-lg bg-white p-3 text-xs text-slate-700">
                            {draft.message_body}
                          </pre>
                        </div>
                      ))
                    )}
                  </CardContent>
                </Card>
              </div>
            )}

            <Card className="border-slate-200 bg-white shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <BarChart3 className="h-5 w-5 text-indigo-600" />
                  Supplier Comparison
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex flex-col gap-2 md:flex-row">
                  <Input
                    placeholder="Filter by product name"
                    value={comparisonQuery}
                    onChange={(event) => setComparisonQuery(event.target.value)}
                  />
                  <Button onClick={loadComparison} variant="outline">
                    <RefreshCcw className="mr-2 h-4 w-4" />
                    Compare
                  </Button>
                </div>
                {comparison?.recommended && (
                  <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                    <p className="text-sm font-semibold text-emerald-800">Recommended supplier offer</p>
                    <p className="mt-1 text-lg font-bold text-slate-950">
                      {comparison.recommended.supplier_name} - {comparison.recommended.supplier_product_name}
                    </p>
                    <p className="text-sm text-slate-600">
                      {comparison.recommended.currency_code} {comparison.recommended.total_landed_cost.toFixed(2)}
                      {" "}landed cost, score {comparison.recommended.recommendation_score}
                    </p>
                  </div>
                )}
                {!comparison || comparison.products.length === 0 ? (
                  <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">
                    Add supplier product offers to compare landed cost, stock, delivery, and reliability.
                  </p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[760px] text-left text-sm">
                      <thead className="text-xs uppercase text-slate-500">
                        <tr>
                          <th className="px-3 py-2">Supplier</th>
                          <th className="px-3 py-2">Product</th>
                          <th className="px-3 py-2">Landed</th>
                          <th className="px-3 py-2">Delivery</th>
                          <th className="px-3 py-2">Stock</th>
                          <th className="px-3 py-2">Score</th>
                        </tr>
                      </thead>
                      <tbody>
                        {comparison.products.map((product) => (
                          <tr key={product.id} className="border-t border-slate-100">
                            <td className="px-3 py-3 font-medium">{product.supplier_name}</td>
                            <td className="px-3 py-3">{product.supplier_product_name}</td>
                            <td className="px-3 py-3">
                              {product.currency_code} {product.total_landed_cost.toFixed(2)}
                            </td>
                            <td className="px-3 py-3">
                              {product.delivery_estimate_days ? `${product.delivery_estimate_days} days` : "Unknown"}
                            </td>
                            <td className="px-3 py-3">
                              {product.stock_available ? product.stock_quantity || "Available" : "Unverified"}
                            </td>
                            <td className="px-3 py-3">
                              <Badge variant={product.recommendation_score >= 75 ? "success" : "secondary"}>
                                {product.recommendation_score}
                              </Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>

            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
              <div className="flex gap-2">
                <CheckCircle className="mt-0.5 h-4 w-4 shrink-0" />
                <p>
                  This page stores user-supplied supplier/contact evidence and creates drafts only.
                  It does not scrape private contact data, send emails, or message WhatsApp automatically.
                </p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function Metric({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Factory;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl bg-white/80 p-3 shadow-sm">
      <div className="flex items-center gap-2 text-xs font-medium text-slate-500">
        <Icon className="h-4 w-4 text-indigo-600" />
        {label}
      </div>
      <div className="mt-1 text-2xl font-bold">{value}</div>
    </div>
  );
}

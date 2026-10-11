"use client";

import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import { fetchApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Sparkles,
  Zap,
  Package,
  Truck,
  TrendingUp,
  AlertTriangle,
  ArrowUpRight,
} from "lucide-react";
import Link from "next/link";

interface DashboardSummary {
  productsAnalyzed?: number;
  newOpportunities?: number;
  highPotentialProducts?: number;
  verifiedUSWarehouseProducts?: number;
  trendingProducts?: number;
  watchlistAlerts?: number;
  previousPeriod?: {
    productsAnalyzed?: number;
    newOpportunities?: number;
    highPotentialProducts?: number;
    verifiedUSWarehouseProducts?: number;
    trendingProducts?: number;
  };
}

interface TrendSeries {
  date: string;
  opportunityScore: number;
  verifiedProducts: number;
  trendingCandidates: number;
}

interface CategoryTrend {
  category: string;
  change: number;
  score: number;
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [trendData, setTrendData] = useState<TrendSeries[]>([]);
  const [categoryData, setCategoryData] = useState<CategoryTrend[]>([]);
  const [lastRun, setLastRun] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [s, t, c, r] = await Promise.all([
          fetchApi<DashboardSummary>("/dashboard/summary"),
          fetchApi<TrendSeries[]>("/dashboard/trends"),
          fetchApi<CategoryTrend[]>("/dashboard/categories"),
          fetchApi<string>("/dashboard/last-research-run"),
        ]);
        setSummary(s);
        setTrendData(t);
        setCategoryData(c);
        setLastRun(r);
      } catch (error) {
        console.error("Failed to load dashboard data", error);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const delta = (current: number | undefined, previous: number | undefined) => {
    if (current == null || previous == null || previous === 0) return null;
    return ((current - previous) / previous) * 100;
  };

  const formatDelta = (d: number | null) => {
    if (d == null) return "—";
    const sign = d >= 0 ? "+" : "";
    return `${sign}${d.toFixed(1)}%`;
  };

  const cards = summary
    ? [
        {
          label: "Products Analyzed",
          value: summary.productsAnalyzed ?? 0,
          sub: "Total unique products researched",
          icon: Package,
          delta: summary.previousPeriod ? delta(summary.productsAnalyzed, summary.previousPeriod.productsAnalyzed) : null,
          color: "navy",
        },
        {
          label: "New Opportunities",
          value: summary.newOpportunities ?? 0,
          sub: "Newly identified qualifying products",
          icon: Sparkles,
          delta: summary.previousPeriod ? delta(summary.newOpportunities, summary.previousPeriod.newOpportunities) : null,
          color: "electric",
        },
        {
          label: "High-Potential Products",
          value: summary.highPotentialProducts ?? 0,
          sub: "Products above configured score",
          icon: TrendingUp,
          delta: summary.previousPeriod ? delta(summary.highPotentialProducts, summary.previousPeriod.highPotentialProducts) : null,
          color: "emerald",
        },
        {
          label: "Verified US Warehouse Products",
          value: summary.verifiedUSWarehouseProducts ?? 0,
          sub: "Recent US inventory verification",
          icon: Truck,
          delta: summary.previousPeriod ? delta(summary.verifiedUSWarehouseProducts, summary.previousPeriod.verifiedUSWarehouseProducts) : null,
          color: "emerald",
        },
        {
          label: "Trending Products",
          value: summary.trendingProducts ?? 0,
          sub: "Increasing demand signals",
          icon: TrendingUp,
          delta: summary.previousPeriod ? delta(summary.trendingProducts, summary.previousPeriod.trendingProducts) : null,
          color: "amber",
        },
        {
          label: "Watchlist Alerts",
          value: summary.watchlistAlerts ?? 0,
          sub: "Material changes requiring attention",
          icon: AlertTriangle,
          delta: null,
          color: "risk",
        },
      ]
    : [];

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Discover profitable products using market intelligence, supplier verification, and AI-powered research.
          </p>
        </div>
        {lastRun && (
          <div className="text-sm text-muted-foreground">
            Last research run: {lastRun}
          </div>
        )}
      </header>

      {cards.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {cards.map((card) => {
            const Icon = card.icon;
            return (
              <Card key={card.label} className="relative overflow-hidden">
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <span className="text-sm font-medium text-muted-foreground">
                    {card.label}
                  </span>
                  <div
                    className={`p-2 text-sm rounded-full bg-${card.color}-500/10 text-${card.color}-500 border border-${card.color}-500/20`}
                  >
                    <Icon className="h-4 w-4" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-semibold">
                    {card.value.toLocaleString()}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{card.sub}</p>
                  {card.delta != null && (
                    <div className="flex items-center gap-1 mt-2 text-xs">
                      {card.delta >= 0 ? (
                        <ArrowUpRight className="h-3 w-3 text-emerald-500" />
                      ) : (
                        <ArrowUpRight className="h-3 w-3 text-risk-500 rotate-[-90deg]" />
                      )}
                      <span
                        className={
                          card.delta >= 0
                            ? "text-emerald-500"
                            : "text-risk-500"
                        }
                      >
                        {formatDelta(card.delta)} vs previous period
                      </span>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="categories">Categories</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Product Opportunity Trends</CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="h-[220px] animate-pulse bg-muted rounded-xl" />
                ) : trendData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={trendData} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
                      <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.25} />
                      <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Line
                        type="monotone"
                        dataKey="opportunityScore"
                        stroke="hsl(var(--primary))"
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="trendingCandidates"
                        stroke="hsl(var(--chart-2))"
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="verifiedProducts"
                        stroke="hsl(var(--chart-3))"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[220px] flex items-center justify-center text-sm text-muted-foreground">
                    No trend data available yet.
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Product Profitability Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="h-[220px] animate-pulse bg-muted rounded-xl" />
                ) : trendData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={trendData} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
                      <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.25} />
                      <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Bar dataKey="opportunityScore" fill="hsl(var(--chart-1))" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[220px] flex items-center justify-center text-sm text-muted-foreground">
                    Profitability distribution will appear after research runs.
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Opportunity Score vs Verified Products</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-[220px] animate-pulse bg-muted rounded-xl" />
              ) : trendData.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={trendData} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.25} />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="opportunityScore"
                      stroke="hsl(var(--primary))"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="verifiedProducts"
                      stroke="hsl(var(--chart-4))"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[220px] flex items-center justify-center text-sm text-muted-foreground">
                  Trend series will be available after research data is collected.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="categories" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Trending Categories — Strongest Recent Demand Growth</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-[220px] animate-pulse bg-muted rounded-xl" />
              ) : categoryData.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart
                    data={categoryData}
                    layout="vertical"
                    margin={{ top: 8, right: 24, left: 8, bottom: 8 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.25} />
                    <XAxis type="number" tick={{ fontSize: 11 }} />
                    <YAxis dataKey="category" type="category" width={140} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="change" fill="hsl(var(--chart-5))" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[220px] flex items-center justify-center text-sm text-muted-foreground">
                  Category trends will appear after research runs.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

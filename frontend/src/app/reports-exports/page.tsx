"use client";

import { useEffect, useState } from "react";
import { Download, FileText, RefreshCcw } from "lucide-react";
import { fetchApi } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ExportRecord {
  id: number;
  export_type: string;
  dataset: string;
  filename: string;
  status: string;
  row_count: number;
  created_at?: string | null;
}

const DATASETS = ["products", "suppliers"] as const;
const FORMATS = ["csv", "json", "xls", "pdf"] as const;

export default function ReportsExportsPage() {
  const [history, setHistory] = useState<ExportRecord[]>([]);

  useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    setHistory(await fetchApi<ExportRecord[]>("/exports/history"));
  }

  async function download(dataset: string, format: string) {
    window.open(`/api/exports/download?dataset=${dataset}&format=${format}`, "_blank");
    setTimeout(loadHistory, 800);
  }

  return (
    <div className="-m-6 min-h-full bg-slate-50 p-4 text-slate-950 md:p-6">
      <div className="mx-auto max-w-[1200px] space-y-4">
        <section className="rounded-2xl border border-indigo-100 bg-white p-6 shadow-sm">
          <Badge className="bg-indigo-100 text-indigo-700 hover:bg-indigo-100">Reports & Exports</Badge>
          <h1 className="mt-3 text-3xl font-bold tracking-tight">Export products and suppliers</h1>
          <p className="mt-2 text-slate-600">
            Download local research data as CSV, JSON, Excel-compatible spreadsheet, or PDF summary.
          </p>
        </section>

        <div className="grid gap-4 lg:grid-cols-2">
          {DATASETS.map((dataset) => (
            <Card key={dataset} className="border-slate-200 bg-white shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg capitalize">
                  <FileText className="h-5 w-5 text-indigo-600" />
                  {dataset}
                </CardTitle>
              </CardHeader>
              <CardContent className="grid gap-2 sm:grid-cols-4">
                {FORMATS.map((format) => (
                  <Button key={format} variant="outline" onClick={() => download(dataset, format)} className="uppercase">
                    <Download className="mr-2 h-4 w-4" />
                    {format}
                  </Button>
                ))}
              </CardContent>
            </Card>
          ))}
        </div>

        <Card className="border-slate-200 bg-white shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center justify-between text-lg">
              <span>Export History</span>
              <Button variant="ghost" size="icon" onClick={loadHistory}>
                <RefreshCcw className="h-4 w-4" />
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {history.length === 0 ? (
              <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">No exports yet.</p>
            ) : (
              history.map((record) => (
                <div key={record.id} className="grid gap-2 rounded-xl bg-slate-50 p-3 text-sm md:grid-cols-[1fr_120px_120px_120px]">
                  <span className="font-medium">{record.filename}</span>
                  <span>{record.dataset}</span>
                  <span>{record.row_count} rows</span>
                  <Badge variant="secondary">{record.status}</Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { Plug, RefreshCcw, Save } from "lucide-react";
import { fetchApi } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

interface ConnectorConfig {
  name: string;
  display_name: string;
  connector_type: string;
  status: string;
  base_url?: string | null;
  api_key_configured: boolean;
  notes?: string | null;
  is_enabled: boolean;
  last_checked_at?: string | null;
}

export default function SettingsIntegrationsPage() {
  const [connectors, setConnectors] = useState<ConnectorConfig[]>([]);
  const [selected, setSelected] = useState<ConnectorConfig | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    loadConnectors();
  }, []);

  async function loadConnectors() {
    const data = await fetchApi<ConnectorConfig[]>("/integrations/configs");
    setConnectors(data);
    setSelected((current) => current || data[0] || null);
  }

  async function saveConnector() {
    if (!selected) return;
    const saved = await fetchApi<ConnectorConfig>("/integrations/configs", {
      method: "PUT",
      body: JSON.stringify({
        ...selected,
        api_key: apiKey || null,
        status: selected.is_enabled ? "configured" : "planned",
      }),
    });
    setSelected(saved);
    setApiKey("");
    setMessage("Connector settings saved.");
    await loadConnectors();
  }

  async function checkConnector() {
    if (!selected) return;
    const result = await fetchApi<{ message: string }>(`/integrations/configs/${selected.name}/check`, {
      method: "POST",
    });
    setMessage(result.message);
    await loadConnectors();
  }

  return (
    <div className="-m-6 min-h-full bg-slate-50 p-4 text-slate-950 md:p-6">
      <div className="mx-auto max-w-[1200px] space-y-4">
        <section className="rounded-2xl border border-indigo-100 bg-white p-6 shadow-sm">
          <Badge className="bg-indigo-100 text-indigo-700 hover:bg-indigo-100">Real Data Connectors</Badge>
          <h1 className="mt-3 text-3xl font-bold tracking-tight">Configure compliant product data sources</h1>
          <p className="mt-2 text-slate-600">
            Store connector settings for marketplaces, suppliers, demand signals, and social sources.
            Live retrieval stays disabled until each provider is configured with allowed API access.
          </p>
        </section>

        {message && <div className="rounded-xl bg-white p-4 text-sm shadow-sm">{message}</div>}

        <div className="grid gap-4 lg:grid-cols-[360px_1fr]">
          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Plug className="h-5 w-5 text-indigo-600" />
                Connectors
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {connectors.map((connector) => (
                <button
                  key={connector.name}
                  onClick={() => setSelected(connector)}
                  className={
                    selected?.name === connector.name
                      ? "w-full rounded-xl border border-indigo-200 bg-indigo-50 p-3 text-left"
                      : "w-full rounded-xl border border-slate-100 bg-slate-50 p-3 text-left hover:bg-indigo-50"
                  }
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold">{connector.display_name}</span>
                    <Badge variant={connector.is_enabled ? "success" : "secondary"}>{connector.status}</Badge>
                  </div>
                  <p className="text-xs text-slate-500">{connector.connector_type}</p>
                </button>
              ))}
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg">Connector Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {!selected ? (
                <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">Select a connector.</p>
              ) : (
                <>
                  <Input value={selected.display_name} onChange={(e) => setSelected({ ...selected, display_name: e.target.value })} />
                  <Input value={selected.base_url || ""} placeholder="Base URL optional" onChange={(e) => setSelected({ ...selected, base_url: e.target.value })} />
                  <Input value={apiKey} type="password" placeholder={selected.api_key_configured ? "API key saved; enter only to replace" : "API key optional"} onChange={(e) => setApiKey(e.target.value)} />
                  <Textarea value={selected.notes || ""} placeholder="Notes, access rules, limits, account details" onChange={(e) => setSelected({ ...selected, notes: e.target.value })} />
                  <label className="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-sm">
                    <input type="checkbox" checked={selected.is_enabled} onChange={(e) => setSelected({ ...selected, is_enabled: e.target.checked })} />
                    Enable connector
                  </label>
                  <div className="flex gap-2">
                    <Button onClick={saveConnector} className="bg-indigo-600 text-white hover:bg-indigo-700">
                      <Save className="mr-2 h-4 w-4" />
                      Save
                    </Button>
                    <Button onClick={checkConnector} variant="outline">
                      <RefreshCcw className="mr-2 h-4 w-4" />
                      Check
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { Play, Plus, RefreshCcw, Zap } from "lucide-react";
import { fetchApi } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

interface AutomationJob {
  id: number;
  name: string;
  schedule_label: string;
  query: string;
  status: string;
  last_run_at?: string | null;
  last_result?: { research_run_id?: number; status?: string } | null;
}

export default function AutomationCenterPage() {
  const [jobs, setJobs] = useState<AutomationJob[]>([]);
  const [form, setForm] = useState({
    name: "Weekly winning products scan",
    schedule_label: "manual / weekly",
    query: "Find growing low-competition products with supplier availability",
  });

  useEffect(() => {
    loadJobs();
  }, []);

  async function loadJobs() {
    setJobs(await fetchApi<AutomationJob[]>("/automation/jobs"));
  }

  async function createJob() {
    await fetchApi("/automation/jobs", {
      method: "POST",
      body: JSON.stringify({
        ...form,
        status: "active",
        filters: { marketplace: "both", region_code: "US" },
      }),
    });
    await loadJobs();
  }

  async function runJob(id: number) {
    await fetchApi(`/automation/jobs/${id}/run`, { method: "POST" });
    await loadJobs();
  }

  async function toggleJob(id: number) {
    await fetchApi(`/automation/jobs/${id}/toggle`, { method: "POST" });
    await loadJobs();
  }

  return (
    <div className="-m-6 min-h-full bg-slate-50 p-4 text-slate-950 md:p-6">
      <div className="mx-auto max-w-[1200px] space-y-4">
        <section className="rounded-2xl border border-indigo-100 bg-white p-6 shadow-sm">
          <Badge className="bg-indigo-100 text-indigo-700 hover:bg-indigo-100">Automation</Badge>
          <h1 className="mt-3 text-3xl font-bold tracking-tight">Schedule and run research jobs</h1>
          <p className="mt-2 text-slate-600">
            Create repeatable product research jobs, run them manually, and track queued research runs.
          </p>
        </section>

        <div className="grid gap-4 lg:grid-cols-[380px_1fr]">
          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Plus className="h-5 w-5 text-indigo-600" />
                New Job
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              <Input value={form.schedule_label} onChange={(e) => setForm({ ...form, schedule_label: e.target.value })} />
              <Textarea value={form.query} onChange={(e) => setForm({ ...form, query: e.target.value })} />
              <Button onClick={createJob} className="w-full bg-indigo-600 text-white hover:bg-indigo-700">
                <Zap className="mr-2 h-4 w-4" />
                Save Automation Job
              </Button>
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center justify-between text-lg">
                <span>Jobs</span>
                <Button variant="ghost" size="icon" onClick={loadJobs}>
                  <RefreshCcw className="h-4 w-4" />
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {jobs.length === 0 ? (
                <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">No automation jobs yet.</p>
              ) : (
                jobs.map((job) => (
                  <div key={job.id} className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                    <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
                      <div>
                        <p className="font-semibold">{job.name}</p>
                        <p className="mt-1 text-sm text-slate-500">{job.query}</p>
                        <p className="mt-1 text-xs text-slate-400">{job.schedule_label}</p>
                      </div>
                      <Badge variant={job.status === "active" ? "success" : "secondary"}>{job.status}</Badge>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Button size="sm" onClick={() => runJob(job.id)} className="bg-emerald-600 text-white hover:bg-emerald-700">
                        <Play className="mr-2 h-4 w-4" />
                        Run Now
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => toggleJob(job.id)}>
                        {job.status === "active" ? "Pause" : "Activate"}
                      </Button>
                      {job.last_result?.research_run_id && (
                        <Badge variant="secondary">Run #{job.last_result.research_run_id}</Badge>
                      )}
                    </div>
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

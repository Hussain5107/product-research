import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export function PlaceholderPage({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="-m-6 min-h-full bg-slate-50 p-4 text-slate-950 md:p-6">
      <div className="mx-auto max-w-[1000px] space-y-4">
        <section className="rounded-2xl border border-indigo-100 bg-white p-6 shadow-sm">
          <Badge className="bg-indigo-100 text-indigo-700 hover:bg-indigo-100">ProductHunter AI</Badge>
          <h1 className="mt-3 text-3xl font-bold tracking-tight">{title}</h1>
          <p className="mt-2 text-slate-600">{description}</p>
        </section>
        <Card className="border-slate-200 bg-white shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">
              This workspace is available for the next implementation phase. Current working features are Product Finder,
              Supplier Finder, Manual Imports, Email Outreach, Real Data Connectors, Automation, and Reports.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

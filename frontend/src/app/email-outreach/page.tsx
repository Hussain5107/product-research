"use client";

import { useEffect, useState } from "react";
import { Mail, Save, Send, ShieldCheck } from "lucide-react";
import { fetchApi } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

interface EmailAccount {
  configured: boolean;
  label?: string;
  sender_name?: string | null;
  sender_email?: string;
  smtp_host?: string;
  smtp_port?: number;
  smtp_username?: string | null;
  smtp_password_configured?: boolean;
  use_tls?: boolean;
}

export default function EmailOutreachPage() {
  const [account, setAccount] = useState<EmailAccount | null>(null);
  const [form, setForm] = useState({
    label: "Primary Email",
    sender_name: "",
    sender_email: "",
    smtp_host: "",
    smtp_port: "587",
    smtp_username: "",
    smtp_password: "",
    use_tls: true,
  });
  const [sendForm, setSendForm] = useState({
    outreach_id: "",
    to_email: "",
    confirm_send: false,
  });
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    loadAccount();
  }, []);

  async function loadAccount() {
    const data = await fetchApi<EmailAccount>("/email/account");
    setAccount(data);
    if (data.configured) {
      setForm({
        label: data.label || "Primary Email",
        sender_name: data.sender_name || "",
        sender_email: data.sender_email || "",
        smtp_host: data.smtp_host || "",
        smtp_port: String(data.smtp_port || 587),
        smtp_username: data.smtp_username || "",
        smtp_password: "",
        use_tls: data.use_tls ?? true,
      });
    }
  }

  async function saveAccount() {
    setSaving(true);
    setMessage("");
    try {
      const data = await fetchApi<EmailAccount>("/email/account", {
        method: "PUT",
        body: JSON.stringify({
          ...form,
          smtp_port: Number(form.smtp_port || 587),
          smtp_password: form.smtp_password || null,
          is_active: true,
        }),
      });
      setAccount(data);
      setMessage("Email account saved.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not save email account.");
    } finally {
      setSaving(false);
    }
  }

  async function sendDraft() {
    setSending(true);
    setMessage("");
    try {
      const data = await fetchApi<{ sent: boolean; to_email: string; sent_at: string }>("/email/send-draft", {
        method: "POST",
        body: JSON.stringify({
          outreach_id: Number(sendForm.outreach_id),
          to_email: sendForm.to_email || null,
          confirm_send: sendForm.confirm_send,
        }),
      });
      setMessage(`Email sent to ${data.to_email} at ${data.sent_at}.`);
      setSendForm({ outreach_id: "", to_email: "", confirm_send: false });
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not send email.");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="-m-6 min-h-full bg-slate-50 p-4 text-slate-950 md:p-6">
      <div className="mx-auto max-w-[1100px] space-y-4">
        <section className="rounded-2xl border border-indigo-100 bg-gradient-to-br from-white via-indigo-50 to-sky-50 p-6 shadow-sm">
          <Badge className="bg-indigo-100 text-indigo-700 hover:bg-indigo-100">Email Outreach</Badge>
          <h1 className="mt-3 text-3xl font-bold tracking-tight md:text-4xl">
            Connect your email and send approved supplier drafts
          </h1>
          <p className="mt-2 max-w-3xl text-slate-600">
            Save SMTP settings locally, then send supplier negotiation drafts only after checking the confirmation box.
          </p>
        </section>

        {message && (
          <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-700 shadow-sm">
            {message}
          </div>
        )}

        <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Mail className="h-5 w-5 text-indigo-600" />
                SMTP Account
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid gap-3 md:grid-cols-2">
                <Input placeholder="Label" value={form.label} onChange={(event) => setForm({ ...form, label: event.target.value })} />
                <Input placeholder="Sender name" value={form.sender_name} onChange={(event) => setForm({ ...form, sender_name: event.target.value })} />
              </div>
              <Input placeholder="Sender email" value={form.sender_email} onChange={(event) => setForm({ ...form, sender_email: event.target.value })} />
              <div className="grid gap-3 md:grid-cols-[1fr_120px]">
                <Input placeholder="SMTP host" value={form.smtp_host} onChange={(event) => setForm({ ...form, smtp_host: event.target.value })} />
                <Input placeholder="Port" type="number" value={form.smtp_port} onChange={(event) => setForm({ ...form, smtp_port: event.target.value })} />
              </div>
              <Input placeholder="SMTP username" value={form.smtp_username} onChange={(event) => setForm({ ...form, smtp_username: event.target.value })} />
              <Input
                placeholder={account?.smtp_password_configured ? "Password saved; enter only to replace" : "SMTP password / app password"}
                type="password"
                value={form.smtp_password}
                onChange={(event) => setForm({ ...form, smtp_password: event.target.value })}
              />
              <label className="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.use_tls}
                  onChange={(event) => setForm({ ...form, use_tls: event.target.checked })}
                />
                Use TLS
              </label>
              <Button onClick={saveAccount} disabled={saving} className="w-full bg-indigo-600 text-white hover:bg-indigo-700">
                <Save className="mr-2 h-4 w-4" />
                {saving ? "Saving..." : "Save Email Account"}
              </Button>
            </CardContent>
          </Card>

          <aside className="space-y-4">
            <Card className="border-slate-200 bg-white shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <ShieldCheck className="h-5 w-5 text-emerald-600" />
                  Status
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <Status label="Configured" value={account?.configured ? "Yes" : "No"} good={!!account?.configured} />
                <Status label="Password saved" value={account?.smtp_password_configured ? "Yes" : "No"} good={!!account?.smtp_password_configured} />
                <Status label="Explicit approval" value="Required" good />
              </CardContent>
            </Card>

            <Card className="border-slate-200 bg-white shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Send className="h-5 w-5 text-indigo-600" />
                  Send Draft
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Input
                  placeholder="Outreach draft ID"
                  type="number"
                  value={sendForm.outreach_id}
                  onChange={(event) => setSendForm({ ...sendForm, outreach_id: event.target.value })}
                />
                <Input
                  placeholder="Recipient email optional"
                  value={sendForm.to_email}
                  onChange={(event) => setSendForm({ ...sendForm, to_email: event.target.value })}
                />
                <label className="flex items-start gap-2 rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-800">
                  <input
                    type="checkbox"
                    className="mt-1"
                    checked={sendForm.confirm_send}
                    onChange={(event) => setSendForm({ ...sendForm, confirm_send: event.target.checked })}
                  />
                  I reviewed this draft and approve sending it now.
                </label>
                <Button
                  onClick={sendDraft}
                  disabled={sending || !sendForm.outreach_id || !sendForm.confirm_send}
                  className="w-full bg-emerald-600 text-white hover:bg-emerald-700"
                >
                  <Send className="mr-2 h-4 w-4" />
                  {sending ? "Sending..." : "Send Approved Draft"}
                </Button>
              </CardContent>
            </Card>
          </aside>
        </div>
      </div>
    </div>
  );
}

function Status({ label, value, good }: { label: string; value: string; good: boolean }) {
  return (
    <div className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2">
      <span className="text-slate-600">{label}</span>
      <Badge variant={good ? "success" : "secondary"}>{value}</Badge>
    </div>
  );
}

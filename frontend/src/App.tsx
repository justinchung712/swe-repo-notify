import React, { useMemo, useState, useEffect } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Link,
  useNavigate,
  useLocation,
} from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { AlertCircle, CheckCircle2, Loader2 } from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

async function postJSON(path: string, body: any) {
  const r = await fetch(API_BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const text = await r.text();
  let data: any = null;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { raw: text };
  }
  if (!r.ok)
    throw Object.assign(new Error(`HTTP ${r.status}`), {
      status: r.status,
      data,
    });
  return data;
}

async function getText(path: string) {
  const r = await fetch(API_BASE + path);
  const t = await r.text();
  if (!r.ok)
    throw Object.assign(new Error(`HTTP ${r.status}`), {
      status: r.status,
      data: t,
    });
  return t;
}

function useQuery() {
  const { search } = useLocation();
  return useMemo(() => new URLSearchParams(search), [search]);
}

function Banner({
  kind = "info",
  children,
}: {
  kind?: "ok" | "warn" | "err" | "info";
  children: React.ReactNode;
}) {
  const color =
    kind === "ok"
      ? "bg-emerald-50 text-emerald-800 border-emerald-200"
      : kind === "err"
      ? "bg-red-50 text-red-800 border-red-200"
      : kind === "warn"
      ? "bg-amber-50 text-amber-900 border-amber-200"
      : "bg-slate-50 text-slate-800 border-slate-200";
  const Icon =
    kind === "ok" ? CheckCircle2 : kind === "err" ? AlertCircle : AlertCircle;
  return (
    <div className={`border rounded-xl p-3 flex items-start gap-2 ${color}`}>
      <Icon className="h-5 w-5 shrink-0 mt-0.5" />
      <div className="text-sm">{children}</div>
    </div>
  );
}

function KeywordInput({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <div className="space-y-2">
      <Label className="text-sm font-medium">
        {label}{" "}
        <span className="text-slate-500 font-normal">(comma-separated)</span>
      </Label>
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder || "e.g. spring boot, postgres"}
        className="min-h-[70px]"
      />
    </div>
  );
}

function SubscribeForm() {
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [notifyEmail, setNotifyEmail] = useState(true);
  const [notifySms, setNotifySms] = useState(false);
  const [ng, setNg] = useState(true);
  const [intern, setIntern] = useState(false);
  const [receiveAll, setReceiveAll] = useState(true);
  const [tech, setTech] = useState("");
  const [role, setRole] = useState("");
  const [loc, setLoc] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{
    kind: "ok" | "err" | "info";
    text: string;
  } | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    if (!email && !phone) {
      setMsg({ kind: "err", text: "Provide an email or phone." });
      return;
    }
    if (!notifyEmail && !notifySms) {
      setMsg({
        kind: "err",
        text: "Enable at least one notification channel.",
      });
      return;
    }
    setBusy(true);
    try {
      const payload = {
        email: email || null,
        phone: phone || null,
        notify_email: notifyEmail,
        notify_sms: notifySms,
        prefs: {
          subscribe_new_grad: ng,
          subscribe_internship: intern,
          receive_all: receiveAll,
          tech_keywords: tech
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
          role_keywords: role
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
          location_keywords: loc
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
        },
      };
      const res = await postJSON("/subscribe", payload);
      setMsg({
        kind: "ok",
        text:
          res?.status === "verification_sent"
            ? "Check your inbox (or SMS) to verify. The link expires in 15 minutes."
            : "Updated your preferences.",
      });
    } catch (e: any) {
      setMsg({ kind: "err", text: e?.data?.detail || e.message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="shadow-xl border-slate-200">
      <CardContent className="p-6 space-y-6">
        <h2 className="text-xl font-semibold">Subscribe</h2>
        <p className="text-sm text-slate-600">
          You'll receive notifications for new postings from{" "}
          <a
            className="underline"
            href="https://github.com/SimplifyJobs/New-Grad-Positions"
            target="_blank"
            rel="noreferrer"
          >
            SimplifyJobs/New-Grad-Positions
          </a>{" "}
          and{" "}
          <a
            className="underline"
            href="https://github.com/SimplifyJobs/Summer2026-Internships"
            target="_blank"
            rel="noreferrer"
          >
            SimplifyJobs/Summer2026-Internships
          </a>
          .
        </p>
        {msg && (
          <Banner
            kind={
              msg.kind === "ok" ? "ok" : msg.kind === "err" ? "err" : "info"
            }
          >
            {msg.text}
          </Banner>
        )}
        <form onSubmit={onSubmit} className="space-y-6">
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Email</Label>
              <Input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
              />
            </div>
            <div className="space-y-2">
              <Label>Phone (E.164)</Label>
              <Input
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+15551234567"
              />
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            <div className="flex items-center justify-between p-3 rounded-xl border">
              <Label htmlFor="notifyEmail">Email notifications</Label>
              <Switch
                id="notifyEmail"
                checked={notifyEmail}
                onCheckedChange={setNotifyEmail}
              />
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl border">
              <Label htmlFor="notifySms">SMS notifications</Label>
              <Switch
                id="notifySms"
                checked={notifySms}
                onCheckedChange={setNotifySms}
              />
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl border">
              <Label htmlFor="receiveAll">Receive all roles/tech</Label>
              <Switch
                id="receiveAll"
                checked={receiveAll}
                onCheckedChange={setReceiveAll}
              />
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div className="flex items-center justify-between p-3 rounded-xl border">
              <Label htmlFor="ng">Subscribe: New Grad repo</Label>
              <Switch id="ng" checked={ng} onCheckedChange={setNg} />
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl border">
              <Label htmlFor="intern">Subscribe: Internships repo</Label>
              <Switch
                id="intern"
                checked={intern}
                onCheckedChange={setIntern}
              />
            </div>
          </div>

          {!receiveAll && (
            <div className="grid gap-4">
              <KeywordInput
                label="Role keywords"
                value={role}
                onChange={setRole}
                placeholder="backend, devops, qa"
              />
              <KeywordInput
                label="Tech keywords"
                value={tech}
                onChange={setTech}
                placeholder="spring boot, postgres, rails"
              />
              <KeywordInput
                label="Location keywords"
                value={loc}
                onChange={setLoc}
                placeholder="remote, chicago, canada"
              />
            </div>
          )}

          <Button type="submit" className="w-full" disabled={busy}>
            {busy && <Loader2 className="h-4 w-4 mr-2 animate-spin" />} Submit
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function RequestEditLink() {
  const [email, setEmail] = useState(""),
    [phone, setPhone] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | undefined>();
  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg(undefined);
    if (!email && !phone) {
      setMsg("Provide email or phone.");
      return;
    }
    setBusy(true);
    try {
      await postJSON("/request-edit-link", {
        email: email || null,
        phone: phone || null,
      });
      setMsg("If an account exists, a temporary link was sent.");
    } catch (e: any) {
      setMsg(e?.data?.detail || e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Card className="shadow-xl border-slate-200">
      <CardContent className="p-6 space-y-6">
        <h2 className="text-xl font-semibold">Get edit link</h2>
        {msg && <Banner kind="info">{msg}</Banner>}
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Email</Label>
              <Input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
              />
            </div>
            <div className="space-y-2">
              <Label>Phone (E.164)</Label>
              <Input
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+15551234567"
              />
            </div>
          </div>
          <Button type="submit" disabled={busy}>
            {busy ? "Sending..." : "Send link"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function EditWithToken() {
  const q = useQuery();
  const token = q.get("token") || "";
  const [msg, setMsg] = useState<string | undefined>();
  const [busy, setBusy] = useState(false);
  const [ng, setNg] = useState(true);
  const [intern, setIntern] = useState(false);
  const [receiveAll, setReceiveAll] = useState(true);
  const [tech, setTech] = useState("");
  const [role, setRole] = useState("");
  const [loc, setLoc] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg(undefined);
    setBusy(true);
    try {
      const body = {
        token,
        subscribe_new_grad: ng,
        subscribe_internship: intern,
        receive_all: receiveAll,
        tech_keywords: tech
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        role_keywords: role
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        location_keywords: loc
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
      };
      const res = await postJSON("/update-prefs", body);
      setMsg("Preferences updated.");
    } catch (e: any) {
      setMsg(e?.data?.detail || e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="shadow-xl border-slate-200">
      <CardContent className="p-6 space-y-6">
        <h2 className="text-xl font-semibold">Edit preferences</h2>
        {token ? (
          <Banner kind="info">
            Token present. Submit to update your preferences.
          </Banner>
        ) : (
          <Banner kind="warn">Missing token in URL (?token=...)</Banner>
        )}
        {msg && <Banner kind="ok">{msg}</Banner>}
        <form onSubmit={onSubmit} className="space-y-6">
          <div className="grid md:grid-cols-2 gap-4">
            <div className="flex items-center justify-between p-3 rounded-xl border">
              <Label htmlFor="ng">New Grad</Label>
              <Switch id="ng" checked={ng} onCheckedChange={setNg} />
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl border">
              <Label htmlFor="intern">Internships</Label>
              <Switch
                id="intern"
                checked={intern}
                onCheckedChange={setIntern}
              />
            </div>
          </div>
          <div className="flex items-center justify-between p-3 rounded-xl border">
            <Label htmlFor="receiveAll">Receive all roles/tech</Label>
            <Switch
              id="receiveAll"
              checked={receiveAll}
              onCheckedChange={setReceiveAll}
            />
          </div>
          {!receiveAll && (
            <div className="grid gap-4">
              <KeywordInput
                label="Role keywords"
                value={role}
                onChange={setRole}
                placeholder="backend, devops, qa"
              />
              <KeywordInput
                label="Tech keywords"
                value={tech}
                onChange={setTech}
                placeholder="spring boot, postgres, rails"
              />
              <KeywordInput
                label="Location keywords"
                value={loc}
                onChange={setLoc}
                placeholder="remote, chicago, canada"
              />
            </div>
          )}
          <Button type="submit" className="w-full" disabled={!token || busy}>
            {busy ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}{" "}
            Save
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function UnsubscribeWithToken() {
  const q = useQuery();
  const token = q.get("token") || "";
  const [disableEmail, setDisableEmail] = useState(true);
  const [disableSms, setDisableSms] = useState(true);
  const [msg, setMsg] = useState<string | undefined>();
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMsg(undefined);
    try {
      const res = await postJSON("/unsubscribe/confirm", {
        token,
        disable_email: disableEmail,
        disable_sms: disableSms,
      });
      setMsg("Preference saved. You can resubscribe any time.");
    } catch (e: any) {
      setMsg(e?.data?.detail || e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="shadow-xl border-slate-200">
      <CardContent className="p-6 space-y-6">
        <h2 className="text-xl font-semibold">Unsubscribe</h2>
        {token ? (
          <Banner kind="info">Token present for unsubscribe.</Banner>
        ) : (
          <Banner kind="warn">Missing token in URL (?token=...)</Banner>
        )}
        {msg && <Banner kind="ok">{msg}</Banner>}
        <form onSubmit={onSubmit} className="space-y-6">
          <div className="grid md:grid-cols-2 gap-4">
            <div className="flex items-center justify-between p-3 rounded-xl border">
              <Label htmlFor="de">Disable Email</Label>
              <Switch
                id="de"
                checked={disableEmail}
                onCheckedChange={setDisableEmail}
              />
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl border">
              <Label htmlFor="ds">Disable SMS</Label>
              <Switch
                id="ds"
                checked={disableSms}
                onCheckedChange={setDisableSms}
              />
            </div>
          </div>
          <Button type="submit" className="w-full" disabled={!token || busy}>
            {busy ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}{" "}
            Confirm
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function Shell() {
  const location = useLocation();
  const tab = location.pathname.startsWith("/edit")
    ? "edit"
    : location.pathname.startsWith("/unsubscribe")
    ? "unsub"
    : location.pathname.startsWith("/request-edit")
    ? "request"
    : "subscribe";
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="max-w-3xl mx-auto px-4 py-10">
        <div className="mb-6 text-center">
          <h1 className="text-3xl font-bold">
            Personalized Tech Jobs & Internships Notifications
          </h1>
          <p className="text-slate-600">
            Subscribe, edit preferences, or unsubscribe securely.
          </p>
        </div>
        <Tabs value={tab} className="w-full">
          <TabsList className="grid grid-cols-3 md:grid-cols-4">
            <TabsTrigger value="subscribe" asChild>
              <Link to="/">Subscribe</Link>
            </TabsTrigger>
            <TabsTrigger value="request" asChild>
              <Link to="/request-edit">Get Edit Link</Link>
            </TabsTrigger>
            <TabsTrigger value="edit" asChild>
              <Link to="/edit">Edit (token)</Link>
            </TabsTrigger>
            <TabsTrigger value="unsub" asChild>
              <Link to="/unsubscribe">Unsubscribe (token)</Link>
            </TabsTrigger>
          </TabsList>
          <div className="mt-6">
            <Routes>
              <Route path="/" element={<SubscribeForm />} />
              <Route path="/request-edit" element={<RequestEditLink />} />
              <Route path="/edit" element={<EditWithToken />} />
              <Route path="/unsubscribe" element={<UnsubscribeWithToken />} />
            </Routes>
          </div>
        </Tabs>
        <p className="mt-8 text-center text-xs text-slate-500">
          By subscribing you agree to receive notifications. Links expire per
          message.
        </p>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Shell />
    </BrowserRouter>
  );
}

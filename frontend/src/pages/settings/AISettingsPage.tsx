import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router";
import {
  Key,
  FileText,
  Sparkles,
  TestTube,
  Trash2,
  RotateCcw,
} from "lucide-react";
import { toast } from "sonner";
import axios from "axios";
import api, { ApiError } from "@/api/client";
import type {
  AIConfigResponse,
  AIConfigPut,
  AIPromptOverride,
} from "@/api/types";
import { useAuth } from "@/auth/AuthContext";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { PlanUpgradeGate } from "@/components/PlanUpgradeGate";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const PARSER_LABELS: Record<string, string> = {
  da_email: "DA Email Parser",
  emission_report: "Emission Parser",
};

const DEFAULT_BASE_URL = "https://api.openai.com/v1";
const DEFAULT_MODEL = "gpt-4o-mini";

function isUpgradeRequired(err: unknown): boolean {
  if (axios.isAxiosError(err) && err.response?.status === 403) {
    const data = err.response.data as
      | { code?: string; detail?: { code?: string } }
      | undefined;
    return (
      data?.code === "upgrade_required" ||
      data?.detail?.code === "upgrade_required"
    );
  }
  if (err instanceof ApiError && err.code === "upgrade_required") {
    return true;
  }
  return false;
}

function getUpgradeMessage(err: unknown): string {
  if (axios.isAxiosError(err) && err.response?.data) {
    const data = err.response.data as {
      message?: string;
      detail?: { message?: string };
    };
    return (
      data?.message ??
      data?.detail?.message ??
      "Upgrade to Professional or Enterprise to configure your own AI settings."
    );
  }
  if (err instanceof ApiError) {
    return err.message;
  }
  return "Upgrade to Professional or Enterprise to configure your own AI settings.";
}

export function AISettingsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const hasSettingsWrite = user?.permissions.includes("settings:write") ?? false;
  const isPlatformAdmin = user?.is_platform_admin ?? false;

  const [config, setConfig] = useState<AIConfigResponse | null>(null);
  const [prompts, setPrompts] = useState<AIPromptOverride[]>([]);
  const [loading, setLoading] = useState(true);
  const [upgradeRequired, setUpgradeRequired] = useState(false);
  const [upgradeMessage, setUpgradeMessage] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  // Integration form state
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState(DEFAULT_BASE_URL);
  const [model, setModel] = useState(DEFAULT_MODEL);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [confirmClear, setConfirmClear] = useState(false);

  // Prompts form state
  const [promptTexts, setPromptTexts] = useState<Record<string, string>>({});
  const [savingPrompt, setSavingPrompt] = useState<string | null>(null);
  const [resettingPrompt, setResettingPrompt] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<"integration" | "prompts">(
    "integration",
  );

  const fetchData = useCallback(async () => {
    if (!hasSettingsWrite && !isPlatformAdmin) {
      navigate("/settings/integrations", { replace: true });
      return;
    }

    setLoading(true);
    setError(null);
    setUpgradeRequired(false);

    try {
      const [configRes, promptsRes] = await Promise.all([
        api.get<AIConfigResponse | null>("/settings/ai"),
        api.get<AIPromptOverride[]>("/settings/ai/prompts"),
      ]);

      const cfg = configRes.data;
      setConfig(cfg ?? null);

      if (cfg) {
        setBaseUrl(cfg.base_url ?? DEFAULT_BASE_URL);
        setModel(cfg.model ?? DEFAULT_MODEL);
      } else {
        setBaseUrl(DEFAULT_BASE_URL);
        setModel(DEFAULT_MODEL);
      }

      const promptList = promptsRes.data ?? [];
      setPrompts(promptList);

      const texts: Record<string, string> = {};
      for (const p of promptList) {
        texts[p.parser_type] = p.prompt_text;
      }
      setPromptTexts(texts);
    } catch (err) {
      if (isUpgradeRequired(err)) {
        setUpgradeRequired(true);
        setUpgradeMessage(getUpgradeMessage(err));
      } else {
        setError(
          err instanceof ApiError ? err.message : "Failed to load AI settings",
        );
      }
    } finally {
      setLoading(false);
    }
  }, [hasSettingsWrite, isPlatformAdmin, navigate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  async function handleSaveIntegration(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setUpgradeRequired(false);

    try {
      const body: AIConfigPut = {
        base_url: baseUrl || null,
        model: model || null,
        enabled: true,
      };
      if (apiKey.trim()) {
        body.api_key = apiKey.trim();
      } else if (!config?.api_key_configured) {
        toast.error("API key is required when creating config.");
        setSaving(false);
        return;
      }

      await api.put<AIConfigResponse>("/settings/ai", body);
      setApiKey("");
      toast.success("AI integration saved.");
      fetchData();
    } catch (err) {
      if (isUpgradeRequired(err)) {
        setUpgradeRequired(true);
        setUpgradeMessage(getUpgradeMessage(err));
      } else {
        toast.error(
          err instanceof ApiError ? err.message : "Failed to save",
        );
      }
    } finally {
      setSaving(false);
    }
  }

  async function handleTestConnection() {
    setTesting(true);
    setError(null);
    setUpgradeRequired(false);

    try {
      const body: { api_key?: string; base_url?: string; model?: string } = {};
      if (apiKey.trim()) body.api_key = apiKey.trim();
      if (baseUrl.trim()) body.base_url = baseUrl.trim();
      if (model.trim()) body.model = model.trim();

      const res = await api.post<{
        status: string;
        message: string;
        model?: string;
      }>("/settings/ai/test", Object.keys(body).length > 0 ? body : undefined);

      const msg =
        res.data.model != null
          ? `Connected to ${res.data.model}`
          : res.data.message ?? "Connection successful.";
      toast.success(msg);
    } catch (err) {
      if (isUpgradeRequired(err)) {
        setUpgradeRequired(true);
        setUpgradeMessage(getUpgradeMessage(err));
      } else {
        const msg =
          err instanceof ApiError
            ? err.message
            : axios.isAxiosError(err) &&
                err.response?.data?.detail &&
                typeof err.response.data.detail === "object" &&
                "message" in err.response.data.detail
              ? String(
                  (err.response.data.detail as { message?: string }).message,
                )
              : "Connection test failed.";
        toast.error(msg);
      }
    } finally {
      setTesting(false);
    }
  }

  async function handleClearConfig() {
    setSaving(true);
    setError(null);
    setUpgradeRequired(false);

    try {
      await api.delete("/settings/ai");
      setConfig(null);
      setApiKey("");
      setBaseUrl(DEFAULT_BASE_URL);
      setModel(DEFAULT_MODEL);
      toast.success("AI config removed.");
      setConfirmClear(false);
    } catch (err) {
      if (isUpgradeRequired(err)) {
        setUpgradeRequired(true);
        setUpgradeMessage(getUpgradeMessage(err));
      } else {
        toast.error(
          err instanceof ApiError ? err.message : "Failed to remove config",
        );
      }
    } finally {
      setSaving(false);
    }
  }

  async function handleSavePrompt(parserType: string) {
    const text = promptTexts[parserType] ?? "";
    setSavingPrompt(parserType);
    setError(null);
    setUpgradeRequired(false);

    try {
      await api.put(`/settings/ai/prompts/${parserType}`, {
        prompt_text: text,
        version: "v1",
      });
      toast.success(`${PARSER_LABELS[parserType] ?? parserType} saved.`);
      fetchData();
    } catch (err) {
      if (isUpgradeRequired(err)) {
        setUpgradeRequired(true);
        setUpgradeMessage(getUpgradeMessage(err));
      } else {
        toast.error(
          err instanceof ApiError ? err.message : "Failed to save prompt",
        );
      }
    } finally {
      setSavingPrompt(null);
    }
  }

  async function handleResetPrompt(parserType: string) {
    setResettingPrompt(parserType);
    setError(null);
    setUpgradeRequired(false);

    try {
      await api.post(`/settings/ai/prompts/${parserType}/reset`);
      toast.success(`${PARSER_LABELS[parserType] ?? parserType} reset to default.`);
      fetchData();
    } catch (err) {
      if (isUpgradeRequired(err)) {
        setUpgradeRequired(true);
        setUpgradeMessage(getUpgradeMessage(err));
      } else {
        toast.error(
          err instanceof ApiError ? err.message : "Failed to reset prompt",
        );
      }
    } finally {
      setResettingPrompt(null);
    }
  }

  if (!hasSettingsWrite && !isPlatformAdmin) {
    return null;
  }

  if (loading) return <LoadingSpinner />;

  // Upgrade required: show only the clean marketing-style upgrade page
  if (upgradeRequired) {
    return (
      <PlanUpgradeGate
        featureName="AI Settings"
        requiredPlans="Professional and Enterprise"
        message={upgradeMessage}
        description="Configure your own AI provider, customize prompts, and more."
        icon={Sparkles}
        billingPath="/settings/billing"
        variant="fullPage"
      />
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">AI Settings</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Configure your own AI provider (API key, model) and customize parsing
            prompts.
          </p>
        </div>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Tabs */}
      <div className="mb-6 flex gap-3 border-b border-slate-200 dark:border-slate-700">
        <button
          type="button"
          onClick={() => setActiveTab("integration")}
          className={`flex items-center gap-3 border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "integration"
              ? "border-mint-500 text-navy-800 dark:text-mint-200"
              : "border-transparent text-slate-600 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
          }`}
        >
          <Key className="size-4" />
          Integration
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("prompts")}
          className={`flex items-center gap-3 border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "prompts"
              ? "border-mint-500 text-navy-800 dark:text-mint-200"
              : "border-transparent text-slate-600 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
          }`}
        >
          <FileText className="size-4" />
          Prompts
        </button>
      </div>

      {activeTab === "integration" ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              <Sparkles className="size-5" />
              AI Integration
            </CardTitle>
            <CardDescription>
              Configure API key, base URL, and model. Use Azure or other
              OpenAI-compatible endpoints by changing the base URL.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form
              onSubmit={handleSaveIntegration}
              className="flex flex-col gap-4"
            >
              <div className="space-y-2">
                <Label htmlFor="api_key">API Key</Label>
                <Input
                  id="api_key"
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={
                    config?.api_key_configured
                      ? "Enter new key to update"
                      : "Enter your API key"
                  }
                  autoComplete="off"
                />
                {config?.api_key_configured && (
                  <p className="text-xs text-muted-foreground">
                    Leave blank to keep existing key.
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="base_url">Base URL</Label>
                <Input
                  id="base_url"
                  type="url"
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  placeholder="https://api.openai.com/v1"
                />
                <p className="text-xs text-muted-foreground">
                  For Azure or other OpenAI-compatible APIs, use the endpoint
                  URL (e.g. https://your-resource.openai.azure.com/openai/deployments/your-deployment).
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="model">Model</Label>
                <Input
                  id="model"
                  type="text"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  placeholder="gpt-4o-mini"
                />
              </div>

              <div className="flex flex-wrap gap-3">
                <Button type="submit" disabled={saving || upgradeRequired}>
                  {saving ? "Saving…" : "Save"}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleTestConnection}
                  disabled={testing || upgradeRequired}
                >
                  <TestTube
                    className={`size-4 ${testing ? "animate-pulse" : ""}`}
                  />
                  {testing ? "Testing…" : "Test connection"}
                </Button>
                {config?.api_key_configured && (
                  <Button
                    type="button"
                    variant="outline"
                    className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                    onClick={() => setConfirmClear(true)}
                    disabled={saving || upgradeRequired}
                  >
                    <Trash2 className="size-4" />
                    Remove config
                  </Button>
                )}
              </div>
            </form>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {(["da_email", "emission_report"] as const).map((parserType) => {
            const override = prompts.find((p) => p.parser_type === parserType);
            const text =
              promptTexts[parserType] ?? override?.prompt_text ?? "";
            const label = PARSER_LABELS[parserType] ?? parserType;

            return (
              <Card key={parserType}>
                <CardHeader>
                  <div className="flex flex-wrap items-center justify-between gap-4">
                    <div>
                      <CardTitle>{label}</CardTitle>
                    <CardDescription>
                        {override
                          ? "Customize the prompt used for this parser. Reset to restore the default."
                          : "Using default prompt. Add a custom prompt below to override."}
                    </CardDescription>
                    </div>
                    {override?.version && (
                      <span className="text-xs text-muted-foreground">
                        Version: {override.version}
                      </span>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor={`prompt-${parserType}`}>
                      Prompt text
                    </Label>
                    <Textarea
                      id={`prompt-${parserType}`}
                      value={text}
                      onChange={(e) =>
                        setPromptTexts((prev) => ({
                          ...prev,
                          [parserType]: e.target.value,
                        }))
                      }
                      rows={12}
                      className="font-mono text-sm"
                      disabled={upgradeRequired}
                    />
                  </div>
                  <div className="flex gap-3">
                    <Button
                      onClick={() => handleSavePrompt(parserType)}
                      disabled={
                        savingPrompt === parserType || upgradeRequired
                      }
                    >
                      {savingPrompt === parserType ? "Saving…" : "Save"}
                    </Button>
                    {override && (
                      <Button
                        variant="outline"
                        onClick={() => handleResetPrompt(parserType)}
                        disabled={
                          resettingPrompt === parserType || upgradeRequired
                        }
                      >
                      <RotateCcw
                        className={`size-4 ${
                          resettingPrompt === parserType
                            ? "animate-spin"
                            : ""
                        }`}
                      />
                      {resettingPrompt === parserType
                        ? "Resetting…"
                        : "Reset to default"}
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Clear config confirmation - only when not upgrade-gated */}
      <Dialog
        open={confirmClear}
        onOpenChange={(open) => !open && setConfirmClear(false)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove AI config?</DialogTitle>
            <DialogDescription>
              This will remove your API key and custom settings. AI parsing will
              fall back to the default provider. You can reconfigure later.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmClear(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleClearConfig}
              disabled={saving}
            >
              {saving ? "Removing…" : "Remove"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

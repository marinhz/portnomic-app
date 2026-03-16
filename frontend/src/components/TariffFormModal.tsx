import { useState, useEffect } from "react";
import api, { ApiError } from "@/api/client";
import type {
  TariffCreate,
  TariffUpdate,
  TariffResponse,
  TariffFormulaConfig,
  TariffFormulaLineItem,
  TariffLineItemType,
} from "@/api/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Plus, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";

const LINE_ITEM_TYPES: { value: TariffLineItemType; label: string }[] = [
  { value: "per_call", label: "Per call" },
  { value: "per_ton", label: "Per ton" },
  { value: "per_hour", label: "Per hour" },
  { value: "fixed", label: "Fixed" },
];

const CURRENCIES = ["USD", "EUR", "GBP"];

const defaultFormulaConfig: TariffFormulaConfig = {
  items: [{ description: "", type: "per_call", rate: 0, currency: "USD" }],
  tax_rate: 0,
  currency: "USD",
};

function formatDateForInput(dateStr: string | null): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return d.toISOString().slice(0, 10);
}

type TariffFormModalProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  portId: string;
  tariff?: TariffResponse | null;
  onSuccess: () => void;
};

export function TariffFormModal({
  open,
  onOpenChange,
  portId,
  tariff,
  onSuccess,
}: TariffFormModalProps) {
  const isEdit = !!tariff;
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [validFrom, setValidFrom] = useState("");
  const [validTo, setValidTo] = useState("");
  const [formulaConfig, setFormulaConfig] =
    useState<TariffFormulaConfig>(defaultFormulaConfig);

  useEffect(() => {
    if (open) {
      setError(null);
      if (tariff) {
        setName(tariff.name);
        setValidFrom(formatDateForInput(tariff.valid_from));
        setValidTo(formatDateForInput(tariff.valid_to));
        const fc = tariff.formula_config as TariffFormulaConfig;
        setFormulaConfig({
          items:
            fc?.items?.length > 0
              ? fc.items.map((i) => ({
                  description: i.description ?? "",
                  type: (i.type ?? "per_call") as TariffLineItemType,
                  rate: Number(i.rate) ?? 0,
                  currency: i.currency ?? "USD",
                }))
              : defaultFormulaConfig.items,
          tax_rate: Number(fc?.tax_rate) ?? 0,
          currency: fc?.currency ?? "USD",
        });
      } else {
        setName("");
        setValidFrom("");
        setValidTo("");
        setFormulaConfig(defaultFormulaConfig);
      }
    }
  }, [open, tariff]);

  const addLineItem = () => {
    setFormulaConfig((prev) => ({
      ...prev,
      items: [
        ...prev.items,
        {
          description: "",
          type: "per_call" as const,
          rate: 0,
          currency: prev.currency,
        },
      ],
    }));
  };

  const removeLineItem = (index: number) => {
    setFormulaConfig((prev) => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index),
    }));
  };

  const updateLineItem = (
    index: number,
    field: keyof TariffFormulaLineItem,
    value: string | number
  ) => {
    setFormulaConfig((prev) => ({
      ...prev,
      items: prev.items.map((item, i) =>
        i === index ? { ...item, [field]: value } : item
      ),
    }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    const payload = {
      name,
      valid_from: validFrom,
      valid_to: validTo || null,
      formula_config: {
        items: formulaConfig.items.filter((i) => i.description.trim()),
        tax_rate: Number(formulaConfig.tax_rate) || 0,
        currency: formulaConfig.currency,
      },
    };

    try {
      if (isEdit) {
        await api.put<TariffUpdate>(`/tariffs/${tariff.id}`, payload);
      } else {
        await api.post<TariffCreate>("/tariffs", {
          ...payload,
          port_id: portId,
        });
      }
      onOpenChange(false);
      onSuccess();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Failed to save tariff"
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit Tariff" : "Add Tariff"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-200">
              {error}
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="tariff-name">Name</Label>
            <Input
              id="tariff-name"
              value={name}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setName(e.target.value)
              }
              required
              placeholder="e.g. Standard Tariff 2025"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="tariff-valid-from">Valid From</Label>
              <Input
                id="tariff-valid-from"
                type="date"
                value={validFrom}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setValidFrom(e.target.value)
                }
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="tariff-valid-to">Valid To (optional)</Label>
              <Input
                id="tariff-valid-to"
                type="date"
                value={validTo}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setValidTo(e.target.value)
                }
              />
            </div>
          </div>

          <div className="space-y-3 border-t border-slate-200 pt-4 dark:border-slate-700">
            <div className="flex items-center justify-between">
              <Label>Line Items</Label>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={addLineItem}
              >
                <Plus className="size-4" />
                Add Item
              </Button>
            </div>
            <div className="space-y-3">
              {formulaConfig.items.map((item, index) => (
                <div
                  key={index}
                  className="flex flex-wrap items-end gap-2 rounded-md border border-slate-200 p-3 dark:border-slate-700"
                >
                  <div className="min-w-[140px] flex-1 space-y-1">
                    <Label className="text-xs">Description</Label>
                    <Input
                      value={item.description}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                        updateLineItem(index, "description", e.target.value)
                      }
                      placeholder="e.g. Pilotage"
                      className="h-8"
                    />
                  </div>
                  <div className="w-24 space-y-1">
                    <Label className="text-xs">Type</Label>
                    <select
                      value={item.type}
                      onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                        updateLineItem(
                          index,
                          "type",
                          e.target.value as TariffLineItemType
                        )
                      }
                      className={cn(
                        "flex h-8 w-full rounded-md border border-input bg-background px-3 py-1 text-sm text-foreground",
                        "dark:bg-navy-800 dark:text-foreground",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      )}
                    >
                      {LINE_ITEM_TYPES.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="w-20 space-y-1">
                    <Label className="text-xs">Rate</Label>
                    <Input
                      type="number"
                      step="any"
                      min={0}
                      value={item.rate || ""}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                        updateLineItem(
                          index,
                          "rate",
                          parseFloat(e.target.value) || 0
                        )
                      }
                      className="h-8"
                    />
                  </div>
                  <div className="w-20 space-y-1">
                    <Label className="text-xs">Currency</Label>
                    <select
                      value={item.currency}
                      onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                        updateLineItem(index, "currency", e.target.value)
                      }
                      className={cn(
                        "flex h-8 w-full rounded-md border border-input bg-background px-3 py-1 text-sm text-foreground",
                        "dark:bg-navy-800 dark:text-foreground",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      )}
                    >
                      {CURRENCIES.map((c) => (
                        <option key={c} value={c}>
                          {c}
                        </option>
                      ))}
                    </select>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="size-8 shrink-0 text-slate-500 hover:text-red-600"
                    onClick={() => removeLineItem(index)}
                    aria-label="Remove line item"
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              ))}
            </div>
            <div className="flex gap-4">
              <div className="w-24 space-y-2">
                <Label htmlFor="tariff-tax-rate">Tax Rate (%)</Label>
                <Input
                  id="tariff-tax-rate"
                  type="number"
                  step="any"
                  min={0}
                  max={100}
                  value={formulaConfig.tax_rate || ""}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setFormulaConfig((prev) => ({
                      ...prev,
                      tax_rate: parseFloat(e.target.value) || 0,
                    }))
                  }
                />
              </div>
              <div className="w-24 space-y-2">
                <Label htmlFor="tariff-currency">Default Currency</Label>
                <select
                  id="tariff-currency"
                  value={formulaConfig.currency}
                  onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                    setFormulaConfig((prev) => ({
                      ...prev,
                      currency: e.target.value,
                    }))
                  }
                  className={cn(
                    "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm text-foreground",
                    "dark:bg-navy-800 dark:text-foreground",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  )}
                >
                  {CURRENCIES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Saving..." : isEdit ? "Update Tariff" : "Create Tariff"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

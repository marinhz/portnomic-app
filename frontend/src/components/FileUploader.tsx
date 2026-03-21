import * as React from "react";
import { Upload } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import type { DocumentCategory } from "@/api/types";

const ACCEPT = ".pdf,.xlsx,.xls,.jpg,.jpeg";
const MAX_SIZE_MB = 10;

export interface FileUploaderProps {
  category: DocumentCategory;
  onCategoryChange: (cat: DocumentCategory) => void;
  onFileSelect: (file: File) => void;
  disabled?: boolean;
  isDragging?: boolean;
  onDragChange?: (dragging: boolean) => void;
  error?: string | null;
  className?: string;
}

const CATEGORY_OPTIONS: { value: DocumentCategory; label: string }[] = [
  { value: "sof", label: "Statement of Facts (SOF)" },
  { value: "da", label: "Disbursement Account (DA/Invoice)" },
  { value: "noon_report", label: "Noon Report" },
];

export function FileUploader({
  category,
  onCategoryChange,
  onFileSelect,
  disabled = false,
  isDragging = false,
  onDragChange,
  error,
  className,
}: FileUploaderProps) {
  const inputRef = React.useRef<HTMLInputElement>(null);

  const validateAndEmit = React.useCallback(
    (file: File) => {
      const ext = file.name.split(".").pop()?.toLowerCase();
      const allowed = ["pdf", "xlsx", "xls", "jpg", "jpeg"];
      if (!ext || !allowed.includes(ext)) {
        return;
      }
      if (file.size > MAX_SIZE_MB * 1024 * 1024) {
        return;
      }
      onFileSelect(file);
    },
    [onFileSelect]
  );

  const handleDrop = React.useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      onDragChange?.(false);
      if (disabled) return;
      const file = e.dataTransfer.files[0];
      if (file) validateAndEmit(file);
    },
    [disabled, onDragChange, validateAndEmit]
  );

  const handleDragOver = React.useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      onDragChange?.(true);
    },
    [onDragChange]
  );

  const handleDragLeave = React.useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      onDragChange?.(false);
    },
    [onDragChange]
  );

  const handleClick = React.useCallback(() => {
    if (disabled) return;
    inputRef.current?.click();
  }, [disabled]);

  const handleChange = React.useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) validateAndEmit(file);
      e.target.value = "";
    },
    [validateAndEmit]
  );

  return (
    <div className={cn("space-y-4", className)}>
      <div className="space-y-2">
        <Label htmlFor="category">Document category</Label>
        <select
          id="category"
          value={category}
          onChange={(e) => onCategoryChange(e.target.value as DocumentCategory)}
          disabled={disabled}
          className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 transition-colors focus:border-mint-500 focus:outline-none focus:ring-2 focus:ring-mint-500/20 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
        >
          {CATEGORY_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        onChange={handleChange}
        className="sr-only"
        aria-hidden
      />

      <div
        role="button"
        tabIndex={0}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={handleClick}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            handleClick();
          }
        }}
        aria-label="Drop file here or click to browse"
        className={cn(
          "flex min-h-[140px] cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 transition-colors",
          isDragging
            ? "border-primary bg-primary/5"
            : "border-slate-300 dark:border-slate-600 hover:border-mint-500 dark:hover:border-mint-600",
          disabled && "cursor-not-allowed opacity-50",
          error && "border-destructive"
        )}
      >
        <Upload
          className={cn(
            "mb-2 size-10 text-slate-400 dark:text-slate-500",
            isDragging && "text-primary"
          )}
          aria-hidden
        />
        <p className="text-center text-sm font-medium text-slate-700 dark:text-slate-300">
          Drop a file here or click to browse
        </p>
        <p className="mt-1 text-center text-xs text-slate-500 dark:text-slate-400">
          PDF, XLSX, JPG up to {MAX_SIZE_MB} MB
        </p>
      </div>

      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

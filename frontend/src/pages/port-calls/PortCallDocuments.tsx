import { useCallback, useEffect, useState } from "react";
import { Link, useLoaderData, useParams } from "react-router";
import api, { ApiError } from "@/api/client";
import type {
  SingleResponse,
  PaginatedResponse,
  DocumentCategory,
  DocumentResponse,
  DocumentUploadResponse,
  DiscrepancyResponse,
  ParseJobResponse,
} from "@/api/types";
import type { PortCallDocumentsLoaderData } from "./loaders";
import { FileUploader } from "@/components/FileUploader";
import { SentinelAlert } from "@/components/sentinel";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

const POLL_INTERVAL_MS = 1500;

type UploadPhase = "idle" | "uploading" | "parsing" | "auditing" | "done" | "error";

export function PortCallDocuments() {
  const { portCallId } = useParams();
  const { portCall, documents: initialDocuments, discrepancies, discrepanciesError } =
    useLoaderData() as PortCallDocumentsLoaderData;

  const [category, setCategory] = useState<DocumentCategory>("da");
  const [phase, setPhase] = useState<UploadPhase>("idle");
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [documents, setDocuments] = useState<DocumentResponse[]>(initialDocuments);
  const [discrepanciesState, setDiscrepanciesState] = useState<DiscrepancyResponse[]>(discrepancies);
  const [discrepanciesDismissed, setDiscrepanciesDismissed] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const refreshDocuments = useCallback(async () => {
    if (!portCallId) return;
    try {
      const res = await api.get<PaginatedResponse<DocumentResponse>>(
        `/port-calls/${portCallId}/documents`
      );
      setDocuments(res.data.data ?? []);
    } catch {
      // ignore
    }
  }, [portCallId]);

  const refreshDiscrepancies = useCallback(async () => {
    if (!portCallId) return;
    try {
      const res = await api.get<SingleResponse<DiscrepancyResponse[]>>(
        `/port-calls/${portCallId}/discrepancies`
      );
      setDiscrepanciesState(res.data.data ?? []);
    } catch {
      // ignore
    }
  }, [portCallId]);

  const handleFileSelect = useCallback(
    async (file: File) => {
      if (!portCallId) return;

      setUploadError(null);
      setUploadMessage(null);
      setPhase("uploading");

      const formData = new FormData();
      formData.append("file", file);
      formData.append("category", category);

      try {
        const res = await api.post<SingleResponse<DocumentUploadResponse>>(
          `/port-calls/${portCallId}/upload`,
          formData,
          {
            headers: { "Content-Type": "multipart/form-data" },
          }
        );

        const { job_id, status: uploadStatus } = res.data.data;

        if (uploadStatus === "already_processed") {
          setUploadMessage("This document has already been processed.");
          setPhase("done");
          await Promise.all([refreshDocuments(), refreshDiscrepancies()]);
          return;
        }

        setDocuments((prev) =>
          prev.concat([
            {
              id: res.data.data.document_id,
              port_call_id: portCallId!,
              filename: file.name,
              category: category,
              processing_status: "pending",
              created_at: new Date().toISOString(),
            },
          ])
        );
        setPhase("parsing");

        const poll = async () => {
          try {
            const statusRes = await api.get<
              SingleResponse<ParseJobResponse>
            >(`/port-calls/${portCallId}/documents/parse-status/${job_id}`);
            const job = statusRes.data.data;
            const status = (job.status || "").toLowerCase();

            if (status === "completed") {
              setPhase("auditing");
              await Promise.all([refreshDiscrepancies(), refreshDocuments()]);
              setPhase("done");
              return;
            }
            if (status === "failed") {
              setPhase("error");
              setUploadError(job.error_message ?? "Parse failed");
              return;
            }
            if (status === "processing") {
              setPhase("parsing");
            }
          } catch (err) {
            setPhase("error");
            setUploadError(
              err instanceof ApiError ? err.message : "Failed to check status"
            );
            return;
          }
          setTimeout(poll, POLL_INTERVAL_MS);
        };

        setTimeout(poll, POLL_INTERVAL_MS);
      } catch (err) {
        setPhase("error");
        setUploadError(
          err instanceof ApiError ? err.message : "Upload failed"
        );
      }
    },
    [portCallId, category, refreshDiscrepancies, refreshDocuments]
  );

  useEffect(() => {
    setDiscrepanciesState(discrepancies);
  }, [discrepancies]);

  useEffect(() => {
    setDocuments(initialDocuments);
  }, [initialDocuments]);

  const isUploading = phase === "uploading" || phase === "parsing" || phase === "auditing";
  const showSentinelAlert =
    !discrepanciesDismissed && discrepanciesState.length > 0 && phase === "done";

  return (
    <div className="space-y-6">
      <div className="mb-6">
        <Link
          to={`/port-calls/${portCallId}`}
          className="mb-2 inline-block text-sm text-mint-500 hover:text-mint-400 dark:text-mint-400 dark:hover:text-mint-300"
        >
          &larr; Back to Port Call
        </Link>
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
          Upload Documents
        </h1>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          Upload SOF, DA, or Noon Report files for Sentinel audit. Parsing and audit run automatically.
        </p>
      </div>

      {discrepanciesError && (
        <div
          className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-200"
          role="status"
        >
          Sentinel data unavailable: {discrepanciesError}
        </div>
      )}

      {showSentinelAlert && (
        <SentinelAlert
          discrepancies={discrepanciesState}
          portCallId={portCallId!}
          onDismiss={() => setDiscrepanciesDismissed(true)}
        />
      )}

      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">
            Add document
          </h2>
        </CardHeader>
        <CardContent>
          {isUploading && (
            <div className="mb-4 flex items-center gap-3 rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-800/50">
              <div className="size-5 shrink-0 animate-spin rounded-full border-2 border-mint-200 border-t-mint-500" />
              <p className="text-sm text-slate-700 dark:text-slate-300">
                {phase === "uploading" && "Uploading..."}
                {phase === "parsing" && "Parsing..."}
                {phase === "auditing" && "Audit in progress..."}
              </p>
            </div>
          )}

          {phase === "done" && !showSentinelAlert && (
            <div
              className="mb-4 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-800 dark:border-green-800 dark:bg-green-950/30 dark:text-green-200"
              role="status"
            >
              {uploadMessage ?? "Document processed successfully. No discrepancies detected."}
            </div>
          )}

          {phase === "error" && uploadError && (
            <div
              className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950/30 dark:text-red-300"
              role="alert"
            >
              {uploadError}
            </div>
          )}

          <FileUploader
            category={category}
            onCategoryChange={setCategory}
            onFileSelect={handleFileSelect}
            disabled={isUploading}
            isDragging={isDragging}
            onDragChange={setIsDragging}
          />
        </CardContent>
      </Card>

      {documents.length > 0 && (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">
              Uploaded documents
            </h2>
          </CardHeader>
          <CardContent>
            <ul className="divide-y divide-slate-200 dark:divide-slate-700">
              {documents.map((doc) => (
                <li
                  key={doc.id}
                  className="flex items-center justify-between py-3 first:pt-0 last:pb-0"
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-slate-800 dark:text-slate-100">
                      {doc.filename}
                    </p>
                    <p className="mt-0.5 flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                      <span className="capitalize">{doc.category ?? "—"}</span>
                      <span>•</span>
                      <span
                        className={
                          doc.processing_status === "completed"
                            ? "text-green-600 dark:text-green-400"
                            : doc.processing_status === "failed"
                              ? "text-red-600 dark:text-red-400"
                              : "text-amber-600 dark:text-amber-400"
                        }
                      >
                        {doc.processing_status}
                      </span>
                    </p>
                  </div>
                  <span className="ml-3 shrink-0 text-xs text-slate-400 dark:text-slate-500">
                    {new Date(doc.created_at).toLocaleString()}
                  </span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      <div className="flex gap-3">
        <Link
          to={`/port-calls/${portCallId}/audit`}
          className="text-sm font-medium text-mint-500 hover:text-mint-400 dark:text-mint-400 dark:hover:text-mint-300"
        >
          View Sentinel Audit
        </Link>
      </div>
    </div>
  );
}

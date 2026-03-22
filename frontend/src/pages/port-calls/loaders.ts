import { redirect } from "react-router";
import api, { ApiError } from "@/api/client";
import type {
  PaginatedResponse,
  SingleResponse,
  PortCallResponse,
  DiscrepancyResponse,
  DocumentResponse,
} from "@/api/types";

export type PortCallDetailLoaderData = {
  portCall: PortCallResponse;
  discrepancies: DiscrepancyResponse[];
  discrepanciesError: string | null;
};

export async function portCallDetailLoader({
  params,
}: {
  params: { portCallId?: string };
}): Promise<PortCallDetailLoaderData> {
  const portCallId = params.portCallId;
  if (!portCallId) {
    throw redirect("/port-calls");
  }

  const [portCallResult, discrepanciesResult] = await Promise.allSettled([
    api.get<SingleResponse<PortCallResponse>>(`/port-calls/${portCallId}`),
    api.get<SingleResponse<DiscrepancyResponse[]>>(
      `/port-calls/${portCallId}/discrepancies`
    ),
  ]);

  if (portCallResult.status === "rejected") {
    const err = portCallResult.reason;
    throw new Error(
      err instanceof ApiError ? err.message : "Failed to load port call"
    );
  }

  const portCall = portCallResult.value.data.data;

  let discrepancies: DiscrepancyResponse[] = [];
  let discrepanciesError: string | null = null;

  if (discrepanciesResult.status === "fulfilled") {
    discrepancies = discrepanciesResult.value.data.data ?? [];
  } else {
    const err = discrepanciesResult.reason;
    discrepanciesError =
      err instanceof ApiError ? err.message : "Failed to load Sentinel data";
  }

  return { portCall, discrepancies, discrepanciesError };
}

export type PortCallDocumentsLoaderData = {
  portCall: PortCallResponse;
  portCallId: string;
  documents: DocumentResponse[];
  discrepancies: DiscrepancyResponse[];
  discrepanciesError: string | null;
};

export async function portCallDocumentsLoader({
  params,
}: {
  params: { portCallId?: string };
}): Promise<PortCallDocumentsLoaderData> {
  const portCallId = params.portCallId;
  if (!portCallId) {
    throw redirect("/port-calls");
  }

  const [portCallResult, discrepanciesResult, documentsResult] =
    await Promise.allSettled([
      api.get<SingleResponse<PortCallResponse>>(`/port-calls/${portCallId}`),
      api.get<SingleResponse<DiscrepancyResponse[]>>(
        `/port-calls/${portCallId}/discrepancies`
      ),
      api.get<PaginatedResponse<DocumentResponse>>(
        `/port-calls/${portCallId}/documents`
      ),
    ]);

  if (portCallResult.status === "rejected") {
    const err = portCallResult.reason;
    throw new Error(
      err instanceof ApiError ? err.message : "Failed to load port call"
    );
  }

  const portCall = portCallResult.value.data.data;

  let discrepancies: DiscrepancyResponse[] = [];
  let discrepanciesError: string | null = null;

  if (discrepanciesResult.status === "fulfilled") {
    discrepancies = discrepanciesResult.value.data.data ?? [];
  } else {
    const err = discrepanciesResult.reason;
    discrepanciesError =
      err instanceof ApiError ? err.message : "Failed to load Sentinel data";
  }

  let documents: DocumentResponse[] = [];
  if (documentsResult.status === "fulfilled") {
    documents = documentsResult.value.data.data ?? [];
  }

  return { portCall, portCallId, documents, discrepancies, discrepanciesError };
}

export type PortCallAuditLoaderData = {
  discrepancies: DiscrepancyResponse[];
  portCallId: string;
  error: string | null;
};

export async function portCallAuditLoader({
  params,
}: {
  params: { portCallId?: string };
}): Promise<PortCallAuditLoaderData> {
  const portCallId = params.portCallId;
  if (!portCallId) {
    throw redirect("/port-calls");
  }

  try {
    const res = await api.get<SingleResponse<DiscrepancyResponse[]>>(
      `/port-calls/${portCallId}/discrepancies`
    );
    return {
      discrepancies: res.data.data ?? [],
      portCallId,
      error: null,
    };
  } catch (err) {
    return {
      discrepancies: [],
      portCallId,
      error:
        err instanceof ApiError ? err.message : "Failed to load discrepancies",
    };
  }
}

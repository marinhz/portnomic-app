export type ErrorDetail = {
  code: string;
  message: string;
  details?: Record<string, unknown> | unknown[];
};

export type ErrorResponse = {
  error: ErrorDetail;
};

export type PaginationMeta = {
  total: number;
  page: number;
  per_page: number;
};

export type PaginatedResponse<T> = {
  data: T[];
  meta: PaginationMeta;
};

export type SingleResponse<T> = {
  data: T;
};

/** Sentinel discrepancy from GET /port-calls/{id}/discrepancies */
export type DiscrepancyResponse = {
  id: string;
  tenant_id: string;
  port_call_id: string;
  severity: string;
  description: string;
  estimated_loss: string | null;
  source_documents: string[];
  rule_id: string | null;
  raw_evidence: Record<string, unknown> | null;
  created_at: string;
};

export type LoginRequest = {
  email: string;
  password: string;
};

export type LoginResponse = {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  requires_mfa: boolean;
  mfa_token?: string;
};

export type MfaRequest = {
  mfa_token: string;
  code: string;
};

export type TokenResponse = {
  access_token: string;
  expires_in: number;
};

export type VesselCreate = {
  name: string;
  imo?: string;
  mmsi?: string;
  vessel_type?: string;
  flag?: string;
};

export type VesselUpdate = Partial<VesselCreate>;

export type VesselResponse = {
  id: string;
  name: string;
  imo: string | null;
  mmsi: string | null;
  vessel_type: string | null;
  flag: string | null;
  created_at: string;
  updated_at: string | null;
};

/** Port call creation source: "ai" (parse worker) or "manual" (API). */
export type PortCallSource = "ai" | "manual";

export type PortCallCreate = {
  vessel_id: string;
  port_id: string;
  eta?: string;
  etd?: string;
  status?: string;
  agent_assigned_id?: string | null;
  source?: PortCallSource;
};

export type PortCallUpdate = {
  vessel_id?: string;
  port_id?: string;
  eta?: string;
  etd?: string;
  status?: string;
  agent_assigned_id?: string | null;
  source?: PortCallSource;
};

/** Document category for manual upload */
export type DocumentCategory = "sof" | "da" | "noon_report";

/** Response after manual document upload */
export type DocumentUploadResponse = {
  job_id: string;
  email_id: string;
  status: string;
};

export type PortCallResponse = {
  id: string;
  vessel_id: string;
  port_id: string;
  eta: string | null;
  etd: string | null;
  status: string;
  agent_assigned_id: string | null;
  source: PortCallSource;
  created_at: string;
  updated_at: string | null;
};

export type UserCreate = {
  email: string;
  password: string;
  role_id: string;
  mfa_enabled?: boolean;
};

export type UserUpdate = {
  email?: string;
  role_id?: string;
  is_active?: boolean;
  mfa_enabled?: boolean;
};

export type UserResponse = {
  id: string;
  email: string;
  is_active: boolean;
  mfa_enabled: boolean;
  role_id: string;
  created_at: string;
  last_login_at: string | null;
};

export type RoleCreate = {
  name: string;
  permissions: string[];
};

export type RoleUpdate = {
  name?: string;
  permissions?: string[];
};

export type RoleResponse = {
  id: string;
  name: string;
  permissions: string[];
  created_at: string;
};

// Permissions manifest (GET /admin/permissions)
export type PermissionItem = {
  id: string;
  label: string;
  description: string;
};

export type PermissionModule = {
  id: string;
  label: string;
  permissions: PermissionItem[];
};

export type PermissionsManifest = {
  modules: PermissionModule[];
};

export type TenantCreate = {
  name: string;
  slug: string;
  plan?: "demo" | "starter" | "professional" | "enterprise";
  initial_admin_email?: string;
  initial_admin_password?: string;
};

export type TenantResponse = {
  id: string;
  name: string;
  slug: string;
  settings: Record<string, unknown> | null;
  created_at: string;
};

export type CurrentUser = {
  id: string;
  tenant_id: string;
  email: string;
  role_id: string;
  role_name?: string | null;
  permissions: string[];
  mfa_enabled: boolean;
  is_platform_admin?: boolean;
  tenant_plan?: string | null;
  leakage_detector_enabled?: boolean;
  created_at?: string | null;
  last_login_at?: string | null;
};

export type PortCreate = {
  name: string;
  code: string;
  country?: string | null;
  timezone?: string | null;
  latitude?: number | null;
  longitude?: number | null;
};

export type PortResponse = {
  id: string;
  name: string;
  code: string;
  country: string | null;
  timezone: string | null;
  latitude: number | null;
  longitude: number | null;
  created_at: string;
};

export type EmailListResponse = {
  id: string;
  external_id: string;
  subject: string | null;
  sender: string | null;
  received_at: string | null;
  processing_status: string;
  retry_count: number;
  created_at: string;
  port_call_id: string | null;
};

export type EmailResponse = {
  id: string;
  tenant_id: string;
  port_call_id: string | null;
  external_id: string;
  subject: string | null;
  sender: string | null;
  received_at: string | null;
  processing_status: string;
  ai_raw_output: Record<string, unknown> | null;
  error_reason: string | null;
  prompt_version: string | null;
  retry_count: number;
  created_at: string;
  updated_at: string | null;
  emission_report_id?: string | null;
};

// Tariff types

export type TariffLineItemType = "per_call" | "per_ton" | "per_hour" | "fixed";

export type TariffFormulaLineItem = {
  description: string;
  type: TariffLineItemType;
  rate: number;
  currency: string;
};

export type TariffFormulaConfig = {
  items: TariffFormulaLineItem[];
  tax_rate: number;
  currency: string;
};

export type TariffCreate = {
  port_id: string;
  name: string;
  formula_config: Record<string, unknown>;
  valid_from: string;
  valid_to?: string | null;
};

export type TariffUpdate = Partial<Omit<TariffCreate, "port_id">>;

export type TariffResponse = {
  id: string;
  tenant_id: string;
  port_id: string;
  name: string;
  version: number;
  formula_config: Record<string, unknown>;
  valid_from: string;
  valid_to: string | null;
  created_at: string;
  updated_at: string | null;
};

// Disbursement Account types

export type DALineItem = {
  description: string;
  quantity: number;
  unit_price: number;
  amount: number;
  currency: string;
};

export type DATotals = {
  subtotal: number;
  tax: number;
  total: number;
  currency: string;
};

export type DAGenerateRequest = {
  port_call_id: string;
  type: "proforma" | "final";
};

export type DASendRequest = {
  to_addresses?: string[];
};

export type DAResponse = {
  id: string;
  tenant_id: string;
  port_call_id: string;
  tariff_id: string | null;
  version: number;
  type: string;
  status: string;
  line_items: DALineItem[];
  totals: DATotals;
  currency: string;
  pdf_blob_id: string | null;
  created_at: string;
  updated_at: string | null;
  approved_at: string | null;
  approved_by: string | null;
  sent_at: string | null;
};

export type DAListResponse = {
  id: string;
  port_call_id: string;
  version: number;
  type: string;
  status: string;
  currency: string;
  created_at: string;
  approved_at: string | null;
  sent_at: string | null;
  has_anomalies?: boolean;
};

/** Anomaly from AI Leakage Detector (GET /da/{id}/anomalies) */
export type DAAnomalyResponse = {
  id: string;
  tenant_id: string;
  email_id: string;
  da_id: string | null;
  port_call_id: string;
  rule_id: string;
  severity: "low" | "medium" | "high" | "critical";
  description: string;
  line_item_ref: string | null;
  invoiced_value: number | null;
  expected_value: number | null;
  raw_evidence: Record<string, unknown> | null;
  created_at: string;
};

export type ParseRequest = {
  email_id: string;
};

/** Parse job result can be ParsedEmailResult or emission type with emission_report_id */
export type ParseJobResult =
  | ParsedEmailResult
  | ({
      type: "emission";
      emission_report_id: string;
      extraction?: Record<string, unknown>;
      [key: string]: unknown;
    } & Record<string, unknown>);

export type ParseJobResponse = {
  id: string;
  email_id: string;
  status: string;
  result: ParseJobResult | null;
  error_message: string | null;
  prompt_version: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
};

// Mail Connection / Integrations types

export type MailConnectionResponse = {
  id: string;
  provider: string;
  display_email: string | null;
  status: string;
  error_message: string | null;
  last_sync_at: string | null;
  created_at: string;
  updated_at: string | null;
};

export type ImapConnectionCreate = {
  imap_host: string;
  imap_port: number;
  imap_user: string;
  imap_password: string;
};

export type ParsedLineItem = {
  description: string;
  amount: number;
  currency: string;
  quantity: number | null;
  unit_price: number | null;
};

export type ParsedEmailResult = {
  vessel_name: string | null;
  vessel_imo: string | null;
  port_name: string | null;
  port_code: string | null;
  eta: string | null;
  etd: string | null;
  line_items?: ParsedLineItem[];
  total_amount: number | null;
  currency: string | null;
  summary: string | null;
};

/** Fuel entry from emission extraction (Noon/Bunker report). */
export type EmissionFuelEntry = {
  fuel_type: string;
  consumption_mt: number;
  operational_status: string;
};

/** Emission extraction from ai_raw_output (Noon/Bunker report). */
export type EmissionExtraction = {
  vessel_name?: string | null;
  imo_number?: string | null;
  report_date?: string | null;
  fuel_entries?: EmissionFuelEntry[];
  distance_nm?: number | null;
};

// Emissions / Carbon reporting types

export type EmissionFuelBreakdown = {
  fuel_type: string;
  consumption_mt: number;
  co2_mt: number;
};

export type EmissionReportListResponse = {
  id: string;
  vessel_id: string;
  vessel_name: string | null;
  voyage_id: string | null;
  report_date: string;
  co2_mt: number;
  eua_estimate_eur: number | null;
  compliance_status: "green" | "yellow" | "red";
  verification_status: "verified" | "flagged" | "pending";
  source_email_id: string | null;
  created_at: string;
};

export type EmissionReportDetailResponse = {
  id: string;
  tenant_id: string;
  vessel_id: string;
  vessel_name: string | null;
  vessel_imo: string | null;
  voyage_id: string | null;
  report_date: string;
  co2_mt: number;
  eua_estimate_eur: number | null;
  compliance_status: "green" | "yellow" | "red";
  verification_status: "verified" | "flagged" | "pending";
  fuel_breakdown: EmissionFuelBreakdown[];
  anomaly_flags: { code: string; message: string }[];
  source_email_id: string | null;
  created_at: string;
  updated_at: string | null;
};

// AI Settings types (Task 10.5)

export type AIConfigResponse = {
  id: string;
  tenant_id: string;
  base_url: string | null;
  model: string | null;
  enabled: boolean;
  api_key_configured: boolean;
  created_at: string;
  updated_at: string | null;
};

export type AIConfigPut = {
  api_key?: string | null;
  base_url?: string | null;
  model?: string | null;
  enabled?: boolean;
};

export type AIPromptOverride = {
  parser_type: string;
  prompt_text: string;
  version: string;
};

export type EmissionsSummaryResponse = {
  total_co2_mt: number;
  total_eua_estimate_eur: number | null;
  voyage_count: number;
  compliance: {
    green: number;
    yellow: number;
    red: number;
  };
};

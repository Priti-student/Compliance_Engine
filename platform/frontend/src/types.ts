// TypeScript mirrors of the backend DTOs (subset used by the UI).

export type Role = "admin" | "reviewer" | "officer";

export interface User {
  id: number;
  username: string;
  email?: string | null;
  full_name: string;
  role: Role;
  is_active: boolean;
  last_login_at?: string | null;
  created_at?: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Product {
  id: number;
  generic_name: string;
  brand?: string | null;
  category?: string | null;
  manufacturer?: string | null;
  packer?: string | null;
  importer?: string | null;
  net_quantity_text?: string | null;
  mrp?: string | null;
  batch_no?: string | null;
}

export interface InspectionSummary {
  id: number;
  token: string;
  product: Product | null;
  compliance_status: string;
  workflow_status: string;
  stats: Record<string, number>;
  officer?: User | null;
  reviewer?: User | null;
  reviewed_by?: User | null;
  reviewed_at?: string | null;
  created_at?: string | null;
}

export interface Declaration {
  field_name: string;
  value?: string | null;
  raw_text?: string | null;
  confidence: number;
  method?: string | null;
  source_zone?: string | null;
  qualifiers?: string[];
  rule_id?: string | null;
}

export interface Violation {
  rule_id: string;
  rule_reference?: string | null;
  field_name?: string | null;
  status: string;
  severity: string;
  reason: string;
  evidence: Record<string, unknown>;
}

export interface FontMetric {
  zone_type: string;
  char_height_px_median: number;
  char_height_mm_median: number;
  contrast_ratio: number;
  calibrated: boolean;
}

export interface ReportArtifact {
  report_type: "pdf" | "xlsx" | "json";
  filename: string;
  size_bytes: number;
  created_at?: string;
}

export interface EvidenceItem {
  id: number;
  filename: string;
  mime_type: string;
  size_bytes: number;
  created_at?: string;
}

export interface InspectionDetail extends InspectionSummary {
  advice: string[];
  remarks: string;
  image_name: string;
  engine_scan_id?: string | null;
  declarations: Declaration[];
  violations: Violation[];
  font_metrics: FontMetric[];
  evidence: EvidenceItem[];
  reports: ReportArtifact[];
  compliance_json: Record<string, unknown>;
  updated_at?: string | null;
}

export interface DashboardSummary {
  total_inspections: number;
  status_distribution: Record<string, number>;
  total_products: number;
  active_officers: number;
  total_violations: number;
  total_missing_declarations: number;
  reviewed_count: number;
  compliance_rate_pct: number;
  avg_violations_per_scan: number;
  last_updated?: string;
}

export interface Page<T> {
  total: number;
  page: number;
  size: number;
  items: T[];
}
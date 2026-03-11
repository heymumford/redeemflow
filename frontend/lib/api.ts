const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const AUTH_TOKEN = process.env.NEXT_PUBLIC_AUTH_TOKEN ?? "";

function headers(): HeadersInit {
  const h: HeadersInit = {
    "Content-Type": "application/json",
  };
  if (AUTH_TOKEN) {
    h["Authorization"] = `Bearer ${AUTH_TOKEN}`;
  }
  return h;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...init,
    headers: {
      ...headers(),
      ...init?.headers,
    },
  });

  if (!res.ok) {
    throw new ApiError(res.status, `API ${res.status}: ${res.statusText}`);
  }

  return res.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// --- Types ---

export interface Balance {
  program_code: string;
  points: number;
  estimated_value_dollars: string;
}

export interface PortfolioResponse {
  balances: Balance[];
  total_value_dollars: string;
}

export interface Recommendation {
  program_code: string;
  action: string;
  rationale: string;
  cpp_gain: string;
  points_involved: number;
}

export interface RecommendationsResponse {
  recommendations: Recommendation[];
}

export interface CheckoutResponse {
  session_id: string;
  checkout_url: string;
}

export interface Subscription {
  id: string;
  tier: string;
  status: string;
  current_period_start: string;
  current_period_end: string;
}

export interface SubscriptionResponse {
  subscription: Subscription | null;
}

export interface HealthResponse {
  status: string;
  version: string;
  dependencies: Record<string, string>;
}

export interface SweetSpot {
  program: string;
  program_name: string;
  category: string;
  description: string;
  points_required: number;
  cash_equivalent: string;
  effective_cpp: string;
  rating: string;
  route: string | null;
  cabin: string | null;
}

export interface SweetSpotsResponse {
  count: number;
  sweet_spots: SweetSpot[];
}

export interface GraphSummary {
  total_programs: number;
  total_partnerships: number;
  hub_programs: string[];
  isolated_programs: string[];
  avg_connections: number;
  densest_program: string;
  density: number;
}

export interface ProgramConnectivity {
  program: string;
  outbound_partners: number;
  inbound_partners: number;
  total_connections: number;
  is_hub: boolean;
}

export interface ValuationResponse {
  program_code: string;
  program_name: string;
  aggregated_cpp: string;
  strategy: string;
  source_count: number;
  confidence: string;
}

export interface QuizResult {
  archetype: string;
  description: string;
  confidence: string;
  scores: Record<string, number>;
  recommendations: string[];
}

export interface PathResult {
  route: string;
  hops: number;
  effective_cpp: string;
  source_points_needed: number;
  redemption: string;
  efficiency_score: string;
}

// --- API methods ---

export async function getPortfolio(): Promise<PortfolioResponse> {
  return request<PortfolioResponse>("/api/portfolio");
}

export async function getRecommendations(): Promise<RecommendationsResponse> {
  return request<RecommendationsResponse>("/api/recommendations");
}

export async function createCheckout(
  tier: string = "premium",
): Promise<CheckoutResponse> {
  return request<CheckoutResponse>("/api/billing/checkout", {
    method: "POST",
    body: JSON.stringify({ tier }),
  });
}

export async function getSubscription(): Promise<SubscriptionResponse> {
  return request<SubscriptionResponse>("/api/billing/subscription");
}

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export async function getSweetSpots(
  params?: { category?: string; min_rating?: string },
): Promise<SweetSpotsResponse> {
  const query = new URLSearchParams();
  if (params?.category) query.set("category", params.category);
  if (params?.min_rating) query.set("min_rating", params.min_rating);
  const qs = query.toString();
  return request<SweetSpotsResponse>(`/api/sweet-spots${qs ? `?${qs}` : ""}`);
}

export async function getGraphSummary(): Promise<GraphSummary> {
  return request<GraphSummary>("/api/graph/summary");
}

export async function getProgramConnectivity(
  program: string,
): Promise<ProgramConnectivity> {
  return request<ProgramConnectivity>(`/api/graph/connectivity/${program}`);
}

export async function getValuation(
  program: string,
): Promise<ValuationResponse> {
  return request<ValuationResponse>(`/api/valuations/${program}`);
}

export async function submitQuiz(
  answers: Record<string, string | boolean>,
): Promise<{ result: QuizResult }> {
  return request<{ result: QuizResult }>("/api/strategy-quiz", {
    method: "POST",
    body: JSON.stringify(answers),
  });
}

export async function getTopPaths(
  program: string,
  points: number,
): Promise<{ paths: PathResult[] }> {
  return request<{ paths: PathResult[] }>("/api/paths/top", {
    method: "POST",
    body: JSON.stringify({ program, points }),
  });
}

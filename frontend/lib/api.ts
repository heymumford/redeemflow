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

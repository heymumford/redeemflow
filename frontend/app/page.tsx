"use client";

import { useEffect, useState } from "react";
import type {
  PortfolioResponse,
  RecommendationsResponse,
  SubscriptionResponse,
} from "@/lib/api";
import {
  getPortfolio,
  getRecommendations,
  getSubscription,
} from "@/lib/api";
import PortfolioCard from "@/components/PortfolioCard";
import RecommendationCard from "@/components/RecommendationCard";
import SubscriptionBanner from "@/components/SubscriptionBanner";

export default function Dashboard() {
  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null);
  const [recommendations, setRecommendations] =
    useState<RecommendationsResponse | null>(null);
  const [subscription, setSubscription] =
    useState<SubscriptionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [p, r, s] = await Promise.allSettled([
          getPortfolio(),
          getRecommendations(),
          getSubscription(),
        ]);

        if (p.status === "fulfilled") setPortfolio(p.value);
        if (r.status === "fulfilled") setRecommendations(r.value);
        if (s.status === "fulfilled") setSubscription(s.value);

        const allFailed =
          p.status === "rejected" &&
          r.status === "rejected" &&
          s.status === "rejected";
        if (allFailed) {
          setError("Unable to connect to the API. Check your configuration.");
        }
      } catch {
        setError("An unexpected error occurred.");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-rose-200 border-t-rose-500" />
      </div>
    );
  }

  return (
    <div className="space-y-10">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Your Portfolio</h1>
        <p className="mt-2 text-gray-500">
          Track your points, discover transfer opportunities, and maximize
          redemption value.
        </p>
      </div>

      {/* Subscription Banner */}
      <SubscriptionBanner subscription={subscription?.subscription ?? null} />

      {/* Error */}
      {error && (
        <div
          className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800"
          role="alert"
        >
          {error}
        </div>
      )}

      {/* Portfolio */}
      {portfolio && portfolio.balances.length > 0 && (
        <section>
          <div className="mb-4 flex items-baseline justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Balances</h2>
            <span className="text-sm font-medium text-rose-600">
              Total: ${portfolio.total_value_dollars}
            </span>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {portfolio.balances.map((b) => (
              <PortfolioCard key={b.program_code} balance={b} />
            ))}
          </div>
        </section>
      )}

      {/* Recommendations */}
      {recommendations && recommendations.recommendations.length > 0 && (
        <section>
          <h2 className="mb-4 text-xl font-semibold text-gray-900">
            Recommendations
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {recommendations.recommendations.map((r, i) => (
              <RecommendationCard key={`${r.program_code}-${i}`} recommendation={r} />
            ))}
          </div>
        </section>
      )}

      {/* Empty state */}
      {!error &&
        (!portfolio || portfolio.balances.length === 0) &&
        (!recommendations || recommendations.recommendations.length === 0) && (
          <div className="rounded-2xl border border-dashed border-rose-200 p-12 text-center">
            <p className="text-lg font-medium text-gray-400">
              No portfolio data yet.
            </p>
            <p className="mt-2 text-sm text-gray-400">
              Connect your loyalty programs to get started.
            </p>
          </div>
        )}
    </div>
  );
}

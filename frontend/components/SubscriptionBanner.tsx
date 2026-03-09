"use client";

import { useState } from "react";
import type { Subscription } from "@/lib/api";
import { createCheckout } from "@/lib/api";

interface SubscriptionBannerProps {
  subscription: Subscription | null;
}

export default function SubscriptionBanner({
  subscription,
}: SubscriptionBannerProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubscribe() {
    setLoading(true);
    setError(null);
    try {
      const { checkout_url } = await createCheckout("premium");
      window.location.href = checkout_url;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Checkout failed");
      setLoading(false);
    }
  }

  if (subscription && subscription.status === "active") {
    return (
      <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-medium text-emerald-700">
              Active Subscription
            </div>
            <div className="mt-1 text-lg font-bold capitalize text-emerald-900">
              {subscription.tier} Plan
            </div>
            <div className="mt-1 text-xs text-emerald-600">
              Renews{" "}
              {new Date(subscription.current_period_end).toLocaleDateString()}
            </div>
          </div>
          <div className="rounded-full bg-emerald-200 px-3 py-1 text-xs font-semibold text-emerald-800">
            Active
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-rose-200 bg-gradient-to-r from-rose-50 to-pink-50 p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="text-lg font-bold text-rose-900">
            Unlock Premium Insights
          </div>
          <p className="mt-1 text-sm text-rose-700">
            Get personalized transfer recommendations, real-time valuations, and
            priority support.
          </p>
        </div>
        <div className="flex flex-shrink-0 gap-3">
          <button
            onClick={handleSubscribe}
            disabled={loading}
            className="rounded-full bg-rose-500 px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-rose-600 hover:shadow-md disabled:opacity-50"
          >
            {loading ? "Redirecting..." : "Subscribe"}
          </button>
          <a
            href="https://redeemflow.com/donate"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-full border border-rose-300 bg-white px-6 py-2.5 text-sm font-semibold text-rose-600 transition-all hover:bg-rose-50"
          >
            Donate
          </a>
        </div>
      </div>
      {error && (
        <div className="mt-3 text-sm text-red-600" role="alert">
          {error}
        </div>
      )}
    </div>
  );
}

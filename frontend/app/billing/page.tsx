"use client";

import { useEffect, useState } from "react";
import type { SubscriptionResponse } from "@/lib/api";
import { getSubscription, createCheckout } from "@/lib/api";

export default function BillingPage() {
  const [subscription, setSubscription] =
    useState<SubscriptionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await getSubscription();
        setSubscription(data);
      } catch {
        setError("Unable to load subscription data.");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  async function handleUpgrade() {
    setCheckoutLoading(true);
    setError(null);
    try {
      const { checkout_url } = await createCheckout("premium");
      window.location.href = checkout_url;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Checkout failed");
      setCheckoutLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-rose-200 border-t-rose-500" />
      </div>
    );
  }

  const sub = subscription?.subscription;

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Billing</h1>
        <p className="mt-2 text-gray-500">
          Manage your subscription and payment details.
        </p>
      </div>

      {error && (
        <div
          className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800"
          role="alert"
        >
          {error}
        </div>
      )}

      {/* Current Plan */}
      <section className="rounded-2xl border border-rose-100 bg-white p-8 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900">Current Plan</h2>
        {sub ? (
          <div className="mt-4 space-y-3">
            <div className="flex items-center gap-3">
              <span className="text-2xl font-bold capitalize text-rose-600">
                {sub.tier}
              </span>
              <span
                className={`rounded-full px-3 py-1 text-xs font-semibold ${
                  sub.status === "active"
                    ? "bg-emerald-50 text-emerald-700"
                    : "bg-gray-100 text-gray-600"
                }`}
              >
                {sub.status}
              </span>
            </div>
            <div className="text-sm text-gray-500">
              Current period:{" "}
              {new Date(sub.current_period_start).toLocaleDateString()} -{" "}
              {new Date(sub.current_period_end).toLocaleDateString()}
            </div>
          </div>
        ) : (
          <div className="mt-4">
            <p className="text-sm text-gray-500">
              You are on the free tier.
            </p>
          </div>
        )}
      </section>

      {/* Plans */}
      <section>
        <h2 className="mb-6 text-lg font-semibold text-gray-900">
          Available Plans
        </h2>
        <div className="grid gap-6 sm:grid-cols-2">
          {/* Free */}
          <div className="rounded-2xl border border-gray-200 bg-white p-6">
            <div className="text-sm font-medium uppercase tracking-wider text-gray-400">
              Free
            </div>
            <div className="mt-2 text-3xl font-bold text-gray-900">$0</div>
            <div className="mt-1 text-sm text-gray-500">forever</div>
            <ul className="mt-6 space-y-2 text-sm text-gray-600">
              <li>Portfolio tracking</li>
              <li>Basic valuations</li>
              <li>Transfer graph</li>
            </ul>
            {!sub && (
              <div className="mt-6 rounded-full border border-gray-300 px-4 py-2 text-center text-sm font-medium text-gray-500">
                Current Plan
              </div>
            )}
          </div>

          {/* Premium */}
          <div className="rounded-2xl border-2 border-rose-300 bg-gradient-to-b from-rose-50 to-white p-6">
            <div className="text-sm font-medium uppercase tracking-wider text-rose-500">
              Premium
            </div>
            <div className="mt-2 text-3xl font-bold text-gray-900">$9.99</div>
            <div className="mt-1 text-sm text-gray-500">per month</div>
            <ul className="mt-6 space-y-2 text-sm text-gray-600">
              <li>Everything in Free</li>
              <li>Personalized recommendations</li>
              <li>Real-time valuations</li>
              <li>Priority support</li>
            </ul>
            {sub && sub.tier === "premium" && sub.status === "active" ? (
              <div className="mt-6 rounded-full border border-emerald-300 bg-emerald-50 px-4 py-2 text-center text-sm font-medium text-emerald-700">
                Current Plan
              </div>
            ) : (
              <button
                onClick={handleUpgrade}
                disabled={checkoutLoading}
                className="mt-6 w-full rounded-full bg-rose-500 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-rose-600 hover:shadow-md disabled:opacity-50"
              >
                {checkoutLoading ? "Redirecting..." : "Upgrade to Premium"}
              </button>
            )}
          </div>
        </div>
      </section>

      {/* Donate */}
      <section className="rounded-2xl border border-rose-100 bg-white p-8 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900">
          Support RedeemFlow
        </h2>
        <p className="mt-2 text-sm text-gray-500">
          RedeemFlow is built to help women maximize their travel rewards. Your
          donation keeps this mission going.
        </p>
        <a
          href="https://redeemflow.com/donate"
          target="_blank"
          rel="noopener noreferrer"
          className="mt-4 inline-block rounded-full border border-rose-300 bg-white px-6 py-2.5 text-sm font-semibold text-rose-600 transition-all hover:bg-rose-50"
        >
          Make a Donation
        </a>
      </section>
    </div>
  );
}

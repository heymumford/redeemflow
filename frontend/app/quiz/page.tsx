"use client";

import { useState } from "react";
import { submitQuiz, type QuizResult } from "@/lib/api";

const QUESTIONS = [
  {
    id: "travel_frequency",
    label: "How often do you travel?",
    options: [
      { value: "rare", label: "Rarely (1-2x/year)" },
      { value: "moderate", label: "Moderate (3-5x/year)" },
      { value: "frequent", label: "Frequent (6+/year)" },
    ],
  },
  {
    id: "preferred_cabin",
    label: "Preferred cabin class?",
    options: [
      { value: "economy", label: "Economy" },
      { value: "premium_economy", label: "Premium Economy" },
      { value: "business", label: "Business" },
      { value: "first", label: "First" },
    ],
  },
  {
    id: "redemption_preference",
    label: "How do you prefer to redeem?",
    options: [
      { value: "maximum_value", label: "Maximum value per point" },
      { value: "simple", label: "Simple and convenient" },
      { value: "aspirational", label: "Aspirational experiences" },
    ],
  },
  {
    id: "monthly_spend",
    label: "Monthly credit card spend?",
    options: [
      { value: "low", label: "Under $2,000" },
      { value: "medium", label: "$2,000 - $5,000" },
      { value: "high", label: "Over $5,000" },
    ],
  },
  {
    id: "hotel_priority",
    label: "Hotel priority?",
    options: [
      { value: "budget", label: "Budget-friendly" },
      { value: "midrange", label: "Comfortable mid-range" },
      { value: "luxury", label: "Luxury properties" },
    ],
  },
];

const ARCHETYPE_COLORS: Record<string, string> = {
  maximizer: "bg-emerald-50 border-emerald-200 text-emerald-800",
  simplifier: "bg-blue-50 border-blue-200 text-blue-800",
  aspirational: "bg-purple-50 border-purple-200 text-purple-800",
  accumulator: "bg-amber-50 border-amber-200 text-amber-800",
};

export default function QuizPage() {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [flexibility, setFlexibility] = useState(false);
  const [result, setResult] = useState<QuizResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleAnswer(questionId: string, value: string) {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  }

  async function handleSubmit() {
    if (Object.keys(answers).length < QUESTIONS.length) {
      setError("Please answer all questions");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await submitQuiz({ ...answers, flexibility });
      setResult(data.result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit quiz");
    } finally {
      setLoading(false);
    }
  }

  if (result) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Your Strategy</h1>
        </div>
        <div
          className={`rounded-lg border-2 p-6 ${
            ARCHETYPE_COLORS[result.archetype] ?? "bg-gray-50 border-gray-200"
          }`}
        >
          <h2 className="text-xl font-bold capitalize">{result.archetype}</h2>
          <p className="mt-2 text-sm">{result.description}</p>
          <div className="mt-2 text-xs">
            Confidence: {result.confidence}
          </div>
        </div>
        {result.recommendations.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              Recommendations
            </h3>
            <ul className="space-y-2">
              {result.recommendations.map((rec, i) => (
                <li
                  key={i}
                  className="rounded-md bg-gray-50 p-3 text-sm text-gray-700"
                >
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        )}
        <button
          onClick={() => {
            setResult(null);
            setAnswers({});
          }}
          className="text-sm text-rose-600 hover:text-rose-700"
        >
          Retake Quiz
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Strategy Quiz</h1>
        <p className="mt-1 text-gray-500">
          Discover your travel rewards strategy archetype
        </p>
      </div>

      <div className="space-y-6">
        {QUESTIONS.map((q) => (
          <div key={q.id} className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              {q.label}
            </label>
            <div className="flex flex-wrap gap-2">
              {q.options.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => handleAnswer(q.id, opt.value)}
                  className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                    answers[q.id] === opt.value
                      ? "bg-rose-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        ))}

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="flexibility"
            checked={flexibility}
            onChange={(e) => setFlexibility(e.target.checked)}
            className="rounded border-gray-300 text-rose-600"
          />
          <label htmlFor="flexibility" className="text-sm text-gray-700">
            I have flexible travel dates
          </label>
        </div>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={loading}
        className="rounded-md bg-rose-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-rose-700 disabled:opacity-50"
      >
        {loading ? "Analyzing..." : "Get My Strategy"}
      </button>
    </div>
  );
}

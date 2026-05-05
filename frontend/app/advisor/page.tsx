"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import CarForm from "@/components/CarForm";
import { getRecommendations, type RecommendRequest } from "@/lib/api";

/**
 * Advisor page — renders the 3-step CarForm and redirects to /result
 * with the session_id stored in localStorage.
 */
export default function AdvisorPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(data: RecommendRequest) {
    setLoading(true);
    setError(null);
    try {
      const result = await getRecommendations(data);
      // Store the full result in localStorage so the result page can read it
      localStorage.setItem("solomiro_result", JSON.stringify(result));
      localStorage.setItem("solomiro_current_car", data.current_car);
      router.push("/result");
    } catch (err) {
      setError(
        "No pudimos conectarnos al servidor. Verifica que el backend esté corriendo."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-primary-50">
      {/* Top bar */}
      <header className="bg-primary-900 text-white px-4 py-4 flex items-center gap-3">
        <a href="/" className="text-primary-300 hover:text-white text-sm transition-colors">
          ← Inicio
        </a>
        <span className="text-primary-500">|</span>
        <span className="font-semibold">SoloMiro</span>
      </header>

      <div className="max-w-xl mx-auto px-4 py-12">
        <div className="bg-white rounded-2xl shadow-sm p-6 md:p-8">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-800 rounded-xl px-4 py-3 text-sm mb-6">
              {error}
            </div>
          )}
          <CarForm onSubmit={handleSubmit} loading={loading} />
        </div>
      </div>
    </main>
  );
}

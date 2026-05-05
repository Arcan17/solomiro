"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { RecommendResponse } from "@/lib/api";
import RecommendationCard from "@/components/RecommendationCard";
import LeadCapture from "@/components/LeadCapture";

/**
 * Results page — reads recommendation data from localStorage and renders
 * the full analysis including recommendation cards, current car analysis,
 * and the optional WhatsApp lead capture.
 */
export default function ResultPage() {
  const [result, setResult] = useState<RecommendResponse | null>(null);
  const [currentCar, setCurrentCar] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const raw = localStorage.getItem("solomiro_result");
    const car = localStorage.getItem("solomiro_current_car") ?? "";
    if (raw) {
      try {
        setResult(JSON.parse(raw));
      } catch {
        // ignore parse error
      }
    }
    setCurrentCar(car);
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <main className="min-h-screen bg-primary-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Cargando tu análisis…</p>
        </div>
      </main>
    );
  }

  if (!result) {
    return (
      <main className="min-h-screen bg-primary-50 flex items-center justify-center px-4">
        <div className="text-center max-w-sm">
          <div className="text-5xl mb-4">🔍</div>
          <h2 className="text-xl font-bold text-primary-900 mb-2">
            No hay resultados
          </h2>
          <p className="text-gray-600 text-sm mb-6">
            Parece que aún no has realizado un análisis. Completa el formulario para ver tus opciones.
          </p>
          <Link
            href="/advisor"
            className="bg-primary-600 text-white font-semibold px-6 py-3 rounded-xl hover:bg-primary-700 transition-colors"
          >
            Ir al asesor →
          </Link>
        </div>
      </main>
    );
  }

  function formatCLP(amount: number) {
    return new Intl.NumberFormat("es-CL", {
      style: "currency",
      currency: "CLP",
      maximumFractionDigits: 0,
    }).format(amount);
  }

  return (
    <main className="min-h-screen bg-primary-50">
      {/* Header */}
      <header className="bg-primary-900 text-white px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-primary-300 hover:text-white text-sm transition-colors">
            ← Inicio
          </Link>
          <span className="text-primary-500">|</span>
          <span className="font-semibold">SoloMiro</span>
        </div>
        <Link
          href="/advisor"
          className="text-xs bg-primary-700 hover:bg-primary-600 px-3 py-1.5 rounded-lg transition-colors"
        >
          Nuevo análisis
        </Link>
      </header>

      <div className="max-w-2xl mx-auto px-4 py-10 space-y-8">
        {/* Page title */}
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-primary-900 mb-2">
            Tu análisis personalizado
          </h1>
          <p className="text-gray-600 text-sm">
            Basado en tu auto actual y metas seleccionadas.
          </p>
        </div>

        {/* Current car analysis */}
        <div className="bg-white rounded-2xl shadow-sm border border-primary-100 p-5">
          <h2 className="font-semibold text-primary-900 mb-4">
            Tu auto actual
          </h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Auto</p>
              <p className="font-semibold text-gray-800">
                {result.current_car_analysis.name}
              </p>
            </div>
            <div>
              <p className="text-gray-500">Segmento</p>
              <p className="font-semibold text-gray-800 capitalize">
                {result.current_car_analysis.segment.replace(/_/g, " ")}
              </p>
            </div>
            <div>
              <p className="text-gray-500">Valor estimado</p>
              <p className="font-semibold text-green-700">
                {formatCLP(result.current_car_analysis.estimated_value_clp)}
              </p>
            </div>
            <div>
              <p className="text-gray-500">Consumo estimado</p>
              <p className="font-semibold text-gray-800">
                {result.current_car_analysis.estimated_consumption_kpl} km/L
              </p>
            </div>
          </div>
        </div>

        {/* General verdict */}
        <div className="bg-primary-900 text-white rounded-2xl p-5">
          <h2 className="font-semibold mb-2 text-primary-200 text-sm uppercase tracking-wide">
            Veredicto general IA
          </h2>
          <p className="leading-relaxed text-base">{result.general_verdict}</p>
        </div>

        {/* Recommendation cards */}
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-primary-900">
            Top 3 recomendaciones
          </h2>
          {result.recommendations.map((rec) => (
            <RecommendationCard key={rec.rank} recommendation={rec} />
          ))}
        </div>

        {/* Lead capture */}
        <LeadCapture
          sessionId={result.session_id}
          currentCar={currentCar || result.current_car_analysis.name}
        />

        {/* Disclaimer */}
        <p className="text-xs text-gray-400 text-center pb-4">
          SoloMiro es un asesor independiente. Los precios son referenciales y pueden variar.
          Consulta siempre con el concesionario antes de tomar una decisión.
        </p>
      </div>
    </main>
  );
}

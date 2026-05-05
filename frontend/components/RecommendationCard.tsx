"use client";

import type { CarRecommendation } from "@/lib/api";
import ScoreBar from "./ScoreBar";

interface RecommendationCardProps {
  recommendation: CarRecommendation;
}

const RANK_COLORS: Record<number, string> = {
  1: "bg-yellow-400 text-yellow-900",
  2: "bg-gray-200 text-gray-800",
  3: "bg-amber-600 text-white",
};

const TYPE_LABELS: Record<string, string> = {
  rational: "Racional",
  aspirational: "Aspiracional",
  budget: "Económico",
};

/**
 * Displays a single car recommendation with scores, financial data,
 * pros/cons, and the AI-generated analysis.
 */
export default function RecommendationCard({
  recommendation,
}: RecommendationCardProps) {
  const { car, scores, rank, type } = recommendation;
  const rankColor = RANK_COLORS[rank] ?? "bg-primary-600 text-white";

  function formatCLP(amount: number) {
    return new Intl.NumberFormat("es-CL", {
      style: "currency",
      currency: "CLP",
      maximumFractionDigits: 0,
    }).format(amount);
  }

  return (
    <div className="bg-white rounded-2xl shadow-md border border-primary-100 overflow-hidden">
      {/* Header */}
      <div className="bg-primary-50 px-6 py-4 flex items-center gap-3 border-b border-primary-100">
        <span
          className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-base shrink-0 ${rankColor}`}
        >
          #{rank}
        </span>
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-primary-900 truncate">{car.name}</h3>
          <p className="text-sm text-gray-500">
            {car.year} · {car.condition === "new" ? "Nuevo" : "Usado"}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span className="bg-primary-100 text-primary-700 text-xs font-medium px-2 py-0.5 rounded-full">
            {TYPE_LABELS[type] ?? type}
          </span>
          <span className="text-primary-900 font-bold text-sm">
            {formatCLP(car.price_clp)}
          </span>
        </div>
      </div>

      <div className="px-6 py-5 space-y-5">
        {/* Scores */}
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            Puntajes
          </h4>
          <ScoreBar label="General" value={scores.overall} color="bg-primary-600" />
          <ScoreBar label="Consumo" value={scores.consumption} color="bg-green-500" />
          <ScoreBar label="Reventa" value={scores.resale} color="bg-blue-500" />
          <ScoreBar label="Riesgo" value={scores.risk} color="bg-purple-500" />
          <ScoreBar
            label="Valor/precio"
            value={scores.value_for_money}
            color="bg-orange-400"
          />
          <ScoreBar
            label="Compatibilidad"
            value={scores.compatibility}
            color="bg-teal-500"
          />
        </div>

        {/* Financial summary */}
        <div className="rounded-xl bg-primary-50 p-4 space-y-2">
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            Financiero
          </h4>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Costo cambio</span>
            <span className="font-semibold text-primary-800">
              {formatCLP(recommendation.change_cost_clp)}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Ahorro mensual combustible</span>
            <span className="font-semibold text-green-700">
              {formatCLP(recommendation.monthly_fuel_saving_clp)}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Meses recuperación</span>
            <span className="font-semibold text-primary-800">
              {recommendation.payback_months != null
                ? `${recommendation.payback_months} meses`
                : "N/A"}
            </span>
          </div>
        </div>

        {/* Pros / Cons */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <h4 className="text-xs font-semibold text-green-700 uppercase tracking-wide mb-2">
              Pros
            </h4>
            <ul className="space-y-1">
              {recommendation.pros.map((pro, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                  <span className="text-green-500 mt-0.5">✓</span>
                  <span>{pro}</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className="text-xs font-semibold text-red-600 uppercase tracking-wide mb-2">
              Contras
            </h4>
            <ul className="space-y-1">
              {recommendation.cons.map((con, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                  <span className="text-red-400 mt-0.5">✗</span>
                  <span>{con}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* AI analysis */}
        {recommendation.ai_analysis && (
          <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
            <h4 className="text-xs font-semibold text-blue-700 uppercase tracking-wide mb-2">
              Análisis IA
            </h4>
            <p className="text-sm text-blue-900 leading-relaxed">
              {recommendation.ai_analysis}
            </p>
          </div>
        )}

        {/* Verdict */}
        <div className="border-t border-gray-100 pt-4">
          <p className="text-sm font-medium text-primary-800 italic">
            {recommendation.verdict}
          </p>
          {recommendation.not_recommended_if && (
            <p className="text-xs text-gray-500 mt-1">
              <span className="font-semibold">No recomendado si:</span>{" "}
              {recommendation.not_recommended_if}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

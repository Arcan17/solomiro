"use client";

import { useState } from "react";
import type { RecommendRequest } from "@/lib/api";

type Step = 1 | 2 | 3;

const GOAL_OPTIONS = [
  { key: "lower_consumption", label: "Menor consumo de combustible" },
  { key: "better_resale", label: "Mejor precio de reventa" },
  { key: "hybrid", label: "Quiero un híbrido o eléctrico" },
  { key: "more_space", label: "Más espacio interior" },
  { key: "more_equipment", label: "Más equipamiento / tecnología" },
  { key: "lower_payment", label: "Cuota o precio más bajo" },
  { key: "more_power", label: "Más potencia y rendimiento" },
  { key: "less_risk", label: "Menos riesgo / más confiabilidad" },
];

const BUDGET_OPTIONS = [
  { key: "0_to_3M", label: "Hasta $3 millones" },
  { key: "3_to_6M", label: "$3 a $6 millones" },
  { key: "6_to_10M", label: "$6 a $10 millones" },
  { key: "10M_plus", label: "Más de $10 millones" },
  { key: "unknown", label: "No sé / sin límite" },
];

const DRIVING_STYLE_OPTIONS = [
  { key: "city", label: "Ciudad" },
  { key: "highway", label: "Carretera" },
  { key: "mixed", label: "Mixto" },
  { key: "hills", label: "Cerros / caminos" },
];

interface CarFormProps {
  onSubmit: (data: RecommendRequest) => Promise<void>;
  loading: boolean;
}

/**
 * Multi-step car preference form.
 * Step 1: Current car text input.
 * Step 2: Goals (multi-select) and car type.
 * Step 3: Budget, monthly km, driving style, and home charging option.
 */
export default function CarForm({ onSubmit, loading }: CarFormProps) {
  const [step, setStep] = useState<Step>(1);
  const [currentCar, setCurrentCar] = useState("");
  const [goals, setGoals] = useState<string[]>([]);
  const [carType, setCarType] = useState<"new" | "used" | "both">("both");
  const [budgetRange, setBudgetRange] = useState<RecommendRequest["budget_range"]>("unknown");
  const [monthlyKm, setMonthlyKm] = useState<number>(1000);
  const [drivingStyle, setDrivingStyle] = useState<RecommendRequest["driving_style"]>("mixed");
  const [canChargeAtHome, setCanChargeAtHome] = useState(false);

  function toggleGoal(key: string) {
    setGoals((prev) =>
      prev.includes(key) ? prev.filter((g) => g !== key) : [...prev, key]
    );
  }

  async function handleFinalSubmit(e: React.FormEvent) {
    e.preventDefault();
    await onSubmit({
      current_car: currentCar,
      goals: goals.length > 0 ? goals : ["lower_consumption"],
      car_type: carType,
      budget_range: budgetRange,
      monthly_km: monthlyKm,
      driving_style: drivingStyle,
      can_charge_at_home: canChargeAtHome,
    });
  }

  const progressPct = ((step - 1) / 2) * 100 + 33.3;

  return (
    <div className="w-full max-w-xl mx-auto">
      {/* Progress bar */}
      <div className="mb-8">
        <div className="flex justify-between text-sm text-gray-500 mb-2">
          <span>Paso {step} de 3</span>
          <span>{Math.round(progressPct)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-primary-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      {/* Step 1 */}
      {step === 1 && (
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-primary-900 mb-2">
              ¿Qué auto tienes?
            </h2>
            <p className="text-gray-600 text-sm">
              Escribe la marca, modelo y año de tu auto actual.
            </p>
          </div>
          <input
            type="text"
            value={currentCar}
            onChange={(e) => setCurrentCar(e.target.value)}
            placeholder="Ej: Toyota RAV4 2020"
            className="w-full border border-gray-300 rounded-xl px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          <button
            onClick={() => setStep(2)}
            disabled={!currentCar.trim()}
            className="w-full bg-primary-600 text-white font-semibold py-3.5 rounded-xl hover:bg-primary-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Siguiente →
          </button>
        </div>
      )}

      {/* Step 2 */}
      {step === 2 && (
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-primary-900 mb-2">
              ¿Qué quieres mejorar?
            </h2>
            <p className="text-gray-600 text-sm">
              Selecciona una o más metas para tu próximo auto.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {GOAL_OPTIONS.map((opt) => (
              <button
                key={opt.key}
                type="button"
                onClick={() => toggleGoal(opt.key)}
                className={`text-left px-4 py-3 rounded-xl border text-sm transition-colors ${
                  goals.includes(opt.key)
                    ? "bg-primary-600 text-white border-primary-600"
                    : "border-gray-300 text-gray-700 hover:border-primary-400"
                }`}
              >
                {goals.includes(opt.key) ? "✓ " : ""}
                {opt.label}
              </button>
            ))}
          </div>

          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">Tipo de auto</p>
            <div className="flex gap-3">
              {(["new", "used", "both"] as const).map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setCarType(t)}
                  className={`flex-1 py-2.5 rounded-xl border text-sm font-medium transition-colors ${
                    carType === t
                      ? "bg-primary-600 text-white border-primary-600"
                      : "border-gray-300 text-gray-700 hover:border-primary-400"
                  }`}
                >
                  {t === "new" ? "Nuevos" : t === "used" ? "Usados" : "Ambos"}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => setStep(1)}
              className="flex-1 border border-gray-300 text-gray-600 py-3 rounded-xl text-sm hover:bg-gray-50 transition-colors"
            >
              ← Atrás
            </button>
            <button
              onClick={() => setStep(3)}
              className="flex-1 bg-primary-600 text-white font-semibold py-3 rounded-xl hover:bg-primary-700 transition-colors"
            >
              Siguiente →
            </button>
          </div>
        </div>
      )}

      {/* Step 3 */}
      {step === 3 && (
        <form onSubmit={handleFinalSubmit} className="space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-primary-900 mb-2">
              Detalles finales
            </h2>
            <p className="text-gray-600 text-sm">
              Estos datos nos ayudan a afinar el análisis financiero.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Presupuesto para el cambio
            </label>
            <select
              value={budgetRange}
              onChange={(e) => setBudgetRange(e.target.value as RecommendRequest["budget_range"])}
              className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {BUDGET_OPTIONS.map((opt) => (
                <option key={opt.key} value={opt.key}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Kilómetros mensuales aproximados
            </label>
            <input
              type="number"
              min={0}
              max={50000}
              value={monthlyKm}
              onChange={(e) => setMonthlyKm(parseInt(e.target.value) || 1000)}
              className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Estilo de manejo principal
            </label>
            <div className="grid grid-cols-2 gap-2">
              {DRIVING_STYLE_OPTIONS.map((opt) => (
                <button
                  key={opt.key}
                  type="button"
                  onClick={() => setDrivingStyle(opt.key as RecommendRequest["driving_style"])}
                  className={`py-2.5 rounded-xl border text-sm transition-colors ${
                    drivingStyle === opt.key
                      ? "bg-primary-600 text-white border-primary-600"
                      : "border-gray-300 text-gray-700 hover:border-primary-400"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-3 bg-yellow-50 border border-yellow-200 rounded-xl px-4 py-3">
            <input
              type="checkbox"
              id="homeCharging"
              checked={canChargeAtHome}
              onChange={(e) => setCanChargeAtHome(e.target.checked)}
              className="w-4 h-4 accent-primary-600"
            />
            <label htmlFor="homeCharging" className="text-sm text-gray-700">
              Puedo instalar un cargador en casa (para eléctricos/PHEV)
            </label>
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setStep(2)}
              className="flex-1 border border-gray-300 text-gray-600 py-3 rounded-xl text-sm hover:bg-gray-50 transition-colors"
            >
              ← Atrás
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-primary-600 text-white font-semibold py-3 rounded-xl hover:bg-primary-700 disabled:opacity-50 transition-colors"
            >
              {loading ? "Analizando…" : "Ver mis opciones →"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

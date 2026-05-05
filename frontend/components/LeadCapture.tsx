"use client";

import { useState } from "react";
import { submitLead, type LeadRequest } from "@/lib/api";

interface LeadCaptureProps {
  sessionId: string;
  currentCar: string;
}

/**
 * Optional WhatsApp lead capture form shown at the bottom of the results page.
 * Submits to the /leads endpoint and shows a confirmation message on success.
 */
export default function LeadCapture({ sessionId, currentCar }: LeadCaptureProps) {
  const [open, setOpen] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<Omit<LeadRequest, "session_id" | "current_car">>({
    name: "",
    whatsapp: "",
    city: "",
    buy_timeframe: "",
    budget_clp: undefined,
  });

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: name === "budget_clp" ? (value ? parseInt(value) : undefined) : value,
    }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.whatsapp) return;
    setLoading(true);
    setError(null);
    try {
      await submitLead({
        session_id: sessionId,
        current_car: currentCar,
        ...form,
      });
      setSubmitted(true);
    } catch (err) {
      setError("Hubo un error al enviar. Inténtalo de nuevo.");
    } finally {
      setLoading(false);
    }
  }

  if (submitted) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-2xl p-6 text-center">
        <div className="text-3xl mb-2">✅</div>
        <h3 className="font-bold text-green-800 text-lg mb-1">
          ¡Listo! Te contactaremos pronto.
        </h3>
        <p className="text-green-700 text-sm">
          Un asesor de SoloMiro te escribirá a tu WhatsApp para ayudarte.
        </p>
      </div>
    );
  }

  if (!open) {
    return (
      <div className="bg-primary-50 border border-primary-200 rounded-2xl p-6 text-center">
        <h3 className="font-bold text-primary-900 text-lg mb-2">
          ¿Quieres que un asesor te ayude?
        </h3>
        <p className="text-gray-600 text-sm mb-4">
          Deja tu WhatsApp y te contactamos sin compromiso para guiarte en el proceso.
        </p>
        <button
          onClick={() => setOpen(true)}
          className="bg-green-600 text-white font-semibold px-6 py-3 rounded-xl hover:bg-green-700 transition-colors"
        >
          Sí, quiero asesoría gratis
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white border border-primary-200 rounded-2xl p-6">
      <h3 className="font-bold text-primary-900 text-lg mb-4">
        Déjanos tus datos
      </h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Nombre (opcional)
          </label>
          <input
            type="text"
            name="name"
            value={form.name}
            onChange={handleChange}
            placeholder="Tu nombre"
            className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            WhatsApp <span className="text-red-500">*</span>
          </label>
          <input
            type="tel"
            name="whatsapp"
            value={form.whatsapp}
            onChange={handleChange}
            placeholder="+56 9 1234 5678"
            required
            className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Ciudad (opcional)
          </label>
          <input
            type="text"
            name="city"
            value={form.city}
            onChange={handleChange}
            placeholder="Ej: Santiago, Valparaíso"
            className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            ¿Cuándo planeas comprar? (opcional)
          </label>
          <select
            name="buy_timeframe"
            value={form.buy_timeframe}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">Selecciona…</option>
            <option value="immediately">De inmediato</option>
            <option value="1_month">En 1 mes</option>
            <option value="3_months">En 3 meses</option>
            <option value="6_months">En 6 meses</option>
            <option value="exploring">Solo explorando</option>
          </select>
        </div>

        {error && <p className="text-red-600 text-sm">{error}</p>}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-green-600 text-white font-semibold py-3 rounded-xl hover:bg-green-700 disabled:opacity-50 transition-colors"
          >
            {loading ? "Enviando…" : "Enviar"}
          </button>
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="px-4 py-3 border border-gray-300 rounded-xl text-sm text-gray-600 hover:bg-gray-50 transition-colors"
          >
            Cancelar
          </button>
        </div>
      </form>
    </div>
  );
}

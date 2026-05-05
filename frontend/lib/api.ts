const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// TypeScript interfaces matching backend Pydantic schemas
// ---------------------------------------------------------------------------

export interface RecommendRequest {
  current_car: string;
  goals: string[];
  car_type: "new" | "used" | "both";
  budget_range:
    | "0_to_3M"
    | "3_to_6M"
    | "6_to_10M"
    | "10M_plus"
    | "unknown";
  monthly_km?: number;
  driving_style?: "city" | "highway" | "mixed" | "hills";
  can_charge_at_home?: boolean;
}

export interface CarScore {
  overall: number;
  consumption: number;
  resale: number;
  risk: number;
  value_for_money: number;
  compatibility: number;
}

export interface CarRecommendation {
  rank: number;
  type: string;
  car: Car;
  scores: CarScore;
  change_cost_clp: number;
  monthly_fuel_saving_clp: number;
  payback_months: number | null;
  pros: string[];
  cons: string[];
  verdict: string;
  not_recommended_if: string;
  ai_analysis: string;
}

export interface RecommendResponse {
  session_id: string;
  current_car_analysis: {
    name: string;
    estimated_value_clp: number;
    segment: string;
    estimated_consumption_kpl: number;
  };
  recommendations: CarRecommendation[];
  general_verdict: string;
}

export interface Car {
  id: number;
  name: string;
  brand: string;
  model: string;
  year: number;
  segment: string;
  condition: "new" | "used";
  price_clp: number;
  fuel_type: string;
  consumption_kpl: number | null;
  consumption_kwh100km: number | null;
  range_km: number | null;
  power_hp: number;
  transmission: string;
  seats: number;
  trunk_liters: number;
  tags: string[];
  reliability_score: number;
  resale_score: number;
  parts_availability_score: number;
  maintenance_cost_score: number;
  safety_score: number;
  equipment_score: number;
  requires_home_charging: boolean;
  not_recommended_if: string;
}

export interface LeadRequest {
  session_id: string;
  name?: string;
  whatsapp: string;
  current_car: string;
  budget_clp?: number;
  city?: string;
  buy_timeframe?: string;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/**
 * Submit car preferences and receive AI-powered recommendations.
 */
export async function getRecommendations(
  data: RecommendRequest
): Promise<RecommendResponse> {
  const res = await fetch(`${API_URL}/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Recommendation request failed: ${err}`);
  }
  return res.json();
}

/**
 * Submit a WhatsApp lead capture form.
 */
export async function submitLead(data: LeadRequest): Promise<void> {
  const res = await fetch(`${API_URL}/leads`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Lead submission failed: ${err}`);
  }
}

/**
 * Fetch the full car catalogue.
 */
export async function getCars(): Promise<Car[]> {
  const res = await fetch(`${API_URL}/cars`);
  if (!res.ok) {
    throw new Error("Failed to fetch car catalogue");
  }
  return res.json();
}

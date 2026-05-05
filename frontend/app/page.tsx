import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="min-h-screen flex flex-col">
      {/* Hero */}
      <section className="bg-primary-900 text-white px-4 py-20 flex flex-col items-center text-center">
        <div className="max-w-2xl mx-auto">
          <div className="inline-block bg-primary-700 text-primary-100 text-sm font-medium px-3 py-1 rounded-full mb-6">
            Gratis · Sin registro · Chile
          </div>
          <h1 className="text-4xl md:text-5xl font-bold leading-tight mb-4">
            ¿Te conviene cambiar tu auto?
          </h1>
          <p className="text-lg md:text-xl text-primary-200 mb-8 leading-relaxed">
            Dinos qué tienes y qué quieres mejorar. En menos de 1 minuto te
            decimos si vale la pena y a cuál cambiarte.
          </p>
          <Link
            href="/advisor"
            className="inline-block bg-white text-primary-700 font-semibold px-8 py-4 rounded-xl shadow-lg hover:bg-primary-50 transition-colors text-lg"
          >
            Empezar análisis gratis →
          </Link>
        </div>
      </section>

      {/* Benefits */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
          <BenefitCard
            icon="🚫"
            title="Sin registro"
            description="No necesitas crear cuenta ni entregar tus datos para ver los resultados."
          />
          <BenefitCard
            icon="⚡"
            title="Análisis en segundos"
            description="Nuestro motor IA evalúa consumo, reventa, riesgo y valor en tiempo real."
          />
          <BenefitCard
            icon="🇨🇱"
            title="Opciones reales en Chile"
            description="Precios en pesos chilenos. Solo autos disponibles en el mercado local."
          />
        </div>
      </section>

      {/* How it works */}
      <section className="py-16 px-4 bg-primary-50">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl font-bold text-primary-900 mb-10">
            ¿Cómo funciona?
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <StepCard
              number="1"
              title="Cuéntanos tu auto"
              description='Escribe el auto que tienes ahora, por ejemplo "Toyota RAV4 2020".'
            />
            <StepCard
              number="2"
              title="Elige tus metas"
              description="Menor consumo, mejor reventa, más espacio... tú decides qué importa."
            />
            <StepCard
              number="3"
              title="Recibe tu análisis"
              description="Top 3 opciones con costos, ahorros y análisis IA personalizado."
            />
          </div>
          <div className="mt-10">
            <Link
              href="/advisor"
              className="inline-block bg-primary-600 text-white font-semibold px-8 py-4 rounded-xl shadow-md hover:bg-primary-700 transition-colors text-lg"
            >
              Empezar ahora
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-primary-900 text-primary-300 text-center py-6 text-sm mt-auto">
        SoloMiro &copy; 2024 — Asesor independiente. No vendemos autos.
      </footer>
    </main>
  );
}

function BenefitCard({
  icon,
  title,
  description,
}: {
  icon: string;
  title: string;
  description: string;
}) {
  return (
    <div className="flex flex-col items-center text-center p-6 rounded-2xl border border-primary-100 hover:shadow-md transition-shadow">
      <span className="text-4xl mb-4">{icon}</span>
      <h3 className="text-lg font-semibold text-primary-900 mb-2">{title}</h3>
      <p className="text-gray-600 text-sm leading-relaxed">{description}</p>
    </div>
  );
}

function StepCard({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm text-left">
      <div className="w-10 h-10 bg-primary-600 text-white rounded-full flex items-center justify-center font-bold text-lg mb-4">
        {number}
      </div>
      <h3 className="font-semibold text-primary-900 mb-2">{title}</h3>
      <p className="text-gray-600 text-sm">{description}</p>
    </div>
  );
}

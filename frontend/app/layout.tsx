import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "SoloMiro — ¿Te conviene cambiar tu auto?",
  description:
    "Asesor de autos impulsado por IA para el mercado chileno. Descubre si vale la pena cambiar tu auto y a cuál.",
  keywords: ["autos Chile", "cambio de auto", "asesor automotriz", "comparar autos"],
  openGraph: {
    title: "SoloMiro — ¿Te conviene cambiar tu auto?",
    description:
      "Análisis en segundos. Opciones reales en Chile. Sin registro.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body className={inter.className}>{children}</body>
    </html>
  );
}

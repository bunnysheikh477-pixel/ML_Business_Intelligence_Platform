import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'Northstar BI — Business Intelligence', description: 'A modern ML-powered business intelligence workspace.' };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }

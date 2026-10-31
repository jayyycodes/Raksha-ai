import type { Metadata } from 'next';
import { Source_Serif_4, IBM_Plex_Sans } from 'next/font/google';
import './globals.css';
import { AppShell } from '@/components/shell/AppShell';

const sourceSerif = Source_Serif_4({
  subsets: ['latin'],
  variable: '--font-source-serif-4',
  display: 'swap',
});

const ibmPlexSans = IBM_Plex_Sans({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-ibm-plex-sans',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Raksha AI — Intelligence Analyst Workspace',
  description: 'Palantir-inspired open-source threat monitoring and situational awareness platform for India.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${sourceSerif.variable} ${ibmPlexSans.variable}`}>
      <body className="min-h-screen bg-canvas text-text-primary">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}

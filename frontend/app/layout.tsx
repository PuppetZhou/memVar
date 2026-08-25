import type { Metadata } from "next";
import "molstar/build/viewer/molstar.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "memVar | Membrane protein evidence portal",
  description: "A canonical protein-centric evidence portal for reviewed human membrane proteins.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main-content">Skip to content</a>
        <header className="site-header">
          <div className="shell header-inner">
            <div className="header-brand-lockup"><a className="brand" href="/" aria-label="memVar home">mem<span>Var</span></a><p>Canonical protein-centric evidence portal</p></div>
            <nav className="site-nav" aria-label="Primary navigation"><a href="/">Home</a><a href="/about/data-sources">Data sources</a></nav>
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}

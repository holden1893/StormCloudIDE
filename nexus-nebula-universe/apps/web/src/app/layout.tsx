import "./globals.css";

export const metadata = {
  title: "Nexus Nebula Universe",
  description: "AI-powered creation platform with a LangGraph multi-agent swarm + marketplace."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="max-w-6xl mx-auto px-4 py-6">{children}</div>
      </body>
    </html>
  );
}

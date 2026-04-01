import { FormEvent, useEffect, useMemo, useState } from "react";

type OptionResult = {
  callPrice: number;
  putPrice: number;
};

type FormState = {
  spot: number;
  strike: number;
  rate: number;
  dividendYield: number;
  volatility: number;
  maturity: number;
};

type OptionTab = "european" | "basket" | "asian" | "american";

const initialForm: FormState = {
  spot: 100,
  strike: 100,
  rate: 0.05,
  dividendYield: 0.02,
  volatility: 0.2,
  maturity: 1
};

async function fetchEuropeanOption(data: FormState): Promise<OptionResult> {
  const response = await fetch("/api/european-option", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Python pricing service error");
  }

  const payload = (await response.json()) as OptionResult;
  return payload;
}

function formatNumber(value: number): string {
  return Number.isFinite(value) ? value.toFixed(4) : "-";
}

export default function App() {
  const [activeTab, setActiveTab] = useState<OptionTab>("european");
  const [form, setForm] = useState<FormState>(initialForm);
  const [result, setResult] = useState<OptionResult | null>(null);
  const [error, setError] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const assumptions = useMemo(
    () => [
      "标的资产价格服从对数正态分布",
      "无摩擦市场，允许连续交易",
      "无套利机会，且可按无风险利率借贷",
    ],
    []
  );

  useEffect(() => {
    void runPricing(initialForm);
  }, []);

  function updateField<K extends keyof FormState>(key: K, value: number) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function validate(data: FormState): string {
    if (data.spot <= 0) return "Spot price 必须大于 0";
    if (data.strike <= 0) return "Strike price 必须大于 0";
    if (data.volatility <= 0) return "Volatility 必须大于 0";
    if (data.maturity <= 0) return "Time to maturity 必须大于 0";
    return "";
  }

  async function runPricing(data: FormState) {
    try {
      setIsLoading(true);
      const priced = await fetchEuropeanOption(data);
      setResult(priced);
      setError("");
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "计算失败，请检查 Python 服务是否启动");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const validationError = validate(form);
    setError(validationError);

    if (validationError) {
      setResult(null);
      return;
    }

    await runPricing(form);
  }

  async function handleReset() {
    setForm(initialForm);
    setError("");
    await runPricing(initialForm);
  }

  const tabItems: Array<{ key: OptionTab; label: string }> = [
    { key: "european", label: "European" },
    { key: "basket", label: "Basket" },
    { key: "asian", label: "Asian" },
    { key: "american", label: "American" }
  ];

  return (
    <main className="page">
      <section className="hero-card">
        <nav className="tabs" aria-label="Option type tabs">
          {tabItems.map((tab) => (
            <button
              key={tab.key}
              type="button"
              className={`tab-btn ${activeTab === tab.key ? "active" : ""}`}
              onClick={() => setActiveTab(tab.key)}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        <header className="hero-header">
          <h1>
            {activeTab === "european"
              ? "European Option Pricer"
              : activeTab === "basket"
                ? "Basket Option Pricer"
                : activeTab === "asian"
                  ? "Asian Option Pricer"
                  : "American Option Pricer"}
          </h1>
        </header>

        {activeTab === "european" ? (
          <>
            <form className="pricing-form" onSubmit={handleSubmit}>
              <label>
                Spot Price (S)
                <input
                  type="number"
                  step="0.01"
                  value={form.spot}
                  onChange={(e) => updateField("spot", Number(e.target.value))}
                />
              </label>

              <label>
                Strike Price (K)
                <input
                  type="number"
                  step="0.01"
                  value={form.strike}
                  onChange={(e) => updateField("strike", Number(e.target.value))}
                />
              </label>

              <label>
                Risk-free Rate (r)
                <input
                  type="number"
                  step="0.001"
                  value={form.rate}
                  onChange={(e) => updateField("rate", Number(e.target.value))}
                />
              </label>

              <label>
                Dividend Yield (q)
                <input
                  type="number"
                  step="0.001"
                  value={form.dividendYield}
                  onChange={(e) => updateField("dividendYield", Number(e.target.value))}
                />
              </label>

              <label>
                Volatility (sigma)
                <input
                  type="number"
                  step="0.001"
                  value={form.volatility}
                  onChange={(e) => updateField("volatility", Number(e.target.value))}
                />
              </label>

              <label>
                Time to Maturity (T, years)
                <input
                  type="number"
                  step="0.01"
                  value={form.maturity}
                  onChange={(e) => updateField("maturity", Number(e.target.value))}
                />
              </label>

              <div className="actions">
                <button type="submit" disabled={isLoading}>
                  {isLoading ? "Calculating..." : "Calculate"}
                </button>
                <button type="button" className="secondary" onClick={() => void handleReset()} disabled={isLoading}>
                  Reset
                </button>
              </div>
            </form>

            {error ? <p className="error">{error}</p> : null}

            <section className="result-grid" aria-live="polite">
              <article>
                <p className="metric">Call Price</p>
                <p className="value">{result ? formatNumber(result.callPrice) : "-"}</p>
              </article>
              <article>
                <p className="metric">Put Price</p>
                <p className="value">{result ? formatNumber(result.putPrice) : "-"}</p>
              </article>
            </section>
          </>
        ) : (
          <section className="placeholder-panel">
            <h3>{tabItems.find((tab) => tab.key === activeTab)?.label} Option</h3>
            <p>该标签页的计算逻辑稍后接入，当前仅完成页面结构。</p>
          </section>
        )}
      </section>

      <aside className="assumption-card">
        <h2>Model Assumptions</h2>
        <ul>
          {assumptions.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </aside>
    </main>
  );
}

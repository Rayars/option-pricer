import { FormEvent, useEffect, useMemo, useState } from "react";

type OptionResult = {
  callPrice: number;
  putPrice: number;
};

type ImpliedVolatilityResult = {
  impliedVolatility: number;
};

type AsianOptionResult = {
  geometricValue: number;
  standardMcValue: number;
  controlVariateMcValue: number;
  standardMcConfidenceInterval: [number, number];
  controlVariateConfidenceInterval: [number, number];
};

type AmericanOptionResult = {
  price: number;
};

type FormState = {
  spot: string;
  strike: string;
  rate: string;
  dividendYield: string;
  volatility: string;
  maturity: string;
};

type PricingPayload = {
  spot: number;
  strike: number;
  rate: number;
  dividendYield: number;
  volatility: number;
  maturity: number;
};

type ImpliedVolatilityFormState = {
  spot: string;
  strike: string;
  rate: string;
  dividendYield: string;
  maturity: string;
  marketPrice: string;
  optionType: "call" | "put";
};

type ImpliedVolatilityPayload = {
  spot: number;
  strike: number;
  rate: number;
  dividendYield: number;
  maturity: number;
  marketPrice: number;
  optionType: "call" | "put";
};

type AsianFormState = {
  spot: string;
  strike: string;
  rate: string;
  volatility: string;
  maturity: string;
  nSteps: string;
  nPaths: string;
  optionType: "call" | "put";
};

type AsianPricingPayload = {
  spot: number;
  strike: number;
  rate: number;
  volatility: number;
  maturity: number;
  nSteps: number;
  nPaths: number;
  optionType: "call" | "put";
};

type AmericanFormState = {
  spot: string;
  strike: string;
  rate: string;
  volatility: string;
  maturity: string;
  nSteps: string;
  optionType: "call" | "put";
};

type AmericanPricingPayload = {
  spot: number;
  strike: number;
  rate: number;
  volatility: number;
  maturity: number;
  nSteps: number;
  optionType: "call" | "put";
};

type OptionTab = "european" | "basket" | "asian" | "american";

const initialForm: FormState = {
  spot: "100",
  strike: "100",
  rate: "0.05",
  dividendYield: "0.02",
  volatility: "0.2",
  maturity: "1"
};

const initialIvForm: ImpliedVolatilityFormState = {
  spot: "100",
  strike: "100",
  rate: "0.05",
  dividendYield: "0.02",
  maturity: "1",
  marketPrice: "10",
  optionType: "call"
};

const initialAsianForm: AsianFormState = {
  spot: "100",
  strike: "100",
  rate: "0.05",
  volatility: "0.2",
  maturity: "1",
  nSteps: "50",
  nPaths: "10000",
  optionType: "call"
};

const initialAmericanForm: AmericanFormState = {
  spot: "100",
  strike: "100",
  rate: "0.05",
  volatility: "0.2",
  maturity: "1",
  nSteps: "50",
  optionType: "put"
};

async function fetchEuropeanOption(data: PricingPayload): Promise<OptionResult> {
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

async function fetchImpliedVolatility(data: ImpliedVolatilityPayload): Promise<ImpliedVolatilityResult> {
  const response = await fetch("/api/implied-volatility", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Python implied volatility service error");
  }

  const payload = (await response.json()) as ImpliedVolatilityResult;
  return payload;
}

async function fetchAsianOption(data: AsianPricingPayload): Promise<AsianOptionResult> {
  const response = await fetch("/api/asian-option", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Python asian option service error");
  }

  const payload = (await response.json()) as AsianOptionResult;
  return payload;
}

async function fetchAmericanOption(data: AmericanPricingPayload): Promise<AmericanOptionResult> {
  const response = await fetch("/api/american-option", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Python american option service error");
  }

  const payload = (await response.json()) as AmericanOptionResult;
  return payload;
}

function formatNumber(value: number): string {
  return Number.isFinite(value) ? value.toFixed(4) : "-";
}

export default function App() {
  const [activeTab, setActiveTab] = useState<OptionTab>("european");
  const [form, setForm] = useState<FormState>(initialForm);
  const [result, setResult] = useState<OptionResult | null>(null);
  const [ivForm, setIvForm] = useState<ImpliedVolatilityFormState>(initialIvForm);
  const [ivResult, setIvResult] = useState<ImpliedVolatilityResult | null>(null);
  const [ivError, setIvError] = useState<string>("");
  const [isIvLoading, setIsIvLoading] = useState<boolean>(false);
  const [asianForm, setAsianForm] = useState<AsianFormState>(initialAsianForm);
  const [asianResult, setAsianResult] = useState<AsianOptionResult | null>(null);
  const [asianError, setAsianError] = useState<string>("");
  const [isAsianLoading, setIsAsianLoading] = useState<boolean>(false);
  const [americanForm, setAmericanForm] = useState<AmericanFormState>(initialAmericanForm);
  const [americanResult, setAmericanResult] = useState<AmericanOptionResult | null>(null);
  const [americanError, setAmericanError] = useState<string>("");
  const [isAmericanLoading, setIsAmericanLoading] = useState<boolean>(false);
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
    void runPricing(parsePricingPayload(initialForm));
  }, []);

  function updateField<K extends keyof FormState>(key: K, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function updateIvField<K extends keyof ImpliedVolatilityFormState>(
    key: K,
    value: ImpliedVolatilityFormState[K]
  ) {
    setIvForm((prev) => ({ ...prev, [key]: value }));
  }

  function updateAsianField<K extends keyof AsianFormState>(
    key: K,
    value: AsianFormState[K]
  ) {
    setAsianForm((prev) => ({ ...prev, [key]: value }));
  }

  function updateAmericanField<K extends keyof AmericanFormState>(
    key: K,
    value: AmericanFormState[K]
  ) {
    setAmericanForm((prev) => ({ ...prev, [key]: value }));
  }

  function toNumber(value: string): number {
    return Number(value.trim());
  }

  function parsePricingPayload(data: FormState): PricingPayload {
    return {
      spot: toNumber(data.spot),
      strike: toNumber(data.strike),
      rate: toNumber(data.rate),
      dividendYield: toNumber(data.dividendYield),
      volatility: toNumber(data.volatility),
      maturity: toNumber(data.maturity)
    };
  }

  function parseImpliedVolatilityPayload(data: ImpliedVolatilityFormState): ImpliedVolatilityPayload {
    return {
      spot: toNumber(data.spot),
      strike: toNumber(data.strike),
      rate: toNumber(data.rate),
      dividendYield: toNumber(data.dividendYield),
      maturity: toNumber(data.maturity),
      marketPrice: toNumber(data.marketPrice),
      optionType: data.optionType
    };
  }

  function parseAsianPayload(data: AsianFormState): AsianPricingPayload {
    return {
      spot: toNumber(data.spot),
      strike: toNumber(data.strike),
      rate: toNumber(data.rate),
      volatility: toNumber(data.volatility),
      maturity: toNumber(data.maturity),
      nSteps: Number.parseInt(data.nSteps.trim(), 10),
      nPaths: Number.parseInt(data.nPaths.trim(), 10),
      optionType: data.optionType
    };
  }

  function parseAmericanPayload(data: AmericanFormState): AmericanPricingPayload {
    return {
      spot: toNumber(data.spot),
      strike: toNumber(data.strike),
      rate: toNumber(data.rate),
      volatility: toNumber(data.volatility),
      maturity: toNumber(data.maturity),
      nSteps: Number.parseInt(data.nSteps.trim(), 10),
      optionType: data.optionType
    };
  }

  function validate(data: FormState): string {
    const parsed = parsePricingPayload(data);
    if (!Number.isFinite(parsed.spot) || parsed.spot <= 0) return "Spot price 必须是大于 0 的数字";
    if (!Number.isFinite(parsed.strike) || parsed.strike <= 0) return "Strike price 必须是大于 0 的数字";
    if (!Number.isFinite(parsed.volatility) || parsed.volatility <= 0) return "Volatility 必须是大于 0 的数字";
    if (!Number.isFinite(parsed.maturity) || parsed.maturity <= 0) return "Time to maturity 必须是大于 0 的数字";
    if (!Number.isFinite(parsed.rate)) return "Risk-free Rate 必须是数字";
    if (!Number.isFinite(parsed.dividendYield)) return "Dividend Yield 必须是数字";
    return "";
  }

  function validateImpliedVolatility(data: ImpliedVolatilityFormState): string {
    const parsed = parseImpliedVolatilityPayload(data);
    if (!Number.isFinite(parsed.spot) || parsed.spot <= 0) return "IV: Spot price 必须是大于 0 的数字";
    if (!Number.isFinite(parsed.strike) || parsed.strike <= 0) return "IV: Strike price 必须是大于 0 的数字";
    if (!Number.isFinite(parsed.maturity) || parsed.maturity <= 0) return "IV: Time to maturity 必须是大于 0 的数字";
    if (!Number.isFinite(parsed.marketPrice) || parsed.marketPrice <= 0) return "IV: Market option price 必须是大于 0 的数字";
    if (!Number.isFinite(parsed.rate)) return "IV: Risk-free Rate 必须是数字";
    if (!Number.isFinite(parsed.dividendYield)) return "IV: Dividend Yield 必须是数字";
    return "";
  }

  function validateAsian(data: AsianFormState): string {
    const parsed = parseAsianPayload(data);
    if (!Number.isFinite(parsed.spot) || parsed.spot <= 0) return "Asian: Spot price 必须是大于 0 的数字";
    if (!Number.isFinite(parsed.strike) || parsed.strike <= 0) return "Asian: Strike price 必须是大于 0 的数字";
    if (!Number.isFinite(parsed.volatility) || parsed.volatility <= 0) return "Asian: Volatility 必须是大于 0 的数字";
    if (!Number.isFinite(parsed.maturity) || parsed.maturity <= 0) return "Asian: Time to maturity 必须是大于 0 的数字";
    if (!Number.isFinite(parsed.rate)) return "Asian: Risk-free Rate 必须是数字";
    if (!Number.isInteger(parsed.nSteps) || parsed.nSteps <= 0) return "Asian: Number of steps 必须是正整数";
    if (!Number.isInteger(parsed.nPaths) || parsed.nPaths <= 0) return "Asian: Number of paths 必须是正整数";
    return "";
  }

  function validateAmerican(data: AmericanFormState): string {
    const parsed = parseAmericanPayload(data);
    if (!Number.isFinite(parsed.spot) || parsed.spot <= 0) return "American: Spot price 必须是大于 0 的数字";
    if (!Number.isFinite(parsed.strike) || parsed.strike <= 0) return "American: Strike price 必须是大于 0 的数字";
    if (!Number.isFinite(parsed.volatility) || parsed.volatility <= 0) return "American: Volatility 必须是大于 0 的数字";
    if (!Number.isFinite(parsed.maturity) || parsed.maturity <= 0) return "American: Time to maturity 必须是大于 0 的数字";
    if (!Number.isFinite(parsed.rate)) return "American: Risk-free Rate 必须是数字";
    if (!Number.isInteger(parsed.nSteps) || parsed.nSteps <= 0) return "American: Number of steps 必须是正整数";
    return "";
  }

  async function runPricing(data: PricingPayload) {
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

  async function runImpliedVolatility(data: ImpliedVolatilityPayload) {
    try {
      setIsIvLoading(true);
      const iv = await fetchImpliedVolatility(data);
      setIvResult(iv);
      setIvError("");
    } catch (err) {
      setIvResult(null);
      setIvError(err instanceof Error ? err.message : "IV 计算失败，请检查 Python 服务是否启动");
    } finally {
      setIsIvLoading(false);
    }
  }

  async function runAsianPricing(data: AsianPricingPayload) {
    try {
      setIsAsianLoading(true);
      const priced = await fetchAsianOption(data);
      setAsianResult(priced);
      setAsianError("");
    } catch (err) {
      setAsianResult(null);
      setAsianError(err instanceof Error ? err.message : "Asian Option 计算失败，请检查 Python 服务是否启动");
    } finally {
      setIsAsianLoading(false);
    }
  }

  async function runAmericanPricing(data: AmericanPricingPayload) {
    try {
      setIsAmericanLoading(true);
      const priced = await fetchAmericanOption(data);
      setAmericanResult(priced);
      setAmericanError("");
    } catch (err) {
      setAmericanResult(null);
      setAmericanError(err instanceof Error ? err.message : "American Option 计算失败，请检查 Python 服务是否启动");
    } finally {
      setIsAmericanLoading(false);
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

    await runPricing(parsePricingPayload(form));
  }

  async function handleReset() {
    setForm(initialForm);
    setError("");
    await runPricing(parsePricingPayload(initialForm));
  }

  async function handleIvSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const validationError = validateImpliedVolatility(ivForm);
    setIvError(validationError);

    if (validationError) {
      setIvResult(null);
      return;
    }

    await runImpliedVolatility(parseImpliedVolatilityPayload(ivForm));
  }

  function handleIvReset() {
    setIvForm(initialIvForm);
    setIvResult(null);
    setIvError("");
  }

  async function handleAsianSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const validationError = validateAsian(asianForm);
    setAsianError(validationError);

    if (validationError) {
      setAsianResult(null);
      return;
    }

    await runAsianPricing(parseAsianPayload(asianForm));
  }

  function handleAsianReset() {
    setAsianForm(initialAsianForm);
    setAsianResult(null);
    setAsianError("");
  }

  async function handleAmericanSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const validationError = validateAmerican(americanForm);
    setAmericanError(validationError);

    if (validationError) {
      setAmericanResult(null);
      return;
    }

    await runAmericanPricing(parseAmericanPayload(americanForm));
  }

  function handleAmericanReset() {
    setAmericanForm(initialAmericanForm);
    setAmericanResult(null);
    setAmericanError("");
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
                    type="text"
                    inputMode="decimal"
                  value={form.spot}
                    onChange={(e) => updateField("spot", e.target.value)}
                />
              </label>

              <label>
                Strike Price (K)
                <input
                    type="text"
                    inputMode="decimal"
                  value={form.strike}
                    onChange={(e) => updateField("strike", e.target.value)}
                />
              </label>

              <label>
                Risk-free Rate (r)
                <input
                    type="text"
                    inputMode="decimal"
                  value={form.rate}
                    onChange={(e) => updateField("rate", e.target.value)}
                />
              </label>

              <label>
                Dividend Yield (q)
                <input
                    type="text"
                    inputMode="decimal"
                  value={form.dividendYield}
                    onChange={(e) => updateField("dividendYield", e.target.value)}
                />
              </label>

              <label>
                Volatility (sigma)
                <input
                    type="text"
                    inputMode="decimal"
                  value={form.volatility}
                    onChange={(e) => updateField("volatility", e.target.value)}
                />
              </label>

              <label>
                Time to Maturity (T, years)
                <input
                    type="text"
                    inputMode="decimal"
                  value={form.maturity}
                    onChange={(e) => updateField("maturity", e.target.value)}
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

            <section className="iv-section">
              <h2>Implied Volatility Calculator</h2>

              <form className="pricing-form" onSubmit={handleIvSubmit}>
                <label>
                  Spot Price (S)
                  <input
                      type="text"
                      inputMode="decimal"
                    value={ivForm.spot}
                      onChange={(e) => updateIvField("spot", e.target.value)}
                  />
                </label>

                <label>
                  Strike Price (K)
                  <input
                      type="text"
                      inputMode="decimal"
                    value={ivForm.strike}
                      onChange={(e) => updateIvField("strike", e.target.value)}
                  />
                </label>

                <label>
                  Risk-free Rate (r)
                  <input
                      type="text"
                      inputMode="decimal"
                    value={ivForm.rate}
                      onChange={(e) => updateIvField("rate", e.target.value)}
                  />
                </label>

                <label>
                  Dividend Yield (q)
                  <input
                      type="text"
                      inputMode="decimal"
                    value={ivForm.dividendYield}
                      onChange={(e) => updateIvField("dividendYield", e.target.value)}
                  />
                </label>

                <label>
                  Time to Maturity (T, years)
                  <input
                      type="text"
                      inputMode="decimal"
                    value={ivForm.maturity}
                      onChange={(e) => updateIvField("maturity", e.target.value)}
                  />
                </label>

                <label>
                  Market Option Price (V)
                  <input
                      type="text"
                      inputMode="decimal"
                    value={ivForm.marketPrice}
                      onChange={(e) => updateIvField("marketPrice", e.target.value)}
                  />
                </label>

                <label>
                  Option Type
                  <select
                    value={ivForm.optionType}
                    onChange={(e) => updateIvField("optionType", e.target.value as "call" | "put")}
                  >
                    <option value="call">Call</option>
                    <option value="put">Put</option>
                  </select>
                </label>

                <div className="actions">
                  <button type="submit" disabled={isIvLoading}>
                    {isIvLoading ? "Calculating IV..." : "Calculate IV"}
                  </button>
                  <button type="button" className="secondary" onClick={handleIvReset} disabled={isIvLoading}>
                    Reset
                  </button>
                </div>
              </form>

              {ivError ? <p className="error">{ivError}</p> : null}

              <section className="result-grid iv-result" aria-live="polite">
                <article>
                  <p className="metric">Implied Volatility (sigma)</p>
                  <p className="value">{ivResult ? formatNumber(ivResult.impliedVolatility) : "-"}</p>
                </article>
              </section>
            </section>
          </>
        ) : activeTab === "asian" ? (
          <>
            <form className="pricing-form" onSubmit={handleAsianSubmit}>
              <label>
                Spot Price (S)
                <input
                  type="text"
                  inputMode="decimal"
                  value={asianForm.spot}
                  onChange={(e) => updateAsianField("spot", e.target.value)}
                />
              </label>

              <label>
                Strike Price (K)
                <input
                  type="text"
                  inputMode="decimal"
                  value={asianForm.strike}
                  onChange={(e) => updateAsianField("strike", e.target.value)}
                />
              </label>

              <label>
                Risk-free Rate (r)
                <input
                  type="text"
                  inputMode="decimal"
                  value={asianForm.rate}
                  onChange={(e) => updateAsianField("rate", e.target.value)}
                />
              </label>

              <label>
                Volatility (sigma)
                <input
                  type="text"
                  inputMode="decimal"
                  value={asianForm.volatility}
                  onChange={(e) => updateAsianField("volatility", e.target.value)}
                />
              </label>

              <label>
                Time to Maturity (T, years)
                <input
                  type="text"
                  inputMode="decimal"
                  value={asianForm.maturity}
                  onChange={(e) => updateAsianField("maturity", e.target.value)}
                />
              </label>

              <label>
                Number of Steps (n)
                <input
                  type="text"
                  inputMode="numeric"
                  value={asianForm.nSteps}
                  onChange={(e) => updateAsianField("nSteps", e.target.value)}
                />
              </label>

              <label>
                Number of Paths (M)
                <input
                  type="text"
                  inputMode="numeric"
                  value={asianForm.nPaths}
                  onChange={(e) => updateAsianField("nPaths", e.target.value)}
                />
              </label>

              <label>
                Option Type
                <select
                  value={asianForm.optionType}
                  onChange={(e) => updateAsianField("optionType", e.target.value as "call" | "put")}
                >
                  <option value="call">Call</option>
                  <option value="put">Put</option>
                </select>
              </label>

              <div className="actions">
                <button type="submit" disabled={isAsianLoading}>
                  {isAsianLoading ? "Calculating..." : "Calculate"}
                </button>
                <button type="button" className="secondary" onClick={handleAsianReset} disabled={isAsianLoading}>
                  Reset
                </button>
              </div>
            </form>

            {asianError ? <p className="error">{asianError}</p> : null}

            <section className="result-grid asian-result-grid" aria-live="polite">
              <article>
                <p className="metric">Geometric Option Value (Closed Form)</p>
                <p className="value">{asianResult ? formatNumber(asianResult.geometricValue) : "-"}</p>
              </article>
              <article>
                <p className="metric">Arithmetic Option Value (Standard MC)</p>
                <p className="value">{asianResult ? formatNumber(asianResult.standardMcValue) : "-"}</p>
                <p className="ci-text">
                  95% CI: {asianResult ? `${formatNumber(asianResult.standardMcConfidenceInterval[0])}, ${formatNumber(asianResult.standardMcConfidenceInterval[1])}` : "-"}
                </p>
              </article>
              <article>
                <p className="metric">Arithmetic Option Value (Control Variate MC)</p>
                <p className="value">{asianResult ? formatNumber(asianResult.controlVariateMcValue) : "-"}</p>
                <p className="ci-text">
                  95% CI: {asianResult ? `${formatNumber(asianResult.controlVariateConfidenceInterval[0])}, ${formatNumber(asianResult.controlVariateConfidenceInterval[1])}` : "-"}
                </p>
              </article>
            </section>
          </>
        ) : activeTab === "american" ? (
          <>
            <form className="pricing-form" onSubmit={handleAmericanSubmit}>
              <label>
                Spot Price (S)
                <input
                  type="text"
                  inputMode="decimal"
                  value={americanForm.spot}
                  onChange={(e) => updateAmericanField("spot", e.target.value)}
                />
              </label>

              <label>
                Strike Price (K)
                <input
                  type="text"
                  inputMode="decimal"
                  value={americanForm.strike}
                  onChange={(e) => updateAmericanField("strike", e.target.value)}
                />
              </label>

              <label>
                Risk-free Rate (r)
                <input
                  type="text"
                  inputMode="decimal"
                  value={americanForm.rate}
                  onChange={(e) => updateAmericanField("rate", e.target.value)}
                />
              </label>

              <label>
                Volatility (sigma)
                <input
                  type="text"
                  inputMode="decimal"
                  value={americanForm.volatility}
                  onChange={(e) => updateAmericanField("volatility", e.target.value)}
                />
              </label>

              <label>
                Time to Maturity (T, years)
                <input
                  type="text"
                  inputMode="decimal"
                  value={americanForm.maturity}
                  onChange={(e) => updateAmericanField("maturity", e.target.value)}
                />
              </label>

              <label>
                Number of Steps (n)
                <input
                  type="text"
                  inputMode="numeric"
                  value={americanForm.nSteps}
                  onChange={(e) => updateAmericanField("nSteps", e.target.value)}
                />
              </label>

              <label>
                Option Type
                <select
                  value={americanForm.optionType}
                  onChange={(e) => updateAmericanField("optionType", e.target.value as "call" | "put")}
                >
                  <option value="put">Put</option>
                  <option value="call">Call</option>
                </select>
              </label>

              <div className="actions">
                <button type="submit" disabled={isAmericanLoading}>
                  {isAmericanLoading ? "Calculating..." : "Calculate"}
                </button>
                <button type="button" className="secondary" onClick={handleAmericanReset} disabled={isAmericanLoading}>
                  Reset
                </button>
              </div>
            </form>

            {americanError ? <p className="error">{americanError}</p> : null}

            <section className="result-grid iv-result" aria-live="polite">
              <article>
                <p className="metric">American Option Value</p>
                <p className="value">{americanResult ? formatNumber(americanResult.price) : "-"}</p>
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

import type { ScenarioTipo } from "../api/client";

interface Props {
  scenario: ScenarioTipo;
  onScenarioChange: (s: ScenarioTipo) => void;
  onUndo: () => void;
  undoDisabled: boolean;
  budgetPct: number | null;
  statoBudget: "ok" | "warning" | "critical" | "n/a";
}

const SCENARI: ScenarioTipo[] = ["Conservativo", "Base", "Aggressivo"];

export function Header({ scenario, onScenarioChange, onUndo, undoDisabled, budgetPct, statoBudget }: Props) {
  return (
    <div className="auxiell-header">
      <div className="auxiell-brand">
        {/* Logo X auxiell — path SVG originale, colorato in grigio brand (#97a4ae) */}
        <svg className="auxiell-logo-svg" viewBox="0 0 257.53 242.2" xmlns="http://www.w3.org/2000/svg">
          <path
            fill="#97a4ae"
            d="m196.24,150.26c-7.41-10.88-10.88-20.26-10.88-29.17,0-8.4,2.97-16.79,9.9-27.17L257.53,0h-55.85l-48.95,73.64c-4.94,7.41-8.4,15.82-10.87,24.23h-26.2c-1.97-8.41-5.93-16.82-10.87-24.23L55.36,0H0l62.29,93.92c6.91,10.38,9.88,18.78,9.88,27.17,0,8.91-3.46,18.29-10.88,29.17L0,242.2h55.36l49.43-73.17c5.44-8.4,9.38-17.29,11.85-26.69h24.23c2.47,9.4,6.43,18.29,11.85,26.69l49.43,73.17h55.36l-61.29-91.94Z"
          />
        </svg>
        <div className="auxiell-text">auxiell</div>
      </div>

      <div className="auxiell-topright">
        <div className="scengroup">
          {SCENARI.map((s) => (
            <button
              key={s}
              className={`scenbtn ${scenario === s ? "active" : ""}`}
              onClick={() => onScenarioChange(s)}
            >
              {s}
            </button>
          ))}
        </div>
        <button className="toolbtn" onClick={onUndo} disabled={undoDisabled}>
          ↶ Undo
        </button>
        {budgetPct !== null && (
          <div className={`budgetbadge ${statoBudget}`}>
            <span>{budgetPct}%</span>
          </div>
        )}
      </div>
    </div>
  );
}

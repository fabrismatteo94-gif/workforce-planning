import type { ParametriOrg } from "../api/client";

interface Props {
  parametri: ParametriOrg;
  onChange: (patch: Partial<ParametriOrg>) => void;
}

export function ParametriOrgPanel({ parametri, onChange }: Props) {
  return (
    <div style={{ marginBottom: 24 }}>
      <h2 className="sectionheader">Parametri organizzazione</h2>
      <div className="paramsection">
        <div className="paramitem">
          <label>Turni al giorno</label>
          <select
            value={parametri.turni}
            onChange={(e) => onChange({ turni: Number(e.target.value) })}
          >
            <option value={1}>1 shift</option>
            <option value={2}>2 shift</option>
            <option value={3}>3 shift</option>
          </select>
        </div>
        <div className="paramitem">
          <label>Giorni/anno</label>
          <input
            type="number"
            value={parametri.giorni_lavorativi_anno}
            onChange={(e) => onChange({ giorni_lavorativi_anno: Number(e.target.value) })}
          />
        </div>
        <div className="paramitem">
          <label>Ore/shift</label>
          <input
            type="number"
            value={parametri.ore_per_turno}
            onChange={(e) => onChange({ ore_per_turno: Number(e.target.value) })}
          />
        </div>
        <div className="paramitem">
          <label>Margine capacità %</label>
          <input
            type="number"
            value={Math.round(parametri.margine_capacita_pct * 100)}
            onChange={(e) => onChange({ margine_capacita_pct: Number(e.target.value) / 100 })}
          />
        </div>
        <div className="paramitem">
          <label>Budget annuale (€)</label>
          <input
            type="number"
            value={parametri.budget_annuale ?? ""}
            placeholder="non impostato"
            onChange={(e) =>
              onChange({ budget_annuale: e.target.value === "" ? undefined : Number(e.target.value) })
            }
          />
        </div>
      </div>
    </div>
  );
}

interface RiskGaugeProps {
  compliancePercentage: number;
  riskScore: number;
}

const SIZE = 168;
const STROKE_WIDTH = 14;
const RADIUS = (SIZE - STROKE_WIDTH) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

function toneFor(compliance: number): { ring: string; text: string } {
  if (compliance >= 80) return { ring: "stroke-success", text: "text-success" };
  if (compliance >= 50) return { ring: "stroke-medium", text: "text-medium" };
  return { ring: "stroke-critical", text: "text-critical" };
}

/**
 * The dashboard's one deliberate visual flourish: a radial gauge showing
 * compliance at a glance, colour-coded the same way as everything else
 * (green/amber/red) so it reads consistently with the severity badges
 * elsewhere on the page.
 */
export function RiskGauge({ compliancePercentage, riskScore }: RiskGaugeProps) {
  const clamped = Math.max(0, Math.min(100, compliancePercentage));
  const offset = CIRCUMFERENCE * (1 - clamped / 100);
  const tone = toneFor(clamped);

  return (
    <div className="flex flex-col items-center gap-3">
      <div
        className="relative"
        role="img"
        aria-label={`Compliance score: ${clamped.toFixed(0)} percent. Risk score: ${riskScore.toFixed(0)}.`}
      >
        <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`} className="-rotate-90">
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            fill="none"
            strokeWidth={STROKE_WIDTH}
            className="stroke-border"
          />
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            fill="none"
            strokeWidth={STROKE_WIDTH}
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={offset}
            className={`transition-[stroke-dashoffset] duration-700 ease-out ${tone.ring}`}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-3xl font-semibold tabular-nums ${tone.text}`}>
            {clamped.toFixed(0)}%
          </span>
          <span className="text-xs text-text-secondary">Compliance</span>
        </div>
      </div>
      <p className="text-sm text-text-secondary">
        Risk score <span className="font-medium text-text-primary">{riskScore.toFixed(0)}</span>{" "}
        / 100
      </p>
    </div>
  );
}

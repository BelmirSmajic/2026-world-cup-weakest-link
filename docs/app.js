const data = window.WEAK_LINK_DATA;

const money = value => `$${(value / 1000000).toFixed(2)}M`;
const points = value => `${value} ${value === 1 ? "point" : "points"}`;
const pct = value => `${Math.round(value * 100)}%`;

const correlations = [
  { label: "Bottom-three average", value: 0.770768, note: "Lineup floor" },
  { label: "Total Core XI value", value: 0.718641, note: "Whole lineup" },
  { label: "Top-three average", value: 0.699404, note: "Biggest stars" },
];

function advancementCount(row) {
  return Math.round(row.advanced_rate * row.teams);
}

function quartileChart() {
  const el = document.getElementById("quartile-chart");
  if (!el) return;
  const rows = data.quartiles;
  const max = Math.max(...rows.map(row => row.advanced_rate));
  el.innerHTML = rows.map(row => {
    const advanced = advancementCount(row);
    const width = Math.max(4, (row.advanced_rate / max) * 100);
    return `<div class="quartile-row">
      <div>
        <strong>${row.bottom_three_quartile}</strong>
        <span>${advanced} of ${row.teams} advanced</span>
      </div>
      <div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div>
      <b>${pct(row.advanced_rate)}</b>
    </div>`;
  }).join("");
}

function correlationChart() {
  const el = document.getElementById("correlation-chart");
  if (!el) return;
  const max = Math.max(...correlations.map(row => row.value));
  el.innerHTML = correlations.map(row => {
    const width = (row.value / max) * 100;
    return `<div class="correlation-row">
      <div>
        <strong>${row.label}</strong>
        <span>${row.note}</span>
      </div>
      <div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div>
      <b>${row.value.toFixed(2)}</b>
    </div>`;
  }).join("");
}

function rankedTable(id, rows) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = `<table>
    <thead>
      <tr>
        <th>Rank</th>
        <th>Team</th>
        <th>Floor</th>
        <th>Points</th>
        <th>Outcome</th>
      </tr>
    </thead>
    <tbody>
      ${rows.slice(0, 5).map(row => `<tr>
        <td>${row.rank}</td>
        <td>${row.team}</td>
        <td>${money(row.value)}</td>
        <td>${row.points}</td>
        <td>${row.advanced_flag ? "Advanced" : "Eliminated"}</td>
      </tr>`).join("")}
    </tbody>
  </table>`;
}

function scatterChart() {
  const el = document.getElementById("scatter-chart");
  if (!el) return;

  const rows = data.scatter;
  const w = 900;
  const h = 470;
  const pad = { top: 28, right: 36, bottom: 82, left: 74 };
  const xs = rows.map(d => d.bottom_3_average_value_usd);
  const ys = rows.map(d => d.points);
  const minLog = Math.log10(Math.min(...xs));
  const maxLog = Math.log10(Math.max(...xs));
  const minY = 0;
  const maxY = Math.max(...ys);

  const innerW = w - pad.left - pad.right;
  const innerH = h - pad.top - pad.bottom;
  const scaleX = value => pad.left + ((Math.log10(value) - minLog) / (maxLog - minLog || 1)) * innerW;
  const scaleY = value => pad.top + (1 - ((value - minY) / (maxY - minY || 1))) * innerH;

  const logs = rows.map(d => Math.log10(d.bottom_3_average_value_usd));
  const meanX = logs.reduce((sum, value) => sum + value, 0) / logs.length;
  const meanY = ys.reduce((sum, value) => sum + value, 0) / ys.length;
  const slope = logs.reduce((sum, value, index) => sum + (value - meanX) * (ys[index] - meanY), 0) /
    logs.reduce((sum, value) => sum + (value - meanX) ** 2, 0);
  const intercept = meanY - slope * meanX;
  const trendY1 = Math.max(minY, Math.min(maxY, intercept + slope * minLog));
  const trendY2 = Math.max(minY, Math.min(maxY, intercept + slope * maxLog));

  const xTicks = [100000, 1000000, 10000000, 45000000];
  const yTicks = [0, 3, 6, 9];
  const labelTeams = new Set(["England", "France", "IR Iran", "Curaçao", "Cabo Verde", "Mexico"]);
  const labelOffsets = {
    England: [-54, -12],
    France: [-36, -16],
    "IR Iran": [8, -8],
    "Curaçao": [8, 16],
    "Cabo Verde": [8, -18],
    Mexico: [8, -16],
  };

  const grid = [
    ...xTicks.map(tick => `<line class="grid" x1="${scaleX(tick)}" y1="${pad.top}" x2="${scaleX(tick)}" y2="${h - pad.bottom}"></line>
      <text class="label axis-label" x="${scaleX(tick)}" y="${h - 48}" text-anchor="middle">${money(tick)}</text>`),
    ...yTicks.map(tick => `<line class="grid" x1="${pad.left}" y1="${scaleY(tick)}" x2="${w - pad.right}" y2="${scaleY(tick)}"></line>
      <text class="label axis-label" x="${pad.left - 14}" y="${scaleY(tick) + 4}" text-anchor="end">${tick}</text>`),
  ].join("");

  const dots = rows.map(d => {
    const cls = d.advanced_flag ? "dot advanced" : "dot";
    return `<circle class="${cls}" cx="${scaleX(d.bottom_3_average_value_usd)}" cy="${scaleY(d.points)}" r="5.5">
      <title>${d.team}: ${money(d.bottom_3_average_value_usd)} floor, ${points(d.points)}, ${d.advanced_flag ? "advanced" : "eliminated"}</title>
    </circle>`;
  }).join("");

  const labels = rows.filter(d => labelTeams.has(d.team)).map(d => {
    const [dx, dy] = labelOffsets[d.team] || [8, -8];
    return `<text class="team-label" x="${scaleX(d.bottom_3_average_value_usd) + dx}" y="${scaleY(d.points) + dy}">${d.team}</text>`;
  }).join("");

  el.innerHTML = `<svg class="chart-svg scatter-svg" viewBox="0 0 ${w} ${h}" role="img" aria-label="Bottom-three lineup-floor value versus group-stage points">
    ${grid}
    <line class="axis" x1="${pad.left}" y1="${h - pad.bottom}" x2="${w - pad.right}" y2="${h - pad.bottom}"></line>
    <line class="axis" x1="${pad.left}" y1="${pad.top}" x2="${pad.left}" y2="${h - pad.bottom}"></line>
    <line class="trend-line" x1="${scaleX(Math.min(...xs))}" y1="${scaleY(trendY1)}" x2="${scaleX(Math.max(...xs))}" y2="${scaleY(trendY2)}"></line>
    ${dots}
    ${labels}
    <g class="legend">
      <circle class="dot advanced" cx="${w - 238}" cy="28" r="5.5"></circle>
      <text class="label" x="${w - 224}" y="33">Advanced</text>
      <circle class="dot" cx="${w - 138}" cy="28" r="5.5"></circle>
      <text class="label" x="${w - 124}" y="33">Eliminated</text>
      <line class="trend-line" x1="${w - 238}" y1="52" x2="${w - 202}" y2="52"></line>
      <text class="label" x="${w - 194}" y="56">Trend line</text>
    </g>
    <text class="axis-title" x="${pad.left + innerW / 2}" y="${h - 14}" text-anchor="middle">Bottom-three average value, USD (log scale)</text>
    <text class="axis-title" transform="translate(20 ${pad.top + innerH / 2}) rotate(-90)" text-anchor="middle">Group-stage points</text>
  </svg>`;
}

quartileChart();
correlationChart();
scatterChart();
rankedTable("strongest-table", data.strongestFloors);
rankedTable("weakest-table", data.weakestFloors);

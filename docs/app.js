const data = window.WEAK_LINK_DATA;
const money = value => `$${(value / 1000000).toFixed(2)}M`;
const points = value => `${value} ${value === 1 ? "point" : "points"}`;

function barChart(id, rows, options = {}) {
  const el = document.getElementById(id);
  if (!el) return;
  const max = Math.max(...rows.map(row => row.value));
  el.innerHTML = rows.map(row => {
    const width = Math.max(2, (row.value / max) * 100);
    return `<div class="bar-row">
      <strong>${row.rank}. ${row.team}</strong>
      <div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div>
      <span>${money(row.value)}</span>
    </div>`;
  }).join("");
}

function scatterChart(id, rows, xKey, yKey, labelKey, xFormatter = v => v, yFormatter = v => v) {
  const el = document.getElementById(id);
  if (!el) return;
  const w = 760, h = 340, pad = 48;
  const xs = rows.map(d => d[xKey]);
  const ys = rows.map(d => d[yKey]);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const scaleX = x => pad + ((x - minX) / (maxX - minX || 1)) * (w - pad * 1.5);
  const scaleY = y => h - pad - ((y - minY) / (maxY - minY || 1)) * (h - pad * 1.5);
  const dots = rows.map(d => {
    const cls = d.advanced_flag ? "dot advanced" : "dot";
    return `<circle class="${cls}" cx="${scaleX(d[xKey])}" cy="${scaleY(d[yKey])}" r="5">
      <title>${d[labelKey]}: ${xFormatter(d[xKey])}, ${yFormatter(d[yKey])}</title>
    </circle>`;
  }).join("");
  el.innerHTML = `<svg class="chart-svg" viewBox="0 0 ${w} ${h}" role="img" aria-label="Scatter plot">
    <line class="axis" x1="${pad}" y1="${h - pad}" x2="${w - pad / 2}" y2="${h - pad}"></line>
    <line class="axis" x1="${pad}" y1="${pad / 2}" x2="${pad}" y2="${h - pad}"></line>
    ${dots}
    <text class="label" x="${pad}" y="${h - 10}">${xFormatter(minX)}</text>
    <text class="label" x="${w - 110}" y="${h - 10}">${xFormatter(maxX)}</text>
    <text class="label" x="8" y="${scaleY(minY)}">${yFormatter(minY)}</text>
    <text class="label" x="8" y="${scaleY(maxY)}">${yFormatter(maxY)}</text>
  </svg>`;
}

function quartileChart() {
  const el = document.getElementById("quartile-chart");
  if (!el) return;
  const rows = data.quartiles;
  el.innerHTML = rows.map(row => {
    const width = Math.max(3, row.advanced_rate * 100);
    return `<div class="bar-row">
      <strong>${row.bottom_three_quartile}</strong>
      <div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div>
      <span>${(row.advanced_rate * 100).toFixed(1)}%</span>
    </div>`;
  }).join("");
}

barChart("weakest-chart", data.weakestFloors);
barChart("strongest-chart", data.strongestFloors);
scatterChart("scatter-chart", data.scatter, "bottom_3_average_value_usd", "points", "team", money, points);
scatterChart("total-vs-floor-chart", data.scatter, "core_xi_total_value_usd", "bottom_3_average_value_usd", "team", money, money);
quartileChart();

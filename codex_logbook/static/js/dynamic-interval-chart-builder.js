/***********************************************************************
 * Shared palette & grid-line color
 *********************************************************************/
const COLOR = {
  red:    { stroke: '#9E3B16', fill: 'rgba(158,59,22,0.12)' },
  blue:   { stroke: '#EB6A1C', fill: 'rgba(235,106,28,0.12)' },
  orange: { stroke: '#B0997A', fill: 'rgba(176,153,122,0.14)' },
  amber:  { stroke: '#ECDFC8', fill: 'rgba(236,223,200,0.20)' }
};
const GRID_COLOR = "rgba(176,153,122,0.25)";

const withColor = (name, extra = {}) => ({
  borderColor:    COLOR[name].stroke,
  backgroundColor: COLOR[name].fill,
  ...extra
});

/***********************************************************************
 * Generic dynamic-interval chart builder
 *********************************************************************/
function makeDynamicIntervalChart({
  canvasId,
  labels,
  datasets,
  yScales,
  legendPos = 'top',
  tooltipExtra = {},
  optionOverrides = {},
  limitedBucketData,
  useHourlyInterval
}) {
  /* format bucket timestamp for hourly *or* daily data */
  const fmt = idx => {
    const b = limitedBucketData[idx];
    if (!b) {return '';}
    const p = b.timestamp.split('-').map(Number);
    const d = useHourlyInterval
      ? new Date(p[0], p[1] - 1, p[2], p[3])
      : new Date(p[0], p[1] - 1, p[2]);
    return d.toLocaleDateString('en-US', {
      weekday: 'short',
      year:    'numeric',
      month:   'short',
      day:     'numeric',
      hour:    useHourlyInterval ? 'numeric' : undefined,
      hour12:  true
    });
  };

  /* supply default grid colors if missing */
  Object.values(yScales).forEach(s => {
    s.grid ??= {};
    if (!s.grid.color) {s.grid.color = GRID_COLOR;}
  });

  const opts = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend:  { display: true, position: legendPos },
      tooltip: { callbacks: { title: ctx => fmt(ctx[0].dataIndex), ...tooltipExtra } }
    },
    scales: {
      x: {
        title: { display: true, text: 'Time' },
        grid:  { color: GRID_COLOR },
        ticks: {
          maxRotation: 45,
          minRotation: 0,
          autoSkip: false,
          callback(v) { return this.getLabelForValue(v) || ''; }
        }
      },
      ...yScales
    },
    ...optionOverrides
  };

  return new Chart(document.getElementById(canvasId), {
    type: 'line',
    data: { labels, datasets },
    options: opts
  });
}

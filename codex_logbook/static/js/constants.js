// Constants for Codex Logbook

// User interruption patterns
const USER_INTERRUPTION_PREFIX = '[Request interrupted by user for tool use]';
const USER_INTERRUPTION_API_ERROR = 'API Error: Request was aborted.';
const USER_INTERRUPTION_PATTERNS = [
  USER_INTERRUPTION_PREFIX,
  USER_INTERRUPTION_API_ERROR
];

// Pagination defaults
const DEFAULT_MESSAGES_PER_PAGE = 20;
const DEFAULT_COMMANDS_PER_PAGE = 20;

// Chart colors
const CHART_COLORS = {
  primary: '#EB6A1C',
  secondary: '#B0997A',
  success: '#7A6549',
  warning: '#ECDFC8',
  danger: '#9E3B16',
  info: '#3A2A18'
};

// Codex logs location info
const CODEX_LOGS_TOOLTIP = `<div class="example">
    <strong>Example:</strong><br>
    Project: /Users/developer/dev/demoapp<br>
    Logs at: ~/.codex-logbook/codex/projects/-Users-developer-dev-demoapp/
</div>`;

function applyCodexLogbookChartTheme() {
  if (typeof Chart === 'undefined') {
    return;
  }

  Chart.defaults.color = '#7A6549';
  Chart.defaults.borderColor = '#ECDFC8';
  Chart.defaults.font.family = 'Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
  Chart.defaults.plugins.legend.labels.color = '#3A2A18';
  Chart.defaults.plugins.tooltip.backgroundColor = '#FFFFFF';
  Chart.defaults.plugins.tooltip.titleColor = '#3A2A18';
  Chart.defaults.plugins.tooltip.bodyColor = '#3A2A18';
  Chart.defaults.plugins.tooltip.borderColor = '#EB6A1C';
  Chart.defaults.plugins.tooltip.borderWidth = 1;
}

document.addEventListener('DOMContentLoaded', applyCodexLogbookChartTheme);

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    USER_INTERRUPTION_PREFIX,
    USER_INTERRUPTION_API_ERROR,
    USER_INTERRUPTION_PATTERNS,
    DEFAULT_MESSAGES_PER_PAGE,
    DEFAULT_COMMANDS_PER_PAGE,
    CHART_COLORS,
    CODEX_LOGS_TOOLTIP,
    applyCodexLogbookChartTheme
  };
}

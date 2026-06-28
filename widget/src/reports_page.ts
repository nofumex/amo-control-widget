export function reportsPage(report?: Record<string, unknown>): string {
  const today = new Date().toISOString().slice(0, 10);
  const rendered = String(report?.rendered_text || "");
  const raw = report?.raw_json ? JSON.stringify(report.raw_json, null, 2) : "";
  return `
    <div class="acw-report-tools">
      <input id="report_date" type="date" value="${today}">
      <button data-action="build-report">Построить</button>
      <button data-action="load-report">Открыть</button>
      <button data-action="send-telegram">Отправить в Telegram</button>
      <button data-action="copy-report">Скопировать</button>
    </div>
    <textarea id="rendered_report" readonly>${rendered}</textarea>
    <details><summary>Raw JSON</summary><pre>${raw}</pre></details>
  `;
}

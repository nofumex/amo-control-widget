export type ApiConfig = {
  backendUrl: string;
  widgetToken?: string;
  tenantId?: string;
};

export class WidgetApi {
  constructor(private readonly config: ApiConfig) {}

  async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers = new Headers(options.headers);
    headers.set("Content-Type", "application/json");
    if (this.config.widgetToken) headers.set("X-Widget-Token", this.config.widgetToken);
    if (this.config.tenantId) headers.set("X-Tenant-Id", this.config.tenantId);
    const response = await fetch(`${this.config.backendUrl.replace(/\/$/, "")}${path}`, { ...options, headers });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `HTTP ${response.status}`);
    }
    return response.json() as Promise<T>;
  }

  getStatus() { return this.request<Record<string, unknown>>("/api/widget/status"); }
  getSettings() { return this.request<Record<string, unknown>>("/api/widget/settings"); }
  saveSettings(payload: unknown) { return this.request("/api/widget/settings", { method: "PUT", body: JSON.stringify(payload) }); }
  getEventCatalog() { return this.request<Array<Record<string, unknown>>>("/api/widget/event-catalog"); }
  getUsers() { return this.request<Array<Record<string, unknown>>>("/api/widget/users"); }
  listReports() { return this.request<Array<Record<string, unknown>>>("/api/widget/reports"); }
  buildReport(date: string) { return this.request<Record<string, unknown>>(`/api/widget/reports/${date}/build`, { method: "POST" }); }
  getReport(date: string) { return this.request<Record<string, unknown>>(`/api/widget/reports/${date}`); }
  sendTelegram(date: string) {
    return this.request<Record<string, unknown>>(`/api/widget/reports/${date}/send-telegram`, { method: "POST" });
  }
  getTelegram() { return this.request<Record<string, unknown>>("/api/widget/telegram"); }
  saveTelegram(payload: unknown) { return this.request("/api/widget/telegram", { method: "PUT", body: JSON.stringify(payload) }); }
  testTelegram() { return this.request<Record<string, unknown>>("/api/widget/telegram/test", { method: "POST" }); }
  syncNow() { return this.request<Record<string, unknown>>("/api/widget/sync", { method: "POST" }); }
}

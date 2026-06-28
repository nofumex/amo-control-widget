export type ApiConfig = {
  backendUrl: string;
  devTenantId?: string;
  kommoAccountId?: string;
  kommoSubdomain?: string;
  kommoTimestamp?: string;
  kommoSignature?: string;
};

export class WidgetApi {
  constructor(private readonly config: ApiConfig) {}

  async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    if (!this.config.backendUrl) {
      throw new Error("Backend URL не настроен. Откройте настройки виджета и укажите HTTPS URL backend.");
    }
    const headers = new Headers(options.headers);
    headers.set("Content-Type", "application/json");
    if (this.config.devTenantId) headers.set("X-Dev-Tenant-Id", this.config.devTenantId);
    if (this.config.kommoAccountId) headers.set("X-KOMMO-Account-Id", this.config.kommoAccountId);
    if (this.config.kommoSubdomain) headers.set("X-KOMMO-Subdomain", this.config.kommoSubdomain);
    if (this.config.kommoTimestamp) headers.set("X-KOMMO-Timestamp", this.config.kommoTimestamp);
    if (this.config.kommoSignature) headers.set("X-KOMMO-Signature", this.config.kommoSignature);
    const response = await fetch(`${this.config.backendUrl.replace(/\/$/, "")}${path}`, { ...options, headers });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(humanApiError(response.status, text));
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

function humanApiError(status: number, body: string): string {
  if (status === 401) return "Нет доступа: виджет не прошел проверку подлинности.";
  if (status === 409) return "Интеграция требует подключения или переподключения amoCRM OAuth.";
  try {
    const parsed = JSON.parse(body) as { detail?: string; error?: { message?: string } };
    return parsed.detail || parsed.error?.message || `Ошибка API ${status}`;
  } catch {
    return body || `Ошибка API ${status}`;
  }
}

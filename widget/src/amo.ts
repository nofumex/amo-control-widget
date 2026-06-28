declare global {
  interface Window {
    AMOCRM?: {
      widgets?: {
        system?: {
          domain?: string;
          amouser_id?: number;
          account?: { id?: number; subdomain?: string };
        };
      };
    };
  }
}

export function readWidgetSettings(): { backendUrl: string; widgetToken?: string; tenantId?: string } {
  const search = new URLSearchParams(window.location.search);
  const backendUrl = search.get("backend_url") || localStorage.getItem("amoControlBackendUrl") || "http://localhost:8000";
  const widgetToken = search.get("widget_token") || localStorage.getItem("amoControlWidgetToken") || undefined;
  const tenantId = search.get("tenant_id") || localStorage.getItem("amoControlTenantId") || "1";
  return { backendUrl, widgetToken, tenantId };
}

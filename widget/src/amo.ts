declare global {
  interface Window {
    AMOCRM?: {
      widgets?: {
        system?: {
          domain?: string;
          amouser_id?: number;
          account?: { id?: number; subdomain?: string };
          secure?: { timestamp?: number; signature?: string };
        };
      };
    };
  }
}

export function readWidgetSettings(): {
  backendUrl: string;
  devTenantId?: string;
  kommoAccountId?: string;
  kommoSubdomain?: string;
  kommoTimestamp?: string;
  kommoSignature?: string;
} {
  const search = new URLSearchParams(window.location.search);
  const system = window.AMOCRM?.widgets?.system;
  const backendUrl = search.get("backend_url") || "";
  return {
    backendUrl,
    devTenantId: search.get("dev_tenant_id") || undefined,
    kommoAccountId: search.get("account_id") || String(system?.account?.id || "") || undefined,
    kommoSubdomain: search.get("subdomain") || system?.account?.subdomain || system?.domain || undefined,
    kommoTimestamp: search.get("kommo_timestamp") || String(system?.secure?.timestamp || "") || undefined,
    kommoSignature: search.get("kommo_signature") || system?.secure?.signature || undefined
  };
}

import { api } from "../lib/api";

export async function createReportExport(period_start: string, period_end: string) {
  const { data } = await api.post("/exports/report", { period_start, period_end });
  return data as { report_id: string; status: string };
}

export async function getReportStatus(reportId: string) {
  const { data } = await api.get(`/exports/report/${reportId}`);
  return data as { report_id: string; status: string; download_url?: string };
}

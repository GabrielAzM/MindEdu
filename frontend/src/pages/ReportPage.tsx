import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { Panel } from "../components/common/Panel";
import { createReportExport, getReportStatus } from "../services/exportsService";

export function ReportPage() {
  const [reportId, setReportId] = useState<string | null>(null);
  const createMutation = useMutation({
    mutationFn: () => createReportExport("2026-02-01", "2026-02-15"),
    onSuccess: (data) => setReportId(data.report_id),
  });

  const statusMutation = useMutation({
    mutationFn: () => (reportId ? getReportStatus(reportId) : Promise.reject(new Error("missing reportId"))),
  });

  return (
    <div className="space-y-4">
      <h1 className="font-heading text-2xl font-bold">Relatorio educativo</h1>
      <Panel>
        <button className="rounded bg-ink px-4 py-2 text-white" onClick={() => createMutation.mutate()} type="button">
          Gerar relatorio
        </button>
        {reportId ? <p className="mt-2 text-sm">report_id: {reportId}</p> : null}
      </Panel>
      {reportId ? (
        <Panel>
          <button className="rounded border px-4 py-2" onClick={() => statusMutation.mutate()} type="button">
            Atualizar status
          </button>
          {statusMutation.data ? (
            <div className="mt-2 text-sm">
              <p>Status: {statusMutation.data.status}</p>
              {statusMutation.data.download_url ? (
                <a className="text-blue-700" href={`${import.meta.env.VITE_API_URL ?? "http://localhost:8000"}${statusMutation.data.download_url}`}>
                  Baixar PDF
                </a>
              ) : null}
            </div>
          ) : null}
        </Panel>
      ) : null}
    </div>
  );
}

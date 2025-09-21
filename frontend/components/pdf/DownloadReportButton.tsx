"use client";
import { PDFDownloadLink } from "@react-pdf/renderer";
import type { SummarizeResponse } from "@/types/insightreel";
import { TranscriptReport } from "./TranscriptReport";

export function DownloadReportButton({ data }: { data: SummarizeResponse }) {
  const filename = `InsightReel_${data.user_profile.type}_${data.video_title.replace(/\W+/g, "_").slice(0, 40)}.pdf`;
  return (
    <PDFDownloadLink document={<TranscriptReport data={data} />} fileName={filename} className="btn">
      {({ loading }) => (loading ? "Preparing PDF..." : "Download PDF Report")}
    </PDFDownloadLink>
  );
}

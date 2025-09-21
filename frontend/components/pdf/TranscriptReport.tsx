import { Document, Page, Text, View, StyleSheet } from "@react-pdf/renderer";
import type { SummarizeResponse } from "@/types/insightreel";

const styles = StyleSheet.create({
  page: { padding: 32, fontSize: 11, fontFamily: "Helvetica" },
  h1: { fontSize: 20, marginBottom: 8, fontWeight: 700 },
  h2: { fontSize: 14, marginTop: 16, marginBottom: 6, fontWeight: 700 },
  meta: { color: "#555", marginBottom: 16 },
  section: { marginBottom: 12 },
  row: { flexDirection: "row", gap: 8, marginBottom: 6 },
  badge: { backgroundColor: "#E9D5FF", color: "#6B21A8", padding: 4, borderRadius: 4 },
});

export function TranscriptReport({ data }: { data: SummarizeResponse }) {
  const { video_title, channel, duration, ai_enhanced, key_concepts, summary } = data;
  return (
    <Document>
      <Page size="A4" style={styles.page}>
        <Text style={styles.h1}>InsightReel — {video_title}</Text>
        <Text style={styles.meta}>
          Channel: {channel} • Duration: {duration} • {ai_enhanced ? "AI-Enhanced" : "Basic Analysis"}
        </Text>

        <View style={styles.section}>
          <Text style={styles.h2}>Summary</Text>
          <Text>{summary.replace(/[#!>*_`]/g, "").slice(0, 4000)}</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.h2}>Key Concepts</Text>
          <View style={styles.row}>
            <Text style={styles.badge}>Keywords: {key_concepts.keywords.map(([k]) => k).slice(0, 6).join(", ")}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.badge}>Technical: {key_concepts.technical_terms.slice(0, 6).join(", ")}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.badge}>Actions: {key_concepts.action_words.slice(0, 6).join(", ")}</Text>
          </View>
        </View>
      </Page>
    </Document>
  );
}

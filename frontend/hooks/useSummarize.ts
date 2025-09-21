"use client";
import { useMutation } from "@tanstack/react-query";
import { summarize } from "@/lib/api";
import type { SummarizeRequest, SummarizeResponse } from "@/types/insightreel";

export function useSummarize() {
  return useMutation<SummarizeResponse, Error, SummarizeRequest>({
    mutationFn: summarize,
  });
}

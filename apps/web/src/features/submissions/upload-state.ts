import { ApiError } from "@/lib/api/client";

export function uploadError(error: unknown): {
  uncertain: boolean;
  message: string;
} {
  if (
    !(error instanceof ApiError) ||
    error.code === "INVALID_RESPONSE" ||
    ![400, 401, 403, 404, 413, 422].includes(error.status)
  ) {
    return {
      uncertain: true,
      message:
        "We could not confirm the upload outcome. It may have been stored. Check submission history before deciding whether to upload again. A missing history entry does not prove an in-flight upload failed.",
    };
  }
  const messages: Record<string, string> = {
    INVALID_CSV:
      "The API rejected this file. Use UTF-8 CSV with the required columns, standard quoting, no blank records and at least one student record.",
    SCHEMA_MISMATCH:
      "The API rejected the headers. Use the strict-v1 template with all eight headers in the exact order shown.",
    FILE_TOO_LARGE:
      "The file or multipart request exceeds the configured size limit. Select a smaller complete snapshot within the limit.",
    ROW_LIMIT_EXCEEDED:
      "The CSV exceeds the configured data-record limit. It was not stored. Do not split one complete snapshot into separate candidates; this prototype needs a separately approved limit change for larger datasets.",
    INVALID_REQUEST:
      "The API rejected the upload context or file metadata. Check the programme, academic year and file selection.",
  };
  return {
    uncertain: false,
    message:
      messages[error.code] ??
      "The API did not accept this upload. Check your session, institution permissions and selected programme before trying again.",
  };
}

export function templateCSV(headers: readonly string[]): string {
  return headers.join(",") + "\r\n";
}

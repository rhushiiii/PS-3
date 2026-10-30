import { ApiError } from "@/lib/api/client";

export function uploadError(error: unknown): {
  uncertain: boolean;
  message: string;
} {
  if (
    !(error instanceof ApiError) ||
    error.code === "INVALID_RESPONSE" ||
    ![400, 401, 403, 404, 409, 413, 422].includes(error.status)
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
      "The CSV exceeds the configured data-record limit. It was not stored. Do not split one complete snapshot into separate candidates; this platform needs a separately approved limit change for larger datasets.",
    UNSUPPORTED_FILE_TYPE:
      "This file type is not accepted. Choose a file in one of the formats listed in the upload policy.",
    INVALID_XLSX:
      "The API could not read this Excel file. Use a plain .xlsx workbook with the data on the first worksheet, the exact template headers and values only (no macros).",
    IDEMPOTENCY_KEY_REUSED:
      "This upload attempt was already used for different content. Nothing new was stored. Prepare a new upload and try again.",
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

/** Fresh key per submission attempt; matches ^[A-Za-z0-9._:-]{8,128}$. */
export function newIdempotencyKey(): string {
  return `upl-${crypto.randomUUID()}`;
}

export function acceptAttribute(formats: readonly string[]): string {
  return formats.map((format) => `.${format}`).join(",");
}

export function formatList(formats: readonly string[]): string {
  return formats.map((format) => format.toUpperCase()).join(" or ");
}

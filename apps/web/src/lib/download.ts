/** The shared "make a browser download out of a Blob" dance. */
export function saveBlob({
  blob,
  filename,
}: {
  blob: Blob;
  filename: string;
}): void {
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 0);
}

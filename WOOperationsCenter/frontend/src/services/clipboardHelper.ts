/**
 * Enterprise Clipboard Helper for WO Operations Center & TAMMI.
 * Supports:
 * 1. Formatted HTML Table with Windows CF_HTML + TSV fallback.
 * 2. Pixel-perfect PNG Image copy directly onto Windows Clipboard.
 * 3. Clean Plain Text formatted table.
 * 4. TSV format for direct Excel paste.
 */

import { bridge } from "./bridge";

export type ClipboardCopyMode = "html" | "image" | "text" | "tsv";

/**
 * Converts a DOM element into a PNG image data URI via Canvas and foreignObject.
 */
export async function captureElementToPngBase64(element: HTMLElement): Promise<string> {
  const clone = element.cloneNode(true) as HTMLElement;
  const rect = element.getBoundingClientRect();
  const width = Math.max(Math.ceil(rect.width), element.scrollWidth, 600);
  const height = Math.max(Math.ceil(rect.height), element.scrollHeight, 100);

  // Inline computed styles for fonts and backgrounds
  clone.style.width = `${width}px`;
  clone.style.height = `${height}px`;
  clone.style.backgroundColor = window.getComputedStyle(element).backgroundColor || "#ffffff";
  clone.style.color = window.getComputedStyle(element).color || "#000000";
  clone.style.fontFamily = "Arial, sans-serif";

  const wrapper = document.createElement("div");
  wrapper.appendChild(clone);

  const serializedHtml = new XMLSerializer().serializeToString(wrapper);
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">
      <foreignObject width="100%" height="100%">
        <div xmlns="http://www.w3.org/1999/xhtml" style="font-family: Arial, sans-serif; background: #ffffff;">
          ${serializedHtml}
        </div>
      </foreignObject>
    </svg>
  `;

  return new Promise((resolve, reject) => {
    const img = new Image();
    const svgBlob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(svgBlob);

    img.onload = () => {
      try {
        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext("2d");
        if (!ctx) {
          URL.revokeObjectURL(url);
          reject(new Error("Không thể khởi tạo 2D canvas"));
          return;
        }

        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, width, height);
        ctx.drawImage(img, 0, 0);
        URL.revokeObjectURL(url);
        const dataUrl = canvas.toDataURL("image/png");
        resolve(dataUrl);
      } catch (e) {
        URL.revokeObjectURL(url);
        reject(e);
      }
    };

    img.onerror = (e) => {
      URL.revokeObjectURL(url);
      reject(new Error("Lỗi chuyển đổi bảng thành hình ảnh"));
    };

    img.src = url;
  });
}

/**
 * Copies a table or element according to requested copy mode.
 */
export async function copyFormattedTable(params: {
  element?: HTMLElement | null;
  htmlContent: string;
  textContent: string;
  tsvContent?: string;
  mode: ClipboardCopyMode;
}): Promise<boolean> {
  const { element, htmlContent, textContent, tsvContent, mode } = params;

  if (mode === "image" && element) {
    try {
      const base64 = await captureElementToPngBase64(element);
      return await bridge.copyImageFromBase64(base64);
    } catch (e) {
      console.warn("captureElementToPngBase64 failed, falling back to HTML:", e);
      return await bridge.copyCustomHtmlAndText(tsvContent || textContent, htmlContent);
    }
  }

  if (mode === "tsv") {
    return await bridge.copyToClipboard("text", { text: tsvContent || textContent });
  }

  if (mode === "text") {
    return await bridge.copyToClipboard("text", { text: textContent });
  }

  // Default: HTML mode with TSV / Plain text fallback
  return await bridge.copyCustomHtmlAndText(tsvContent || textContent, htmlContent);
}

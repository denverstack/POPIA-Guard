import { useState, useRef, type DragEvent, type ChangeEvent } from "react";
import { UploadCloud } from "lucide-react";

interface UploadDropzoneProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

export function UploadDropzone({ onFileSelected, disabled }: UploadDropzoneProps) {
  const [isDragActive, setIsDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    setIsDragActive(false);
    if (disabled) return;
    const file = event.dataTransfer.files?.[0];
    if (file) onFileSelected(file);
  }

  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) onFileSelected(file);
    // Reset so selecting the same file twice in a row still fires onChange.
    event.target.value = "";
  }

  return (
    <label
      htmlFor="scan-upload-input"
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setIsDragActive(true);
      }}
      onDragLeave={() => setIsDragActive(false)}
      onDrop={handleDrop}
      className={`flex cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors ${
        disabled
          ? "cursor-not-allowed border-border bg-surface text-text-tertiary"
          : isDragActive
            ? "border-accent bg-accent-subtle"
            : "border-border-strong bg-card hover:border-accent hover:bg-accent-subtle"
      }`}
    >
      <UploadCloud className="h-8 w-8 text-text-secondary" aria-hidden="true" />
      <div>
        <p className="text-sm font-medium text-text-primary">
          {disabled ? "Scanning…" : "Drop a .zip file here, or click to browse"}
        </p>
        <p className="mt-1 text-xs text-text-secondary">Up to 20MB. Only .zip archives.</p>
      </div>
      <input
        id="scan-upload-input"
        ref={inputRef}
        type="file"
        accept=".zip"
        onChange={handleChange}
        disabled={disabled}
        className="sr-only"
      />
    </label>
  );
}

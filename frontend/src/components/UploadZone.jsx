import { useRef } from 'react'

export default function UploadZone({ label, accept = '.docx,.pdf', onFile, file }) {
  const inputRef = useRef()

  const handleDrop = (e) => {
    e.preventDefault()
    const dropped = e.dataTransfer.files[0]
    if (dropped) onFile(dropped)
  }

  return (
    <div
      className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center cursor-pointer hover:border-blue-400 transition-colors"
      onClick={() => inputRef.current.click()}
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => onFile(e.target.files[0])}
      />
      {file ? (
        <p className="text-sm text-green-600 font-medium">{file.name}</p>
      ) : (
        <>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-xs text-gray-400 mt-1">Click or drag & drop — {accept}</p>
        </>
      )}
    </div>
  )
}

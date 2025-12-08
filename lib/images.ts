import path from 'path';
import fs from 'fs';

/**
 * Get the filesystem path to an image in the public/images folder
 * Use this in API routes or server-side code
 */
export function getImagePath(imageName: string): string {
  return path.join(process.cwd(), 'public', 'images', imageName);
}

/**
 * Get the public URL path for an image
 * Use this in frontend components (Next.js automatically serves files from /public)
 */
export function getImageUrl(imageName: string): string {
  return `/images/${imageName}`;
}

/**
 * Save uploaded file to public/uploads directory
 */
export function saveUploadedFile(file: File, filename: string): string {
  const uploadsDir = path.join(process.cwd(), 'public', 'uploads');
  if (!fs.existsSync(uploadsDir)) {
    fs.mkdirSync(uploadsDir, { recursive: true });
  }
  
  const filePath = path.join(uploadsDir, filename);
  // Note: In Next.js API routes, you'll need to handle file uploads differently
  // This is a placeholder - actual implementation will be in the API route
  return `/uploads/${filename}`;
}


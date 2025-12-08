import jwt from 'jsonwebtoken';
import { getDatabase } from './db';

const JWT_SECRET = process.env.JWT_SECRET || 'scope-attendance-secret-key-change-in-production';

export interface TokenPayload {
  userId: number;
  email: string;
}

export function generateToken(userId: number, email: string): string {
  return jwt.sign({ userId, email }, JWT_SECRET, { expiresIn: '7d' });
}

export function verifyToken(token: string): TokenPayload | null {
  try {
    const decoded = jwt.verify(token, JWT_SECRET) as TokenPayload;
    return decoded;
  } catch (error) {
    return null;
  }
}

export function getUserIdFromRequest(request: Request): number | null {
  const authHeader = request.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return null;
  }

  const token = authHeader.substring(7);
  const payload = verifyToken(token);
  return payload?.userId || null;
}


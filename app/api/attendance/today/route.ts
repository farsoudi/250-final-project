import { NextResponse } from 'next/server';
import { getDatabase } from '@/lib/db';
import { getUserIdFromRequest } from '@/lib/auth';

export async function GET(request: Request) {
  try {
    const userId = getUserIdFromRequest(request);
    if (!userId) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const db = getDatabase();
    const today = new Date().toISOString().split('T')[0];

    const presentUsers = db.prepare(`
      SELECT u.id, u.name, u.email, u.team, u.major, u.graduating_class, u.profile_pic_path,
             a.checked_off_at
      FROM attendance a
      JOIN users u ON a.user_id = u.id
      WHERE a.date = ?
      ORDER BY a.checked_off_at DESC
    `).all(today);

    return NextResponse.json({ users: presentUsers, date: today });
  } catch (error) {
    console.error('Error fetching today\'s attendance:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}


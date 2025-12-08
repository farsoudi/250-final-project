import { NextResponse } from 'next/server';
import { getDatabase } from '@/lib/db';
import { getUserIdFromRequest } from '@/lib/auth';

export async function GET(
  request: Request,
  { params }: { params: { userId: string } }
) {
  try {
    const authUserId = getUserIdFromRequest(request);
    if (!authUserId) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const userId = parseInt(params.userId);
    if (isNaN(userId)) {
      return NextResponse.json(
        { error: 'Invalid user ID' },
        { status: 400 }
      );
    }

    const db = getDatabase();
    const user = db.prepare(`
      SELECT id, name, email, team, major, dob, graduating_class, profile_pic_path
      FROM users
      WHERE id = ?
    `).get(userId) as any;

    if (!user) {
      return NextResponse.json(
        { error: 'User not found' },
        { status: 404 }
      );
    }

    // Get attendance records
    const attendance = db.prepare(`
      SELECT date, checked_off_at
      FROM attendance
      WHERE user_id = ?
      ORDER BY date DESC
    `).all(userId);

    return NextResponse.json({
      user,
      attendance,
    });
  } catch (error) {
    console.error('Error fetching user:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}


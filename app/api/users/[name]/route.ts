import { NextResponse } from 'next/server';
import { getDatabase } from '@/lib/db';
import { getUserIdFromRequest } from '@/lib/auth';

export async function GET(
  request: Request,
  { params }: { params: { name: string } }
) {
  try {
    const authUserId = getUserIdFromRequest(request);
    if (!authUserId) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // Decode the name from URL
    const userName = decodeURIComponent(params.name);

    if (!userName || userName.trim() === '') {
      return NextResponse.json(
        { error: 'Invalid user name' },
        { status: 400 }
      );
    }

    const db = getDatabase();
    const user = db.prepare(`
      SELECT id, name, email, team, major, dob, graduating_class, profile_pic_path
      FROM users
      WHERE name = ?
    `).get(userName) as any;

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
    `).all(user.id);

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


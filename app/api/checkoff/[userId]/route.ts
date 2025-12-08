import { NextResponse } from 'next/server';
import { getDatabase } from '@/lib/db';
import { getUserIdFromRequest } from '@/lib/auth';

export async function POST(
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
    
    // Check if user exists
    const user = db.prepare('SELECT id FROM users WHERE id = ?').get(userId) as any;
    if (!user) {
      return NextResponse.json(
        { error: 'User not found' },
        { status: 404 }
      );
    }

    // Get today's date (YYYY-MM-DD format)
    const today = new Date().toISOString().split('T')[0];

    // Check if already checked off today
    const existing = db.prepare('SELECT id FROM attendance WHERE user_id = ? AND date = ?').get(userId, today) as any;
    if (existing) {
      return NextResponse.json(
        { error: 'User already checked off today' },
        { status: 400 }
      );
    }

    // Insert attendance record
    db.prepare('INSERT INTO attendance (user_id, date) VALUES (?, ?)').run(userId, today);

    return NextResponse.json({
      message: 'User checked off successfully',
      userId,
      date: today,
    });
  } catch (error) {
    console.error('Checkoff error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}


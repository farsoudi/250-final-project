import { NextResponse } from 'next/server';
import { getDatabase } from '@/lib/db';
import { getUserIdFromRequest } from '@/lib/auth';

export async function POST(
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
    
    // Check if user exists
    const user = db.prepare('SELECT id FROM users WHERE name = ?').get(userName) as any;
    if (!user) {
      return NextResponse.json(
        { error: 'User not found' },
        { status: 404 }
      );
    }

    // Get today's date (YYYY-MM-DD format)
    const today = new Date().toISOString().split('T')[0];

    // Check if already checked off today
    const existing = db.prepare('SELECT id FROM attendance WHERE user_id = ? AND date = ?').get(user.id, today) as any;
    if (existing) {
      return NextResponse.json(
        { error: 'User already checked off today' },
        { status: 400 }
      );
    }

    // Insert attendance record
    db.prepare('INSERT INTO attendance (user_id, date) VALUES (?, ?)').run(user.id, today);

    return NextResponse.json({
      message: 'User checked off successfully',
      name: userName,
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

export async function DELETE(
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
    
    // Check if user exists
    const user = db.prepare('SELECT id FROM users WHERE name = ?').get(userName) as any;
    if (!user) {
      return NextResponse.json(
        { error: 'User not found' },
        { status: 404 }
      );
    }

    // Get today's date (YYYY-MM-DD format)
    const today = new Date().toISOString().split('T')[0];

    // Check if user is checked off today
    const existing = db.prepare('SELECT id FROM attendance WHERE user_id = ? AND date = ?').get(user.id, today) as any;
    if (!existing) {
      return NextResponse.json(
        { error: 'User is not checked off today' },
        { status: 400 }
      );
    }

    // Delete attendance record
    db.prepare('DELETE FROM attendance WHERE user_id = ? AND date = ?').run(user.id, today);

    return NextResponse.json({
      message: 'User uncheckoff successfully',
      name: userName,
      date: today,
    });
  } catch (error) {
    console.error('Uncheckoff error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}


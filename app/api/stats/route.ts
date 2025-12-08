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

    // Total users
    const totalUsers = db.prepare('SELECT COUNT(*) as count FROM users').get() as any;

    // Attendance by team
    const attendanceByTeam = db.prepare(`
      SELECT u.team, COUNT(DISTINCT a.user_id) as user_count, COUNT(a.id) as attendance_count
      FROM attendance a
      JOIN users u ON a.user_id = u.id
      WHERE u.team IS NOT NULL
      GROUP BY u.team
      ORDER BY attendance_count DESC
    `).all();

    // Attendance by graduating class
    const attendanceByClass = db.prepare(`
      SELECT u.graduating_class, COUNT(DISTINCT a.user_id) as user_count, COUNT(a.id) as attendance_count
      FROM attendance a
      JOIN users u ON a.user_id = u.id
      WHERE u.graduating_class IS NOT NULL
      GROUP BY u.graduating_class
      ORDER BY u.graduating_class
    `).all();

    // Today's attendance
    const today = new Date().toISOString().split('T')[0];
    const todayAttendance = db.prepare('SELECT COUNT(*) as count FROM attendance WHERE date = ?').get(today) as any;

    // Most active users (top 10)
    const mostActiveUsers = db.prepare(`
      SELECT u.id, u.name, u.email, u.team, COUNT(a.id) as attendance_count
      FROM users u
      LEFT JOIN attendance a ON u.id = a.user_id
      GROUP BY u.id
      ORDER BY attendance_count DESC
      LIMIT 10
    `).all();

    return NextResponse.json({
      totalUsers: totalUsers.count,
      todayAttendance: todayAttendance.count,
      attendanceByTeam,
      attendanceByClass,
      mostActiveUsers,
    });
  } catch (error) {
    console.error('Error fetching statistics:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}


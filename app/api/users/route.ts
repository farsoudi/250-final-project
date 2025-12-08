import { NextResponse } from 'next/server';
import { getDatabase } from '@/lib/db';
import { getUserIdFromRequest } from '@/lib/auth';
import bcrypt from 'bcryptjs';
import { writeFile, mkdir } from 'fs/promises';
import path from 'path';

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
    const users = db.prepare(`
      SELECT id, name, email, team, major, dob, graduating_class, profile_pic_path
      FROM users
      ORDER BY name
    `).all();

    return NextResponse.json({ users });
  } catch (error) {
    console.error('Error fetching users:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  try {
    const userId = getUserIdFromRequest(request);
    if (!userId) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const formData = await request.formData();
    const name = formData.get('name') as string;
    const email = formData.get('email') as string;
    const password = formData.get('password') as string;
    const team = formData.get('team') as string;
    const major = formData.get('major') as string;
    const dob = formData.get('dob') as string;
    const graduatingClass = formData.get('graduating_class') as string;
    const profilePic = formData.get('profile_pic') as File | null;

    if (!name || !email || !password) {
      return NextResponse.json(
        { error: 'Name, email, and password are required' },
        { status: 400 }
      );
    }

    const db = getDatabase();

    // Check if email already exists
    const existing = db.prepare('SELECT id FROM users WHERE email = ?').get(email) as any;
    if (existing) {
      return NextResponse.json(
        { error: 'Email already exists' },
        { status: 400 }
      );
    }

    // Hash password
    const passwordHash = await bcrypt.hash(password, 10);

    // Handle profile picture upload
    let profilePicPath = null;
    if (profilePic && profilePic.size > 0) {
      const bytes = await profilePic.arrayBuffer();
      const buffer = Buffer.from(bytes);
      
      const uploadsDir = path.join(process.cwd(), 'public', 'uploads');
      try {
        await mkdir(uploadsDir, { recursive: true });
      } catch (error) {
        // Directory might already exist, ignore error
      }
      const filename = `${Date.now()}-${profilePic.name}`;
      const filePath = path.join(uploadsDir, filename);
      
      await writeFile(filePath, buffer);
      profilePicPath = `/uploads/${filename}`;
    }

    // Insert user
    const result = db.prepare(`
      INSERT INTO users (name, email, password_hash, team, major, dob, graduating_class, profile_pic_path)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      name,
      email,
      passwordHash,
      team || null,
      major || null,
      dob || null,
      graduatingClass ? parseInt(graduatingClass) : null,
      profilePicPath
    );

    return NextResponse.json({
      message: 'User created successfully',
      userId: result.lastInsertRowid,
    });
  } catch (error) {
    console.error('Error creating user:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}


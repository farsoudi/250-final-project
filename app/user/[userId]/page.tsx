'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import AuthGuard from '../../components/AuthGuard';
import Image from 'next/image';
import styles from './user.module.css';

interface User {
  id: number;
  name: string;
  email: string;
  team: string | null;
  major: string | null;
  dob: string | null;
  graduating_class: number | null;
  profile_pic_path: string | null;
}

interface AttendanceRecord {
  date: string;
  checked_off_at: string;
}

export default function UserPage() {
  const params = useParams();
  const userId = params.userId as string;
  const [user, setUser] = useState<User | null>(null);
  const [attendance, setAttendance] = useState<AttendanceRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUserData();
  }, [userId]);

  const fetchUserData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/users/${userId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
        setAttendance(data.attendance);
      }
    } catch (error) {
      console.error('Error fetching user data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <AuthGuard>
        <div className={styles.loading}>Loading...</div>
      </AuthGuard>
    );
  }

  if (!user) {
    return (
      <AuthGuard>
        <div className={styles.error}>User not found</div>
      </AuthGuard>
    );
  }

  return (
    <AuthGuard>
      <div className={styles.container}>
        <div className={styles.profileCard}>
          <div className={styles.avatarSection}>
            {user.profile_pic_path ? (
              <Image
                src={user.profile_pic_path}
                alt={user.name}
                width={120}
                height={120}
                className={styles.avatar}
              />
            ) : (
              <div className={styles.avatarPlaceholder}>
                {user.name.charAt(0).toUpperCase()}
              </div>
            )}
            <h1 className={styles.userName}>{user.name}</h1>
          </div>

          <div className={styles.infoSection}>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>Email:</span>
              <span className={styles.infoValue}>{user.email}</span>
            </div>
            {user.team && (
              <div className={styles.infoItem}>
                <span className={styles.infoLabel}>Team:</span>
                <span className={styles.infoValue}>{user.team}</span>
              </div>
            )}
            {user.major && (
              <div className={styles.infoItem}>
                <span className={styles.infoLabel}>Major:</span>
                <span className={styles.infoValue}>{user.major}</span>
              </div>
            )}
            {user.graduating_class && (
              <div className={styles.infoItem}>
                <span className={styles.infoLabel}>Graduating Class:</span>
                <span className={styles.infoValue}>{user.graduating_class}</span>
              </div>
            )}
            {user.dob && (
              <div className={styles.infoItem}>
                <span className={styles.infoLabel}>Date of Birth:</span>
                <span className={styles.infoValue}>
                  {new Date(user.dob).toLocaleDateString('en-US')}
                </span>
              </div>
            )}
          </div>
        </div>

        <div className={styles.attendanceCard}>
          <h2 className={styles.attendanceTitle}>
            Attendance Record ({attendance.length} {attendance.length === 1 ? 'day' : 'days'})
          </h2>
          {attendance.length === 0 ? (
            <p className={styles.noAttendance}>No attendance records yet.</p>
          ) : (
            <div className={styles.attendanceList}>
              {attendance.map((record, index) => (
                <div key={index} className={styles.attendanceItem}>
                  <div className={styles.attendanceDate}>
                    {formatDate(record.date)}
                  </div>
                  <div className={styles.attendanceTime}>
                    Checked off at {formatTime(record.checked_off_at)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </AuthGuard>
  );
}


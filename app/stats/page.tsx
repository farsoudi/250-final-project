'use client';

import { useEffect, useState } from 'react';
import AuthGuard from '../components/AuthGuard';
import styles from './stats.module.css';

interface TeamStats {
  team: string;
  user_count: number;
  attendance_count: number;
}

interface ClassStats {
  graduating_class: number;
  user_count: number;
  attendance_count: number;
}

interface ActiveUser {
  id: number;
  name: string;
  email: string;
  team: string | null;
  attendance_count: number;
}

interface Stats {
  totalUsers: number;
  todayAttendance: number;
  attendanceByTeam: TeamStats[];
  attendanceByClass: ClassStats[];
  mostActiveUsers: ActiveUser[];
}

export default function StatsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/stats', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <AuthGuard>
        <div className={styles.loading}>Loading statistics...</div>
      </AuthGuard>
    );
  }

  if (!stats) {
    return (
      <AuthGuard>
        <div className={styles.error}>Failed to load statistics</div>
      </AuthGuard>
    );
  }

  return (
    <AuthGuard>
      <div className={styles.container}>
        <h1 className={styles.title}>Statistics</h1>

        <div className={styles.statsGrid}>
          <div className={styles.statCard}>
            <div className={styles.statValue}>{stats.totalUsers}</div>
            <div className={styles.statLabel}>Total Users</div>
          </div>
          <div className={styles.statCard}>
            <div className={styles.statValue}>{stats.todayAttendance}</div>
            <div className={styles.statLabel}>Today&apos;s Attendance</div>
          </div>
        </div>

        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>Attendance by Team</h2>
          {stats.attendanceByTeam.length === 0 ? (
            <p className={styles.empty}>No team data available</p>
          ) : (
            <div className={styles.tableContainer}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Team</th>
                    <th>Members</th>
                    <th>Total Attendance</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.attendanceByTeam.map((team, index) => (
                    <tr key={index}>
                      <td>{team.team}</td>
                      <td>{team.user_count}</td>
                      <td>{team.attendance_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>Attendance by Graduating Class</h2>
          {stats.attendanceByClass.length === 0 ? (
            <p className={styles.empty}>No class data available</p>
          ) : (
            <div className={styles.tableContainer}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Graduating Class</th>
                    <th>Members</th>
                    <th>Total Attendance</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.attendanceByClass.map((classData, index) => (
                    <tr key={index}>
                      <td>Class of {classData.graduating_class}</td>
                      <td>{classData.user_count}</td>
                      <td>{classData.attendance_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>Most Active Users</h2>
          {stats.mostActiveUsers.length === 0 ? (
            <p className={styles.empty}>No user data available</p>
          ) : (
            <div className={styles.tableContainer}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Team</th>
                    <th>Attendance Count</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.mostActiveUsers.map((user) => (
                    <tr key={user.id}>
                      <td>{user.name}</td>
                      <td>{user.email}</td>
                      <td>{user.team || 'N/A'}</td>
                      <td>{user.attendance_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </AuthGuard>
  );
}


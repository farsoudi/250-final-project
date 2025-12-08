'use client';

import { useEffect, useState } from 'react';
import AuthGuard from './components/AuthGuard';
import Image from 'next/image';
import Link from 'next/link';
import styles from './page.module.css';

interface User {
  id: number;
  name: string;
  email: string;
  team: string | null;
  major: string | null;
  graduating_class: number | null;
  profile_pic_path: string | null;
}

interface PresentUser extends User {
  checked_off_at: string;
}

export default function Home() {
  const [allUsers, setAllUsers] = useState<User[]>([]);
  const [presentUsers, setPresentUsers] = useState<PresentUser[]>([]);
  const [date, setDate] = useState('');
  const [loading, setLoading] = useState(true);
  const [checkingOff, setCheckingOff] = useState<number | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Fetch all users
      const usersResponse = await fetch('/api/users', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      // Fetch today's attendance
      const attendanceResponse = await fetch('/api/attendance/today', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (usersResponse.ok && attendanceResponse.ok) {
        const usersData = await usersResponse.json();
        const attendanceData = await attendanceResponse.json();
        
        setAllUsers(usersData.users);
        setPresentUsers(attendanceData.users);
        setDate(attendanceData.date);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckoff = async (userId: number) => {
    setCheckingOff(userId);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/checkoff/${userId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        await fetchData();
      } else {
        const data = await response.json();
        alert(data.error || 'Failed to check off user');
      }
    } catch (error) {
      alert('An error occurred');
    } finally {
      setCheckingOff(null);
    }
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  const isPresent = (userId: number) => {
    return presentUsers.some(u => u.id === userId);
  };

  const getPresentUser = (userId: number) => {
    return presentUsers.find(u => u.id === userId);
  };

  return (
    <AuthGuard>
      <div className={styles.container}>
        <div className={styles.header}>
          <h1 className={styles.title}>Today&apos;s Attendance</h1>
          <p className={styles.date}>{date ? new Date(date).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }) : ''}</p>
          <p className={styles.count}>{presentUsers.length} of {allUsers.length} {allUsers.length === 1 ? 'person' : 'people'} present</p>
        </div>

        {loading ? (
          <div className={styles.loading}>Loading...</div>
        ) : allUsers.length === 0 ? (
          <div className={styles.empty}>
            <p>No users found. Add users to get started.</p>
          </div>
        ) : (
          <div className={styles.grid}>
            {allUsers.map((user) => {
              const present = isPresent(user.id);
              const presentUser = getPresentUser(user.id);
              
              return (
                <div key={user.id} className={`${styles.card} ${present ? styles.presentCard : ''}`}>
                  <Link href={`/user/${user.id}`} className={styles.cardLink}>
                    <div className={styles.avatar}>
                      {user.profile_pic_path ? (
                        <Image
                          src={user.profile_pic_path}
                          alt={user.name}
                          width={80}
                          height={80}
                          className={styles.avatarImage}
                        />
                      ) : (
                        <div className={styles.avatarPlaceholder}>
                          {user.name.charAt(0).toUpperCase()}
                        </div>
                      )}
                      {present && <div className={styles.presentBadge}>✓</div>}
                    </div>
                    <h3 className={styles.userName}>{user.name}</h3>
                    {user.team && <p className={styles.userInfo}>Team: {user.team}</p>}
                    {user.major && <p className={styles.userInfo}>{user.major}</p>}
                    {user.graduating_class && (
                      <p className={styles.userInfo}>Class of {user.graduating_class}</p>
                    )}
                    {present && presentUser && (
                      <p className={styles.checkoffTime}>
                        Checked off at {formatTime(presentUser.checked_off_at)}
                      </p>
                    )}
                  </Link>
                  <button
                    onClick={() => handleCheckoff(user.id)}
                    disabled={checkingOff === user.id || present}
                    className={`${styles.checkoffBtn} ${present ? styles.checkedOffBtn : ''}`}
                  >
                    {checkingOff === user.id ? 'Checking...' : present ? 'Already Checked Off' : 'Check Off'}
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </AuthGuard>
  );
}


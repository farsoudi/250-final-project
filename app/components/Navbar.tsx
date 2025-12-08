'use client';

import { useRouter } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import styles from './Navbar.module.css';

export default function Navbar() {
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };

  return (
    <nav className={styles.navbar}>
      <div className={styles.container}>
        <Link href="/" className={styles.logo}>
          <Image
            src="/images/scope.png"
            alt="Scope Logo"
            width={40}
            height={40}
            className={styles.logoImage}
          />
          <span className={styles.logoText}>Scope Attendance</span>
        </Link>
        <div className={styles.navLinks}>
          <Link href="/" className={styles.navLink}>Dashboard</Link>
          <Link href="/add-user" className={styles.navLink}>Add User</Link>
          <Link href="/stats" className={styles.navLink}>Statistics</Link>
          <button onClick={handleLogout} className={styles.logoutBtn}>
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}


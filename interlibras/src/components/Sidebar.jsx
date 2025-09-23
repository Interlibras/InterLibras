import styles from "../styles/Sidebar.module.css";

export default function Sidebar() {
    return (
    <div className={styles.sidebar}>
        <div className={styles.logo}></div>
        <button className={styles.btn}>Config</button>
        <button className={styles.btn}>Audio</button>
    </div>
    );
}

export default function Sidebar() {
    return (
    <aside className="sidebar">
        <div className="logo">
        <img src="../logo.jpeg" alt="InterLibras" />
        <h2>InterLibras</h2>
        </div>
        <nav>
        <button className="menu-btn">⚙ Config</button>
        <button className="menu-btn">🔊 Audio</button>
        </nav>
    </aside>
    );
}

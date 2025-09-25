"use client";
import React, { useState, useEffect } from "react";
import styles from "../styles/Sidebar.module.css";

export default function Sidebar() {
    const [openMenu, setOpenMenu] = useState(null);
    const [tema, setTema] = useState("claro");

    useEffect(() => {
        document.body.classList.remove("tema-claro", "tema-escuro");
        document.body.classList.add(tema === "claro" ? "tema-claro" : "tema-escuro");
    }, [tema]);

    function handleTemaClaro() {
        setTema("claro");
        setOpenMenu(null);
    }
    function handleTemaEscuro() {
        setTema("escuro");
        setOpenMenu(null);
    }

    return (
        <div className={styles.sidebar}>
            <div className={styles.logo}>
                <img src="/logo.png" alt="InterLibras Logo" style={{ width: "100%" }} />
            </div>
            <div className={styles.logoLine}></div> {/*Linnha fina embaixo */}

            {/* Dropdown Config */}
            <div
                className={`${styles.dropdown} ${openMenu === "config" ? styles.open : ""}`}
            >
                <button
                    className={styles.btn}
                    onClick={() =>
                        setOpenMenu(openMenu === "config" ? null : "config")
                    }
                >
                    Config
                </button>
                <div className={styles.dropdownMenu}>
                    <button
                        className={styles.dropdownItem}
                        onClick={handleTemaClaro}
                        disabled={tema === "claro"}
                    >
                        Tema Claro
                    </button>
                    <button
                        className={styles.dropdownItem}
                        onClick={handleTemaEscuro}
                        disabled={tema === "escuro"}
                    >
                        Tema Escuro
                    </button>
                </div>
            </div>
        </div>
    );
}

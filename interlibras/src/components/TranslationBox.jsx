"use client";
import React, { useState, useEffect } from "react";
import styles from "../styles/TranslationBox.module.css";

export default function TranslationBox() {
    const [translation, setTranslation] = useState("Carregando...");

    useEffect(() => {
    // 🔹 Aqui futuramente você vai chamar o backend
    // Por enquanto vou simular uma atualização a cada 3s
    const interval = setInterval(() => {
        setTranslation((prev) => prev + " bla");
    }, 3000);

    return () => clearInterval(interval);
    }, []);

    return (
    <div className={styles.translationBox}>
        <h3>Tradução</h3>
        <p>{translation}</p>
    </div>
    );
}

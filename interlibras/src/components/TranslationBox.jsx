"use client";
import React, { useState, useEffect } from "react";
import styles from "../styles/TranslationBox.module.css";

export default function TranslationBox() {
    const [translation, setTranslation] = useState("Carregando...");

    useEffect(() => {
        const API_URL = "http://localhost:8000/translate";

        const fetchTranslation = async () => {
            try {
                const res = await fetch(API_URL);
                if (!res.ok) throw new Error("Erro na resposta do servidor");
                const data = await res.json();
                setTranslation(data.translation || "Sem tradução disponível");
            } catch (error) {
                console.error("Erro ao buscar tradução:", error);
                setTranslation("Erro ao buscar tradução");
            }
        };

        const interval = setInterval(fetchTranslation, 100);

        return () => clearInterval(interval);
    }, []);

    return (
        <div className={styles.translationBox}>
            <div className={styles.translationLabel}>Tradução</div>
            <div className={styles.translationArea}>
                {translation}
            </div>
        </div>
    );
}

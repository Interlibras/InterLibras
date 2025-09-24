"use client";
import React, { useState } from "react";
import styles from "../styles/TranslationBox.module.css";

export default function TranslationBox() {
    const [translation, setTranslation] = useState("tradução das libras...");

    return (
        <div className={styles.translationBox}>
            <div className={styles.translationLabel}>Tradução</div>
            <div className={styles.translationArea}>
                {translation}
            </div>
        </div>
    );
}

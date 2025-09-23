"use client";
import React, { useState, useEffect } from "react";
import styles from "../styles/TranslationBox.module.css";
export default function TranslationBox() {
    const [translation, setTranslation] = useState("");


    return (
    <div className={styles.translationBox}>
        <h3>Tradução</h3>
        <p>{translation || "Aguardando tradução..."}</p>
    </div>
    );
}

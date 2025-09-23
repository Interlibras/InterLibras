"use client";
import React, { useEffect, useRef } from "react";
import styles from "../styles/VideoArea.module.css";
export default function VideoArea() {
    const videoRef = useRef(null);

    useEffect(() => {
    async function enableCamera() {
        try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
            videoRef.current.srcObject = stream;
        }
        } catch (err) {
        console.error("Erro ao acessar a câmera:", err);
        }
    }
    enableCamera();
    }, []);

    return (
    <div className={styles.videoContainer}>
        <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className={styles.video}
        />
    </div>
    );
}

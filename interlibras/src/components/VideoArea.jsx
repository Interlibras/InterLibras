"use client";
import React, { useEffect, useRef, useState } from "react";
import styles from "../styles/VideoArea.module.css";

export default function VideoArea() {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const streamRef = useRef(null);
    const requestRef = useRef();

    const [status, setStatus] = useState("Aguardando início da câmera...");
    const [isCameraOn, setIsCameraOn] = useState(false);

    const API_URL = "http://localhost:8000/frame";

    const stopCamera = () => {
        if (requestRef.current) {
            cancelAnimationFrame(requestRef.current);
            requestRef.current = null;
        }
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
        if (videoRef.current) {
            videoRef.current.srcObject = null;
        }
        setIsCameraOn(false);
        setStatus("Câmera parada.");
    };

    const captureAndSendFrame = async () => {
        if (!videoRef.current || !canvasRef.current || !streamRef.current) {
            return;
        }

        const video = videoRef.current;
        const canvas = canvasRef.current;
        const context = canvas.getContext("2d");

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        context.translate(canvas.width, 0);
        context.scale(-1, 1);
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        const dataUrl = canvas.toDataURL("image/png");

        try {
            await fetch(API_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ frame: dataUrl }),
            });
        } catch (error) {
            console.error("Erro ao enviar o frame:", error);
            setStatus(`Erro ao enviar o frame: ${error.message}`);
            stopCamera();
            return;
        }

        requestRef.current = requestAnimationFrame(captureAndSendFrame);
    };

    useEffect(() => {
        const enableCamera = async () => {
            try {
                if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                    if (videoRef.current) {
                        videoRef.current.srcObject = stream;
                        streamRef.current = stream;
                        setIsCameraOn(true);
                    }
                } else {
                    setStatus("API de mídia não suportada neste navegador.");
                }
            } catch (err) {
                console.error("Erro ao acessar a câmera:", err);
                setStatus(`Erro ao acessar a câmera: ${err.name}`);
                setIsCameraOn(false);
            }
        };

        enableCamera();

        return () => {
            stopCamera();
        };
    }, []);

    useEffect(() => {
        const startStreaming = () => {
            setStatus("Transmitindo frames...");
            requestRef.current = requestAnimationFrame(captureAndSendFrame);
        };

        if (isCameraOn && videoRef.current) {
            const videoElement = videoRef.current;
            videoElement.addEventListener('canplay', startStreaming);
            
            return () => {
                videoElement.removeEventListener('canplay', startStreaming);
                if (requestRef.current) {
                    cancelAnimationFrame(requestRef.current);
                }
            };
        }
    }, [isCameraOn]);

    return (
        <div className={styles.container}>
            <div className={styles.videoContainer}>
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className={styles.video}
                />
            </div>
            
            <canvas ref={canvasRef} style={{ display: "none" }} />

            <div className={styles.controls}>
                <button onClick={stopCamera} disabled={!isCameraOn}>
                    Parar Transmissão
                </button>
            </div>

            <div className={styles.status}>
                <p>{status}</p>
            </div>
        </div>
    );
}
"use client";
import React, { useEffect, useRef, useState } from "react";
import styles from "../styles/VideoArea.module.css";

export default function VideoArea() {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const streamRef = useRef(null);
    const requestRef = useRef(); // To hold the requestAnimationFrame ID

    // 1. Add a ref to act as our sending lock
    const isSendingRef = useRef(false);

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
        // 2. Check the lock. If a request is already in flight, exit immediately.
        // The currently running request is responsible for scheduling the next one.
        if (isSendingRef.current) {
            return;
        }
        
        if (!videoRef.current || !canvasRef.current || !streamRef.current) {
            // If the camera isn't ready, just schedule the next check and exit.
            requestRef.current = requestAnimationFrame(captureAndSendFrame);
            return;
        }

        // 3. Set the lock to prevent other frames from being sent.
        isSendingRef.current = true;

        try {
            const video = videoRef.current;
            const canvas = canvasRef.current;
            const context = canvas.getContext("2d");

            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;

            context.translate(canvas.width, 0);
            context.scale(-1, 1);
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            const dataUrl = canvas.toDataURL("image/png");

            await fetch(API_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ frame: dataUrl }),
            });
            setStatus("Frame enviado.");

        } catch (error) {
            console.error("Erro ao enviar o frame:", error);
            setStatus(`Erro ao enviar o frame: ${error.message}`);
            stopCamera(); // Optional: stop on error
        } finally {
            // 4. Release the lock and schedule the next frame capture.
            // This happens *after* the await is complete, ensuring we wait.
            isSendingRef.current = false;
            requestRef.current = requestAnimationFrame(captureAndSendFrame);
        }
    };

    // This useEffect starts the camera
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

    // This useEffect starts and stops the animation frame loop
    useEffect(() => {
        if (isCameraOn) {
            setStatus("Transmitindo frames...");
            // Start the loop
            requestRef.current = requestAnimationFrame(captureAndSendFrame);
        }
        
        // Cleanup function to cancel the loop if the camera is turned off
        return () => {
            if (requestRef.current) {
                cancelAnimationFrame(requestRef.current);
            }
        };
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
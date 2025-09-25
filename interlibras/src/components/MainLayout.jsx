"use client";
import React from "react";
import VideoArea from "./VideoArea";
import TranslationBox from "./TranslationBox";
import styles from "../styles/MainLayout.module.css";

export default function MainLayout() {
  return (
    <div className={styles.wrapper}>
      <VideoArea />
      <TranslationBox />
    </div>
  );
}

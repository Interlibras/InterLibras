import React from "react";
import Sidebar from "../components/Sidebar";
import VideoArea from "../components/VideoArea";
import TranslationBox from "../components/TranslationBox";
import styles from "./page.module.css";

export default function Home() {
  return (
    <div className={styles.page}>
      <Sidebar />

      <main className={styles.main}>
        <VideoArea />
        <TranslationBox />
      </main>
    </div>
  );
}

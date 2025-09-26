import React from "react";
import Sidebar from "../components/Sidebar";
import MainLayout from "@/components/MainLayout";
import styles from "./page.module.css";

export default function Home() {
  return (
    <div className={styles.page}>
      <Sidebar />

      <main className={styles.main}>
        <MainLayout/>
      </main>
    </div>
  );
}

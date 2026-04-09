import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";

// Initialize theme from persisted store before first render
const stored = localStorage.getItem("openoma-ui");
if (stored) {
  try {
    const { state } = JSON.parse(stored);
    const theme = state?.theme ?? "dark";
    document.documentElement.classList.add(theme);
  } catch {
    document.documentElement.classList.add("dark");
  }
} else {
  document.documentElement.classList.add("dark");
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);

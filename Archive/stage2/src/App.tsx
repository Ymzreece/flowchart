import { FunctionView } from "./pages/FunctionView";
import "./styles/index.css";
import { useTranslation } from "@i18n/useTranslation";

function App() {
  const { t } = useTranslation();
  return (
    <div className="app-shell" style={{ minHeight: "100vh" }}>
      <header className="app-header">
        <h1>{t("appTitle")}</h1>
      </header>
      <main className="app-main">
        <FunctionView />
      </main>
    </div>
  );
}

export default App;

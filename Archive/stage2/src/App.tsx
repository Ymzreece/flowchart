import { FunctionView } from "./pages/FunctionView";
import "./styles/index.css";

function App() {
  return (
    <div className="app-shell" style={{ minHeight: "100vh" }}>
      <header className="app-header">
        <h1>Flowchart Editor</h1>
      </header>
      <main className="app-main">
        <FunctionView />
      </main>
    </div>
  );
}

export default App;

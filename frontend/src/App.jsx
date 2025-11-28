import ChatWidget from "./components/ChatWidget";

export default function App() {
  return (
    <div style={{ fontFamily: "Arial, sans-serif" }}>
      <nav style={{ padding: '10px 20px', background: '#1766ef', color: 'white', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0, fontSize: '24px' }}>HealthCare Plus — Scheduling Agent</h1>
      </nav>

      <ChatWidget />

      <div style={{ padding: '50px', minHeight: '100vh' }}>
        <h2>Welcome to HealthCare Plus!</h2>
      </div>
    </div>
  );
}
import { useState } from "react";
import ChatInterface from "./ChatInterface";

const ChatIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
    </svg>
);
const CloseIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
        <line x1="18" y1="6" x2="6" y2="18"></line>
        <line x1="6" y1="6" x2="18" y2="18"></line>
    </svg>
);

export default function ChatWidget() {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div>
            {isOpen && (
                <div style={{
                    position: "fixed",
                    bottom: 120,
                    right: 40,
                    width: 380,
                    height: 520,
                    zIndex: 1000,
                    boxShadow: "0 8px 40px rgba(0,0,0,0.18)",
                    borderRadius: 12,
                    overflow: "hidden",
                    display: "flex",
                    flexDirection: "column",
                    backgroundColor: "#ffffff"
                }}>
                    <div style={{ padding: 12, background: "#1766ef", color: "white", fontSize: 16, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                            <div style={{ width: 36, height: 36, borderRadius: 8, background: "rgba(255,255,255,0.12)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.6"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
                            </div>
                            Paramedic
                        </div>
                        <button onClick={() => setIsOpen(false)} title="Close chat" style={{ background: "transparent", border: "none", cursor: "pointer" }}>
                            <CloseIcon />
                        </button>
                    </div>

                    <div style={{ flex: 1, minHeight: 0 }}>
                        <ChatInterface inWidget={true} />
                    </div>

                    <div style={{ padding: 8, textAlign: "center", fontSize: 12, color: "#666" }}>
                        Powered by Paramedic • {new Date().getFullYear()}
                    </div>
                </div>
            )}

            <button
                onClick={() => {
                    setIsOpen(!isOpen)
                    if (isOpen) {
                        localStorage.removeItem("paramedic_session_id");
                    }
                }}
                style={{
                    position: "fixed",
                    bottom: 40,
                    right: 40,
                    width: 60,
                    height: 60,
                    borderRadius: "50%",
                    backgroundColor: "#1766ef",
                    color: "white",
                    border: "none",
                    boxShadow: "0 6px 18px rgba(0,0,0,0.15)",
                    cursor: "pointer",
                    zIndex: 1001,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center"
                }}
                title={isOpen ? "Close Chat" : "Open Chat"}
            >
                {isOpen ? <CloseIcon /> : <ChatIcon />}
            </button>
        </div>
    );
}

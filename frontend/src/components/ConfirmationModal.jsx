import React, { useState, useEffect } from "react";


export default function ConfirmationModal({ open, slot, onClose, onConfirm }) {
    const [name, setName] = useState("");
    const [phone, setPhone] = useState("");
    const [email, setEmail] = useState("");

    useEffect(() => {
        if (!open) {
            setName("");
            setPhone("");
            setEmail("");
        }
    }, [open]);

    if (!open) return null;

    return (
        <div style={{
            position: "fixed", inset: 0, display: "flex", alignItems: "center", justifyContent: "center",
            background: "rgba(0,0,0,0.35)", zIndex: 9999
        }}>
            <div style={{ width: 520, maxWidth: "94%", background: "#fff", borderRadius: 12, padding: 20, boxShadow: "0 12px 40px rgba(0,0,0,0.18)" }}>
                <h3 style={{ marginTop: 0 }}>Confirm appointment</h3>

                <div style={{ marginBottom: 12 }}>
                    <div style={{ fontSize: 13, color: "#666" }}><strong>Time</strong></div>
                    <div style={{ marginTop: 6, fontSize: 15 }}>{slot?.date || ""} {slot?.start_time} — {slot?.end_time}</div>
                </div>

                <div style={{ display: "grid", gap: 8 }}>
                    <label style={{ fontSize: 13 }}>
                        Full name
                        <input value={name} onChange={e => setName(e.target.value)} placeholder="Jane Doe" style={{ width: "100%", padding: 10, marginTop: 6, borderRadius: 8, border: "1px solid #ddd" }} />
                    </label>
                    <label style={{ fontSize: 13 }}>
                        Phone
                        <input value={phone} onChange={e => setPhone(e.target.value)} placeholder="+1-555-0100" style={{ width: "100%", padding: 10, marginTop: 6, borderRadius: 8, border: "1px solid #ddd" }} />
                    </label>
                    <label style={{ fontSize: 13 }}>
                        Email
                        <input value={email} onChange={e => setEmail(e.target.value)} placeholder="jane@example.com" style={{ width: "100%", padding: 10, marginTop: 6, borderRadius: 8, border: "1px solid #ddd" }} />
                    </label>
                </div>

                <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 16 }}>
                    <button onClick={onClose} style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #ddd", background: "#fff" }}>Cancel</button>
                    <button onClick={() => {
                        if (!name || !phone || !email) return alert("Please fill name, phone and email.");
                        onConfirm({ name, phone, email, slot });
                    }} style={{ background: "#1766ef", color: "#fff", padding: "8px 14px", borderRadius: 8, border: "none" }}>
                        Confirm & Book
                    </button>
                </div>
            </div>
        </div>
    );
}

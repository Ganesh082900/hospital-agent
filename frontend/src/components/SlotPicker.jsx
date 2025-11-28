export default function SlotPicker({ slots = [], onSelect, onCancel }) {
    if (!slots || slots.length === 0) {
        return (
            <div style={{ padding: 12, borderRadius: 8, background: "#fff7e6", border: "1px solid #ffe0b2" }}>
                <strong>No available slots</strong>
                <div style={{ marginTop: 8 }}>Try another date or ask the agent to check alternatives.</div>
                <div style={{ marginTop: 8 }}>
                    <button onClick={onCancel} style={{ padding: "8px 12px", borderRadius: 6 }}>Check alternatives</button>
                </div>
            </div>
        );
    }

    return (
        <div style={{ padding: 12, borderRadius: 8, background: "#f7fbff", border: "1px solid #dbefff" }}>
            <div style={{ marginBottom: 8 }}><strong>Available slots</strong></div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {slots.map((s, i) => (
                    <button key={i}
                        onClick={() => onSelect(s)}
                        disabled={!s.available}
                        style={{
                            padding: "10px 12px",
                            borderRadius: 10,
                            border: s.available ? "1px solid #2b7cff" : "1px solid #ddd",
                            background: s.available ? "#eef6ff" : "#f3f3f3",
                            cursor: s.available ? "pointer" : "not-allowed",
                            minWidth: 140,
                            textAlign: "center"
                        }}>
                        <div style={{ fontWeight: 700 }}>{s.start_time}</div>
                        <div style={{ fontSize: 12, color: "#555" }}>{s.end_time}</div>
                    </button>
                ))}
            </div>
        </div>
    );
}

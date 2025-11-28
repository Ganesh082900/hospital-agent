import { useState, useEffect, useRef } from "react";
import SlotPicker from "./SlotPicker";
import ConfirmationModal from "./ConfirmationModal";
import { CLINIC_NAME, CLINIC_PHONE, BACKEND_URL } from "../config";


export default function ChatInterface({ inWidget = false }) {
    const [sessionId, setSessionId] = useState(() => {
        return localStorage.getItem("paramedic_session_id") || null;
    });
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [suggestedSlots, setSuggestedSlots] = useState([]);
    const [showModal, setShowModal] = useState(false);
    const [selectedSlot, setSelectedSlot] = useState(null);
    const ref = useRef();

    useEffect(() => { ref.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, suggestedSlots, showModal]);

    const pushAgent = (text) => setMessages(prev => [...prev, { from: "agent", text }]);
    const pushUser = (text) => setMessages(prev => [...prev, { from: "user", text }]);

    async function sendMessageRaw(payload) {
        const url = `${BACKEND_URL.replace(/\/$/, "")}/api/chat`;

        const sessionToSend =
            payload.session_id ||
            sessionId ||
            localStorage.getItem("paramedic_session_id") ||
            null;

        try {
            const resp = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: sessionToSend,
                    message: payload.message
                })
            });

            if (!resp.ok) {
                const txt = await resp.text();
                pushAgent("Error: backend returned " + resp.status + " — " + txt);
                return null;
            }

            const data = await resp.json();

            const newSession =
                data.session_id ||
                sessionToSend ||
                sessionId;

            if (newSession) {
                setSessionId(newSession);
                localStorage.setItem("paramedic_session_id", newSession);
            }

            return data;
        } catch (e) {
            pushAgent("Error: API connection failed — " + (e.message || e.toString()));
            return null;
        }
    }

    useEffect(() => {
        const localWelcome = `Welcome to ${CLINIC_NAME}. You can ask to book an appointment, check hours, insurance info, or clinic phone: ${CLINIC_PHONE}.`;
        pushAgent(localWelcome);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    async function sendMessage() {
        if (!input.trim()) return;
        const text = input.trim();
        pushUser(text);
        setInput("");
        const data = await sendMessageRaw({ session_id: sessionId, message: text });
        if (!data) return;
        handleAgentResponse(data);
    }

    function handleAgentResponse(data) {
        if (!data) return;
        if (data.type === "question") {
            pushAgent(data.question);
        } else if (data.type === "suggest_slots") {
            setSuggestedSlots(data.slots || []);
            pushAgent("I found some open slots — pick one from below.");
        } else if (data.type === "booking_conf") {
            const b = data.booking;
            // Pretty booking bubble per assessment
            const pretty = [
                "Booking Confirmed ✔️",
                `Appointment ID: ${b.booking_id}`,
                `Date: ${b.details.date}`,
                `Time: ${b.details.start_time} — ${b.details.end_time}`,
                `Clinic: ${CLINIC_NAME}`,
                `Confirmation code: ${b.confirmation_code}`
            ].join("\n");
            pushAgent(pretty);
            // reset
            setSuggestedSlots([]);
            setSelectedSlot(null);
            setShowModal(false);
        } else if (data.type === "faq") {
            pushAgent(data.answer);
        } else if (data.type === "no_slots") {
            pushAgent(data.message || "No slots found.");
            setSuggestedSlots([]);
        } else if (data.type === "error") {
            pushAgent(data.message || JSON.stringify(data));
            setSuggestedSlots([]);
        } else {
            // fallback: print the raw data if unfamiliar
            pushAgent(JSON.stringify(data, null, 2));
        }
    }

    function onPickSlot(slot) {
        setSuggestedSlots([]);
        setSelectedSlot(slot);
        setShowModal(true);
    }

    async function onConfirmBooking(patient) {
        setShowModal(false);
        setSuggestedSlots([]);

        pushUser(`Selected slot: ${selectedSlot.start_time} (${selectedSlot.end_time})`);

        await sendMessageRaw({
            session_id: sessionId,
            message: selectedSlot.start_time,
        });

        const patientCsv = `${patient.name}, ${patient.phone}, ${patient.email}`;
        pushUser(patientCsv);

        const data = await sendMessageRaw({
            session_id: sessionId,
            message: patientCsv
        });

        if (data) handleAgentResponse(data);
    }

    function onCancelModal() {
        setShowModal(false);
        setSelectedSlot(null);
    }

    return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', fontFamily: "Inter, Arial, sans-serif" }}>
            <div
                style={{
                    flex: 1,
                    padding: 16,
                    overflowY: 'auto',
                    background: "#ffffff",
                    minHeight: inWidget ? 'unset' : 360
                }}
            >
                {/* Clinic header (small) */}
                <div style={{ marginBottom: 12, color: "#333", fontSize: 13 }}>
                    <strong>{CLINIC_NAME}</strong> • <span style={{ color: "#666" }}>{CLINIC_PHONE}</span>
                </div>

                {messages.map((m, i) => (
                    <div key={i} style={{ textAlign: m.from === "user" ? "right" : "left", marginBottom: 12 }}>
                        <div style={{
                            display: "inline-block",
                            background: m.from === "user" ? "#e6f7ff" : "#f6f6f6",
                            padding: 12,
                            borderRadius: 16,
                            maxWidth: "86%",
                            whiteSpace: "pre-wrap",
                            lineHeight: 1.4,
                            borderTopLeftRadius: m.from === "agent" ? 6 : 16,
                            borderTopRightRadius: m.from === "user" ? 6 : 16,
                            boxShadow: m.from === "agent" ? "none" : "0 1px 0 rgba(0,0,0,0.03)"
                        }}>
                            <div style={{ fontSize: 14, color: "#111" }}>{m.text}</div>
                        </div>
                    </div>
                ))}

                {suggestedSlots && suggestedSlots.length > 0 && (
                    <div style={{ marginTop: 12 }}>
                        <SlotPicker slots={suggestedSlots} onSelect={onPickSlot} onCancel={() => {
                            (async () => {
                                const d = await sendMessageRaw({ session_id: sessionId, message: "Check other dates" });
                                if (d) handleAgentResponse(d);
                            })();
                        }} />
                    </div>
                )}

                <div ref={ref} />
            </div>

            <div style={{ display: "flex", padding: 12, borderTop: '1px solid #eee', background: '#fff' }}>
                <input
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    style={{ flex: 1, padding: 10, borderRadius: 8, border: '1px solid #ddd', outline: 'none' }}
                    placeholder="Type a message... (e.g. 'Book an appointment')"
                    onKeyDown={e => { if (e.key === 'Enter') sendMessage(); }}
                />
                <button onClick={sendMessage} style={{ marginLeft: 8, padding: "8px 14px", background: "#1766ef", color: "#fff", border: "none", borderRadius: 8 }}>
                    Send
                </button>
            </div>

            <ConfirmationModal
                open={showModal}
                slot={selectedSlot}
                onClose={onCancelModal}
                onConfirm={onConfirmBooking}
            />
        </div>
    );
}

// WebSocket configuration
// We try 'localhost' first as it's more reliable on Mac
const socket = new WebSocket("ws://localhost:8000/ws");
let socketReady = false;

socket.onopen = () => {
    socketReady = true;
    console.log("✅ WebSocket Connected to localhost");
    const out = document.getElementById("output");
    if (out) out.innerText = "Connected to Server";
};

socket.onclose = (event) => {
    socketReady = false;
    console.log("⚠ WebSocket Closed", event.code);
    const out = document.getElementById("output");
    if (out) out.innerText = "Server Disconnected. Re-run uvicorn.";
};

socket.onerror = (err) => {
    console.error("❌ socket error:", err);
};

// Handle messages from backend
socket.onmessage = (event) => {
    const data = JSON.parse(event.data);

    // 1. Update Reps & Accuracy
    if (data.reps !== undefined) {
        document.getElementById("repText").innerText = `Reps: ${data.reps}${data.total_reps ? ` (Total: ${data.total_reps})` : ''}`;
        if (data.accuracy !== undefined) {
            document.getElementById("accuracyText").innerText = `Accuracy: ${data.accuracy}%`;
        }
    }

    // 2. Feedback & Status
    if (data.feedback) {
        const feedback = data.feedback.form || Object.values(data.feedback)[0] || "Tracking...";
        const formEl = document.getElementById("formText");
        if (formEl) formEl.innerText = feedback;

        const statusEl = document.getElementById("statusText");
        if (statusEl) {
            const fbLower = feedback.toLowerCase();
            if (fbLower.includes("good") || fbLower.includes("correct")) {
                statusEl.innerText = "Correct ✔";
                statusEl.style.color = "green";
            } else if (fbLower.includes("waiting") || fbLower.includes("position") || fbLower.includes("steady")) {
                statusEl.innerText = "Waiting...";
                statusEl.style.color = "orange";
            } else {
                statusEl.innerText = "Improve";
                statusEl.style.color = "red";
            }
        }
    }

    // 3. Draw Skeleton
    if (data.landmarks) {
        drawSkeleton(data.landmarks);
    }
};

// Controls
function selectExercise(type) {
    if (socketReady) {
        console.log("Selecting:", type);
        socket.send(JSON.stringify({ exercise: type }));
        const out = document.getElementById("output");
        if (out) out.innerText = `Exercise: ${type.toUpperCase()}`;
    } else {
        alert("Server not connected! Please start the backend server.");
    }
}

function resetStats() {
    if (socketReady && confirm("Reset session?")) {
        socket.send(JSON.stringify({ action: "reset" }));
    }
}

// Visualization
function drawSkeleton(landmarks) {
    const canvas = document.getElementById("canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#00ff00";

    landmarks.forEach(lm => {
        ctx.beginPath();
        ctx.arc(lm.x * canvas.width, lm.y * canvas.height, 4, 0, Math.PI * 2);
        ctx.fill();
    });
}

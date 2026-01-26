const socket = new WebSocket("ws://127.0.0.1:8000/ws");

// ========== CONNECTION EVENTS ==========

socket.onopen = () => {
    console.log("✅ Connected to WebSocket");
    const out = document.getElementById("output");
    if (out) out.innerText = "Connected to server";
};

socket.onerror = (e) => {
    console.error("❌ WebSocket error", e);
};

socket.onclose = () => {
    console.log("⚠️ WebSocket closed");
};

// ========== EXERCISE SELECT ==========

function selectExercise(type) {
    socket.send(JSON.stringify({ exercise: type }));
    const out = document.getElementById("output");
    if (out) out.innerText = `Started ${type}`;
}

// ========== RECEIVE DATA FROM BACKEND ==========

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("DATA:", data);

    // reps + feedback
    if (data.reps !== undefined && data.feedback) {
        document.getElementById("repText").innerText = `Reps: ${data.reps}`;
        document.getElementById("formText").innerText = `Form: ${data.feedback.form}`;

        const status = document.getElementById("statusText");
        if (data.feedback.form.toLowerCase().includes("correct")) {
            status.innerText = "Correct ✔";
            status.style.color = "green";
        } else {
            status.innerText = "Incorrect ❌";
            status.style.color = "red";
        }
    }

    // landmarks
    if (data.landmarks) {
        drawSkeleton(data.landmarks);
    }
};

// ========== DRAW LANDMARKS ==========

function drawSkeleton(landmarks) {
    const canvas = document.getElementById("canvas");
    const ctx = canvas.getContext("2d");

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#00ff00";

    landmarks.forEach(lm => {
        const x = lm.x * canvas.width;
        const y = lm.y * canvas.height;
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
    });
}
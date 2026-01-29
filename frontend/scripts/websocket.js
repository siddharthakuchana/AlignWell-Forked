const socket = new WebSocket("ws://127.0.0.1:8000/ws");

let socketReady = false;

// ------------------ CONNECTION ------------------

socket.onopen = () => {
    socketReady = true;
    console.log("✅ Connected to WebSocket");
    const out = document.getElementById("output");
    if (out) out.innerText = "Connected to server";
};

socket.onerror = (e) => {
    console.error("❌ WebSocket error", e);
};

socket.onclose = () => {
    socketReady = false;
    console.log("⚠ WebSocket closed");
};

// ------------------ EXERCISE SELECTION ------------------

function selectExercise(type) {
    if (!socketReady) {
        alert("Server not connected yet");
        return;
    }

    console.log("🏋 Exercise selected:", type);
    window.selectedExercise = type;   // store globally

    socket.send(JSON.stringify({ exercise: type }));

    const out = document.getElementById("output");
    if (out) out.innerText = `Started ${type}`;
}

// ------------------ RESET ------------------

function resetStats() {
    if (confirm("Are you sure you want to reset all stats for this session?")) {
        socket.send(JSON.stringify({ action: "reset" }));
    }
}

// ------------------ RECEIVE FROM BACKEND ------------------

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("DATA:", data);

    // -------- REPS & ACCURACY --------
    if (data.reps !== undefined) {
        const repText = document.getElementById("repText");
        const totalReps = data.total_reps !== undefined ? ` (Total: ${data.total_reps})` : "";
        if (repText) repText.innerText = `Reps: ${data.reps}${totalReps}`;

        const accuracyText = document.getElementById("accuracyText");
        if (accuracyText && data.accuracy !== undefined) {
            accuracyText.innerText = `Accuracy: ${data.accuracy}%`;
        }
    }

    // -------- ANGLES --------
    if (data.angles) {
        const angleDisplay = document.getElementById("angleDisplay");
        const angleContent = document.getElementById("angleContent");

        if (angleDisplay && angleContent) {
            angleDisplay.style.display = "block";
            let angleHtml = "";
            let sum = 0;
            let count = 0;

            for (const [name, val] of Object.entries(data.angles)) {
                angleHtml += `<div>${name}: ${val}°</div>`;
                if (name.includes("elbow") || name.includes("knee")) {
                    sum += val;
                    count++;
                }
            }

            if (count > 1) {
                angleHtml += `<div style="border-top:1px solid #ddd;margin-top:5px;font-weight:bold;">
                                Average: ${Math.round(sum / count)}°
                              </div>`;
            }

            angleContent.innerHTML = angleHtml;
        }
    }

    // -------- FEEDBACK --------
    if (data.feedback) {
        let primaryFeedback = "";

        for (const [key, value] of Object.entries(data.feedback)) {
            if (["form", "posture", "knee", "elbow"].includes(key)) {
                if (!primaryFeedback || primaryFeedback.toLowerCase().includes("good")) {
                    primaryFeedback = value;
                }
            }
        }

        const formText = document.getElementById("formText");
        if (formText) formText.innerText = primaryFeedback || "Tracking...";

        const status = document.getElementById("statusText");
        if (status) {
            const fbLower = (primaryFeedback || "").toLowerCase();

            if (fbLower.includes("good") || fbLower.includes("correct")) {
                status.innerText = "Correct ✔";
                status.style.color = "green";
            } else if (
                fbLower.includes("person") ||
                fbLower.includes("frame") ||
                fbLower.includes("waiting") ||
                fbLower.includes("steady") ||
                fbLower.includes("position")
            ) {
                status.innerText = "Waiting...";
                status.style.color = "orange";
            } else {
                status.innerText = "Improve";
                status.style.color = "red";
            }
        }
    }

    // -------- LANDMARKS --------
    if (data.landmarks && data.landmarks.length > 0) {
        drawSkeleton(data.landmarks);
    } else {
        const canvas = document.getElementById("canvas");
        const ctx = canvas.getContext("2d");
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
};

// ------------------ DRAW SKELETON ------------------

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

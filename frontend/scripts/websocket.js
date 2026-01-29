const socket = new WebSocket("ws://127.0.0.1:8000/ws");

//websocket connection establishment
socket.onopen = () => {
    console.log("✅ Connected to WebSocket");
    const out = document.getElementById("output");
    if (out) out.innerText = "Connected to server";
};

//if error display error in console
socket.onerror = (e) => {
    console.error("WebSocket error", e);
};

//websocket connection termination
socket.onclose = () => {
    console.log("WebSocket closed");
};

//send the exercise type you selected to the backend
function selectExercise(type) {
    socket.send(JSON.stringify({ exercise: type }));
    const out = document.getElementById("output");
    if (out) out.innerText = `Started ${type}`;
}

function resetStats() {
    if (confirm("Are you sure you want to reset all stats for this session?")) {
        socket.send(JSON.stringify({ action: "reset" }));
    }
}

//receiving data from the backend
socket.onmessage = (event) => {
    // the data in the event is a json string, so we parse it
    const data = JSON.parse(event.data);
    console.log("DATA:", data);

    //update the reps and total reps
    if (data.reps !== undefined) {
        const repText = document.getElementById("repText");
        //reps are updated live in real time
        const totalReps = data.total_reps !== undefined ? ` (Total: ${data.total_reps})` : "";
        if (repText) repText.innerText = `Reps: ${data.reps}${totalReps}`;

        const accuracyText = document.getElementById("accuracyText");
        //accuracy is updated live in real time
        if (accuracyText && data.accuracy !== undefined) {
            accuracyText.innerText = `Accuracy: ${data.accuracy}%`;
        }

        // Handle Angles if present
        if (data.angles) {
            const angleDisplay = document.getElementById("angleDisplay");
            const angleContent = document.getElementById("angleContent");
            //angles are updated live in real time
            if (angleDisplay && angleContent) {
                angleDisplay.style.display = "block";
                let angleHtml = "";
                let sum = 0;
                let count = 0;
                // all the angles are given as they are run through the loop
                for (const [name, val] of Object.entries(data.angles)) {
                    angleHtml += `<div>${name}: ${val}°</div>`;
                    if (name.includes("elbow") || name.includes("knee")) {
                        sum += val;
                        count++;
                    }
                }
                // this is the average of all angles which is optional(we'll look about it later)
                if (count > 1) {
                    angleHtml += `<div style="border-top: 1px solid #ddd; margin-top: 5px; font-weight: bold;">Average: ${Math.round(sum / count)}°</div>`;
                }
                angleContent.innerHTML = angleHtml;
            }
        }

        if (data.feedback) {
            // Handle dynamic feedback keys (form, posture, etc.)
            let primaryFeedback = "";
            for (const [key, value] of Object.entries(data.feedback)) {
                if (["form", "posture", "knee", "elbow"].includes(key)) {
                    // Combine feedback if multiple exist, or pick the first important one
                    if (!primaryFeedback || primaryFeedback.toLowerCase().includes("good")) {
                        primaryFeedback = value;
                    }
                }
            }

            //form text is updated live in real time
            const formText = document.getElementById("formText");
            if (formText) {
                formText.innerText = primaryFeedback || "Tracking...";
            }

            // the status is the feedback given to the user
            const status = document.getElementById("statusText");
            if (status) {
                const fbLower = primaryFeedback.toLowerCase();
                const isCorrect = fbLower.includes("good") || fbLower.includes("correct");
                const isNeutral = fbLower.includes("person") || fbLower.includes("frame") || fbLower.includes("waiting");

                if (isCorrect) {
                    status.innerText = "Correct ✔";
                    status.style.color = "green";
                } else if (isNeutral || fbLower.includes("steady") || fbLower.includes("position") || fbLower.includes("horizontal") || fbLower.includes("lay down")) {
                    status.innerText = "Waiting...";
                    status.style.color = "orange";
                } else {
                    status.innerText = fbLower ? "Improve" : "Waiting...";
                    status.style.color = fbLower ? "red" : "orange";
                }
            }
        }
    }

    // landmarks are the points on the body
    if (data.landmarks) {
        drawSkeleton(data.landmarks);
    }
};

//draws the landmarks on the canvas
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
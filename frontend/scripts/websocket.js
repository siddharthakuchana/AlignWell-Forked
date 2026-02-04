console.log("AlignWell WebSocket Script V1.3 Loaded");
//dynamic websocket url
const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
//create websocket connection
const socket = new WebSocket(`${protocol}//${window.location.host}/ws`);

//variables initialization, socketReady is used to check if the socket is ready to send messages
let socketReady = false;
window.selectedExercise = null;

//function to handle the socket open event
socket.onopen = () => {
    socketReady = true;
    console.log("✅ WebSocket Connected");
};

//function to handle the socket message event
socket.onmessage = (event) => {
    const data = JSON.parse(event.data);

    //body status elements are taken, from the detect.html to display what is necessary 
    const bodyEl = document.getElementById("bodyStatusText");
    const statusEl = document.getElementById("statusText");
    const statusBox = document.getElementById("statusBox");

    if (bodyEl && statusEl && statusBox) {
        //if landmarks are not detected then show out of frame
        if (!data.landmarks || data.landmarks.length === 0) {
            bodyEl.innerText = "OUT OF FRAME";
            bodyEl.style.color = "#e53e3e";
            statusEl.innerText = "Searching for body...";
            statusBox.style.background = "#fff5f5";
            statusEl.style.color = "#c53030";
        } else {
            //if detected then show active
            bodyEl.innerText = "ACTIVE";
            bodyEl.style.color = "#38a169";

            //handle feedback/status logic
            if (data.feedback) {
                const feedback = data.feedback.form || Object.values(data.feedback)[0] || "Tracking...";
                const formEl = document.getElementById("formText");
                if (formEl) formEl.innerText = feedback;

                const fb = feedback.toLowerCase();
                if (fb.includes("good") || fb.includes("correct") || fb.includes("ready")) {
                    statusEl.innerText = "Correct ✔";
                    statusEl.style.color = "#2f855a";
                    statusBox.style.background = "#f0fff4";
                } else if (fb.includes("waiting") || fb.includes("steady") || fb.includes("position")) {
                    statusEl.innerText = "Steady...";
                    statusEl.style.color = "#b7791f";
                    statusBox.style.background = "#fffaf0";
                } else if (fb.includes("none") || fb === "--" || !fb) {
                    statusEl.innerText = "Tracking...";
                    statusEl.style.color = "#4a5568";
                    statusBox.style.background = "#f7fafc";
                } else {
                    statusEl.innerText = feedback; //show the actual advice
                    statusEl.style.color = "#c53030";
                    statusBox.style.background = "#fff5f5";
                }
            }
        }
    }

    //handle reps and accuracy
    if (data.reps !== undefined) {
        const repEl = document.getElementById("repText");
        if (repEl) {
            repEl.innerText = data.reps;
        }

        const accEl = document.getElementById("accuracyText");
        if (accEl) accEl.innerText = `${data.accuracy || 0}%`;
    }

    //draw skeleton points on canvas
    if (data.landmarks) drawSkeleton(data.landmarks);
};

//enhanced exercise selection
function selectExercise(type) {
    window.selectedExercise = type;

    //highlight the selected exercise
    document.querySelectorAll('.exercise').forEach(el => {
        const elText = el.innerText.toLowerCase();
        el.classList.toggle('active', elText.includes(type.substring(0, 3)));
    });

    //update the exercise title
    const title = document.getElementById("exerciseTitle");
    if (title) title.innerText = type.charAt(0).toUpperCase() + type.slice(1);

    //send the exercise type to the backend, to start exercise tracking
    if (socketReady) {
        socket.send(JSON.stringify({ exercise: type }));
    }
}

//reset the session stats
function resetStats() {
    if (socketReady && confirm("Reset session stats?")) {
        socket.send(JSON.stringify({ action: "reset" }));
    }
}

//draw skeleton points on canvas 
function drawSkeleton(landmarks) {
    const canvas = document.getElementById("canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!landmarks || landmarks.length === 0) return;

    ctx.fillStyle = "#00ff00";
    landmarks.forEach(lm => {
        ctx.beginPath();
        ctx.arc(lm.x * canvas.width, lm.y * canvas.height, 4, 0, Math.PI * 2);
        ctx.fill();
    });
}
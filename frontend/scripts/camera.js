console.log("📷 AlignWell Camera Script V1.3 Loaded");
// Global variables (set when camera starts)
let video = null;
let canvas = null;
let ctx = null;

// Offscreen canvas for processing frames
const captureCanvas = document.createElement("canvas");
const captureCtx = captureCanvas.getContext("2d");

let stream = null;
let sendInterval = null;

async function startCamera() {
    // Only fetch elements when we actually start the camera
    video = document.getElementById("video");
    canvas = document.getElementById("canvas");

    if (!video || !canvas) {
        console.error("Camera elements not found on this page.");
        return;
    }

    ctx = canvas.getContext("2d");

    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;

        video.onloadedmetadata = () => {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            captureCanvas.width = video.videoWidth;
            captureCanvas.height = video.videoHeight;
        };

        // ✅ If an exercise was selected before starting, tell the backend now
        if (window.selectedExercise && typeof selectExercise === 'function') {
            selectExercise(window.selectedExercise);
        }

        if (sendInterval) clearInterval(sendInterval);
        sendInterval = setInterval(sendFrame, 100);
        console.log("✅ Camera Started");
    } catch (err) {
        console.error("❌ Camera error:", err);
        alert("Could not start camera. Please check permissions.");
    }
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(t => t.stop());
        stream = null;
    }
    if (sendInterval) {
        clearInterval(sendInterval);
        sendInterval = null;
    }
    if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
    console.log("🛑 Camera Stopped");
}

function sendFrame() {
    // Check if socket is ready (from websocket.js)
    if (typeof socket === 'undefined' || socket.readyState !== 1 || !video || !video.videoWidth) return;

    captureCtx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);
    const img = captureCanvas.toDataURL("image/jpeg", 0.7); // 0.7 adds slight compression for speed
    socket.send(img);
}
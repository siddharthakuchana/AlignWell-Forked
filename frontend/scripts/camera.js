const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

// offscreen canvas only for sending frames
const captureCanvas = document.createElement("canvas");
const captureCtx = captureCanvas.getContext("2d");

let stream = null;
let sendInterval = null;

async function startCamera() {
    stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;

    video.onloadedmetadata = () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        captureCanvas.width = video.videoWidth;
        captureCanvas.height = video.videoHeight;
    };

    // ✅ resend exercise so backend resets tracker
    if (window.selectedExercise) {
        socket.send(JSON.stringify({ exercise: window.selectedExercise }));
    }

    sendInterval = setInterval(sendFrame, 100);
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

    // ✅ clear landmarks
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

function sendFrame() {
    if (!socket || socket.readyState !== 1 || !video.videoWidth) return;

    // draw video only to offscreen canvas
    captureCtx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);
    const img = captureCanvas.toDataURL("image/jpeg");
    socket.send(img);
}

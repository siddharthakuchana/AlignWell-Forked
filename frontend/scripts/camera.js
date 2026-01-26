const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

let stream = null;
let sendInterval = null;

async function startCamera() {
    stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;

    video.onloadedmetadata = () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
    };

    sendInterval = setInterval(sendFrame, 120);
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(t => t.stop());
    }
    clearInterval(sendInterval);
}

function sendFrame() {
    if (!socket || socket.readyState !== 1) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const img = canvas.toDataURL("image/jpeg");
    socket.send(img);
}

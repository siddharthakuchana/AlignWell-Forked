console.log("AlignWell Camera Script V1.3 Loaded");
//global variables initially when the camera starts
let video = null;
let canvas = null;
let ctx = null;

//offscreen canvas for processing frames
const captureCanvas = document.createElement("canvas");
const captureCtx = captureCanvas.getContext("2d");

//global variables for stream and send interval initially null
let stream = null;
let sendInterval = null;

//asyn function to start the camera
async function startCamera() {
    // Only fetch elements when we actually start the camera, because they might not exist on every page as we are extending base.html to every page
    video = document.getElementById("video");
    canvas = document.getElementById("canvas");

    //check if video and canvas elements exist
    if (!video || !canvas) {
        console.error("Camera elements not found on this page.");
        return;
    }

    //get context of canvas
    ctx = canvas.getContext("2d");

    //to get the user media
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        //set the src object of video to stream
        video.srcObject = stream;

        //set the canvas width and height to video width and height, to whatever the video is
        video.onloadedmetadata = () => {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            //set the offscreen canvas width and height to video width and height
            captureCanvas.width = video.videoWidth;
            captureCanvas.height = video.videoHeight;
        };

        // ✅ If an exercise was selected before starting, tell the backend now
        if (window.selectedExercise && typeof selectExercise === 'function') {
            selectExercise(window.selectedExercise);
        }

        //start sending frames to the backend
        if (sendInterval) clearInterval(sendInterval);
        sendInterval = setInterval(sendFrame, 100);
        console.log("✅ Camera Started");
    } catch (err) {
        console.error("❌ Camera error:", err);
        alert("Could not start camera. Please check permissions.");
    }
}

//function to stop the camera
function stopCamera() {
    //stop all the tracks of the stream
    if (stream) {
        stream.getTracks().forEach(t => t.stop());
        stream = null;
    }
    //stop the send interval
    if (sendInterval) {
        clearInterval(sendInterval);
        sendInterval = null;
    }
    //clear the canvas
    if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
    console.log("🛑 Camera Stopped");
}

//function to send the frames of image to the backend
function sendFrame() {
    // Check if socket is ready (from websocket.js)
    if (typeof socket === 'undefined' || socket.readyState !== 1 || !video || !video.videoWidth) return;

    //draw the video frame on the offscreen canvas
    captureCtx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);
    const img = captureCanvas.toDataURL("image/jpeg", 0.7); // 0.7 adds slight compression for speed
    socket.send(img);
}
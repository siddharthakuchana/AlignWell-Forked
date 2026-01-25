const socket = new WebSocket("ws://localhost:8000/ws");

// holds the id by setInterval(), used later to stop the frame sending loop
let streamInterval = null;

// 2. When connection opens
socket.onopen = () => {
    console.log("Connected to WebSocket");
    document.getElementById("output").innerText = "Connected to server";

    //starts sending frames from an already running camera
    if (videoStream) {
        startStreaming();
    }
};

//starts streaming, takes the id set by setInterval()
function startStreaming() {
    isStreaming = true;
    //runs the function repeatedly
    streamInterval = setInterval(() => {
        if (isStreaming && videoStream) {
            //takes current video frame and converts to base64 form, frame is wrapped as a json and returned as a string
            const frameData = captureFrame();
            if (!frameData) return;
            // sending the exercise type too
            socket.send(JSON.stringify({
                image: frameData
            }));
        }
    }, 1000 / 24);// this is the frame rate/ fps control
}

function stopStreaming() {
    isStreaming = false;
    if (streamInterval) {
        clearInterval(streamInterval);//clears the interval loop
    }
}

socket.onclose = () => {
    stopStreaming(); //when the socket is closed, the webcam is stopped
}

// 3. When message is received from server
socket.onmessage = (event) => {
    console.log("Message from server:", event.data);
    document.getElementById("output").innerText = event.data;
};

// 4. Send message to server
function sendMessage() {
    socket.send("Hello from browser");
}


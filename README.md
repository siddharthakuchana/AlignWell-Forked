# 🏋️‍♂️ AlignWell – AI-Based Exercise Posture Correction & Fitness Game

## 🚀 Overview

**AlignWell** is an intelligent fitness application that combines **computer vision**, **real-time posture correction**, and **gamification** to enhance workout quality and user engagement.
It analyzes body movements, provides feedback on exercise posture, and integrates an interactive game to make workouts fun and effective.

---

## 🎯 Features

### 🧠 AI Posture Detection

* Real-time posture analysis using computer vision
* Joint angle calculation for accurate feedback
* Helps users perform exercises safely and correctly

### 🎮 Gamified Experience

* Interactive JavaScript-based game module
* Encourages consistency and motivation
* Makes workouts engaging and less monotonous

### 📊 Backend Integration

* FastAPI-powered backend for handling logic
* API-based communication between frontend and backend
* Scalable and modular architecture

### 🗄️ Database Support

* Cloud database (TiDB) integration
* Stores user data, performance, and progress
* Secure and structured data handling

### 🌐 Frontend Interface

* Clean and responsive UI
* Dynamic HTML, CSS, and JavaScript
* Real-time interaction with backend APIs

---

## 🛠️ Tech Stack

| Layer           | Technology                       |
| --------------- | -------------------------------- |
| Frontend        | HTML, CSS, JavaScript            |
| Backend         | FastAPI (Python)                 |
| Database        | TiDB (MySQL compatible)          |
| AI/ML           | Computer Vision (Pose Detection) |
| Version Control | Git & GitHub                     |

---

## 📂 Project Structure

```
AlignWell/
│
├── backend/
│   ├── database/
│   ├── routers/
│   ├── exercises/
│   ├── main.py
│
├── frontend/
│   ├── scripts/
│   ├── static/
│   ├── templates/
│
└── README.md
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the Repository

```
git clone https://github.com/your-username/alignwell.git
cd alignwell
```

---

### 2️⃣ Backend Setup

```
cd backend
pip install -r requirements.txt
```

---

### 3️⃣ Configure Environment Variables

Create a `.env` file inside `backend/`:

```
DB_USERNAME=your_username
PASSWORD=your_password
HOST=your_host
PORT=4000
DATABASE=your_database
SSL_CA=path_to_cert
```

---

### 4️⃣ Run the Server

```
uvicorn main:app --reload
```

---

### 5️⃣ Initialize Database

Open in browser:

```
http://127.0.0.1:8000/init-db
```

---

### 6️⃣ Access Application

```
http://127.0.0.1:8000
```

---

## 📸 Screenshots

*(Add your project screenshots here for better presentation)*

---

## 🧠 Future Enhancements

* Mobile responsiveness improvements
* Advanced AI models for better accuracy
* Leaderboard and social features
* Personalized workout recommendations

---

## 👨‍💻 Contributors

* Prithvi M
* Siddhartha K
* Siddharth G

---

## 📌 Note

This project is developed as part of a learning initiative to explore **AI + Web Development integration** and build real-world, impactful applications.

---

## ⭐ If you like this project

Give it a ⭐ on GitHub and share your feedback!


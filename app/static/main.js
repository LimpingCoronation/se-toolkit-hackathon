const authBlock = document.getElementById("auth-block");
const authButton = document.getElementById("auth-button");
const monitorBlock = document.getElementById("monitor-list");
const serversBlock = document.getElementById("servers");
const loginInput = document.getElementById("login");
const passwordInput = document.getElementById("password");
const buttonAdd = document.getElementById("button-add");
const buttonLogout = document.getElementById("button-logout");
const monitorAdd = document.getElementById("monitor-add");
const modalCancel = document.getElementById("modal-cancel");
const modalConfirm = document.getElementById("modal-confirm");
const serverUrlInput = document.getElementById("server-url");

let socket;
let heartbeatInterval;
const servers = {};

let token = localStorage.getItem("token") || "";

const BASE_URL = "http://10.93.25.129/:8000/";

// Auto-restore session if token exists
function initSession() {
    if (!token) return;

    authBlock.classList.add("hide");
    monitorBlock.classList.remove("hide");

    loadServers();

    socket = new WebSocket("ws://10.93.25.129/:8000/monitor", [token]);

    setupSocketHandlers();
}

function setupSocketHandlers() {
    socket.onopen = (e) => {
        console.log("Connection is accepted");
        heartbeatInterval = setInterval(() => {
            if (socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ type: "ping" }));
            }
        }, 5000);
    };

    socket.onmessage = (e) => {
        const data = e.data;
        console.log("WebSocket message:", data);

        // Try JSON format first (from send_json)
        try {
            const parsed = JSON.parse(data);
            if (parsed.service_id !== undefined && parsed.status !== undefined) {
                const serverId = String(parsed.service_id);
                const isAlive = parsed.status === 1;
                updateServerStatus(serverId, isAlive);
                return;
            }
        } catch (err) {
            // Not JSON, try plain text format: server_id:status
        }

        // Plain text format: server_id:is_alive[0 or 1]
        // send_json wraps strings in quotes, so strip them
        const cleanData = data.replace(/^"|"$/g, "");
        const parts = cleanData.split(":");
        if (parts.length === 2) {
            const serverId = parts[0].trim();
            const isAlive = parts[1].trim() === "1";
            updateServerStatus(serverId, isAlive);
        }
    };

    socket.onerror = (e) => {
        console.error("WebSocket error:", e);
    };

    socket.onclose = () => {
        console.log("WebSocket closed");
        clearInterval(heartbeatInterval);
    };
}

authButton.addEventListener("click", (e) => {
    fetch(BASE_URL + "users/sign-in/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            username: loginInput.value,
            password: passwordInput.value,
        }),
    })
        .then((res) => res.json())
        .then((data) => {
            if ("token" in data) {
                token = data["token"];
                localStorage.setItem("token", token);
                authBlock.classList.add("hide");
                monitorBlock.classList.remove("hide");

                loadServers();

                socket = new WebSocket("ws://localhost:8000/monitor", [token]);

                setupSocketHandlers();
            }
        })
        .catch((err) => console.error("Auth error:", err));
});

function loadServers() {
    fetch(BASE_URL + "services/list/", {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            authorization: 'Bearer ' + token,
        },
    })
        .then((res) => res.json())
        .then((data) => {
            data.forEach((element) => {
                addServer([element.id, element.url, element.is_alive, element.is_working, element.user_id]);
            });
        })
        .catch((err) => console.error("Load servers error:", err));
}

function addServer([id, url, is_alive, is_working, user_id]) {
    const serverItem = document.createElement("div");
    serverItem.classList.add("server-item");
    serverItem.dataset.id = id;

    const statusDot = document.createElement("div");
    statusDot.classList.add("server-item__status");
    statusDot.classList.add(is_alive ? "server-item__status--alive" : "server-item__status--dead");
    statusDot.dataset.status = is_alive ? "alive" : "dead";

    const urlText = document.createElement("div");
    urlText.classList.add("server-item__url");
    urlText.textContent = url;

    const toggleBtn = document.createElement("button");
    toggleBtn.classList.add("server-item__btn", "server-item__btn--toggle");
    toggleBtn.textContent = is_working ? "Stop" : "Start";

    const deleteBtn = document.createElement("button");
    deleteBtn.classList.add("server-item__btn", "server-item__btn--delete");
    deleteBtn.textContent = "Delete";

    toggleBtn.addEventListener("click", () => {
        const currentWorking = toggleBtn.textContent === "Stop";
        const endpoint = currentWorking ? "stop_monitor" : "monitor";
        const method = "POST";

        fetch(BASE_URL + `services/${endpoint}/${id}`, {
            method: method,
            headers: {
                "Content-Type": "application/json",
                authorization: 'Bearer ' + token,
            },
        })
            .then((res) => res.json())
            .then((data) => {
                const nowWorking = data.is_working;
                toggleBtn.textContent = nowWorking ? "Stop" : "Start";
                servers[id] = { id, url, is_alive: data.is_alive, is_working: nowWorking, user_id: data.user_id };
            })
            .catch((err) => console.error("Toggle monitoring error:", err));
    });

    deleteBtn.addEventListener("click", () => {
        fetch(BASE_URL + `services/remove/${id}`, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
                authorization: 'Bearer ' + token,
            },
        })
            .then((res) => res.json())
            .then((data) => {
                serverItem.remove();
                delete servers[id];
            })
            .catch((err) => console.error("Delete server error:", err));
    });

    serverItem.appendChild(statusDot);
    serverItem.appendChild(urlText);
    serverItem.appendChild(toggleBtn);
    serverItem.appendChild(deleteBtn);

    serversBlock.appendChild(serverItem);
    servers[id] = { id, url, is_alive, is_working, user_id };
}

function updateServerStatus(serverId, isAlive) {
    const serverItem = serversBlock.querySelector(`.server-item[data-id="${serverId}"]`);
    if (serverItem) {
        const statusDot = serverItem.querySelector(".server-item__status");
        statusDot.classList.remove("server-item__status--alive", "server-item__status--dead");
        statusDot.classList.add(isAlive ? "server-item__status--alive" : "server-item__status--dead");
        statusDot.dataset.status = isAlive ? "alive" : "dead";
    }

    if (servers[serverId]) {
        servers[serverId].is_alive = isAlive;
    }
}

// Modal open
buttonAdd.addEventListener("click", () => {
    monitorAdd.classList.remove("hide");
    serverUrlInput.value = "";
    serverUrlInput.focus();
});

// Modal close
modalCancel.addEventListener("click", () => {
    monitorAdd.classList.add("hide");
});

// Modal confirm — add server
modalConfirm.addEventListener("click", () => {
    const url = serverUrlInput.value.trim();
    if (!url) return;

    fetch(BASE_URL + "services/add", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            authorization: 'Bearer ' + token,
        },
        body: JSON.stringify({ url }),
    })
        .then((res) => res.json())
        .then((data) => {
            addServer([data.id, data.url, data.is_alive, data.is_working, data.user_id]);
            monitorAdd.classList.add("hide");
        })
        .catch((err) => console.error("Add server error:", err));
});

// Close modal on overlay click
document.getElementById("modal-overlay").addEventListener("click", (e) => {
    if (e.target.id === "modal-overlay") {
        monitorAdd.classList.add("hide");
    }
});

// Restore session on page load
initSession();

// Logout
buttonLogout.addEventListener("click", () => {
    localStorage.removeItem("token");
    token = "";
    if (socket) {
        socket.close();
    }
    clearInterval(heartbeatInterval);
    serversBlock.innerHTML = "";
    Object.keys(servers).forEach((key) => delete servers[key]);
    monitorBlock.classList.add("hide");
    authBlock.classList.remove("hide");
});

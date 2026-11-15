
const API = "/api";

let token = localStorage.getItem("token");
let eventsCache = [];
let qrScanner = null;

function authHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
    };
}

async function apiRequest(path, options = {}) {
    const response = await fetch(API + path, {
        ...options,
        headers: {
            ...authHeaders(),
            ...(options.headers || {})
        }
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.detail || data.error || "Request failed");
    }

    return data;
}

function showMessage(message, type = "success") {
    const box = document.getElementById("globalMessage");
    box.textContent = message;
    box.className = `alert alert-${type} mt-4`;
}

function showSection(sectionId) {
    document.querySelectorAll(".section").forEach(section => {
        section.classList.add("d-none");
    });

    document.getElementById(sectionId).classList.remove("d-none");

    if (sectionId === "eventsSection") loadEvents();
    if (sectionId === "bookingsSection") loadBookings();
    if (sectionId === "ticketsSection") loadTickets();
    if (sectionId === "adminSection") loadAdminStats();
}

function toggleAuth() {
    document.getElementById("loginForm").classList.toggle("d-none");
    document.getElementById("registerForm").classList.toggle("d-none");
    document.getElementById("authMessage").textContent = "";
}

// REGISTER
async function register() {
    const full_name = document.getElementById("registerName").value;
    const email = document.getElementById("registerEmail").value;
    const password = document.getElementById("registerPassword").value;

    try {
        await apiRequest("/auth/register", {
            method: "POST",
            body: JSON.stringify({ full_name, email, password })
        });

        document.getElementById("authMessage").textContent =
            "Registration successful! Please log in.";

        document.getElementById("authMessage").className =
            "text-success text-center mt-3";

        toggleAuth();
    } catch (error) {
        document.getElementById("authMessage").textContent = error.message;
    }
}

// LOGIN
async function login() {
    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;

    try {
        const result = await apiRequest("/auth/login", {
            method: "POST",
            body: JSON.stringify({ email, password })
        });

        token = result.access_token;
        localStorage.setItem("token", token);

        showMessage("Login successful!");
        showSection("eventsSection");
    } catch (error) {
        document.getElementById("authMessage").textContent = error.message;
    }
}

// LOGOUT
function logout() {
    localStorage.removeItem("token");
    token = null;
    stopScanner();
    showSection("authSection");
    showMessage("You have logged out.", "info");
}

// LOAD EVENTS
async function loadEvents() {
    try {
        eventsCache = await apiRequest("/events/", {
            method: "GET"
        });

        displayEvents(eventsCache);
    } catch (error) {
        showMessage(error.message, "danger");
    }
}

function displayEvents(events) {
    const container = document.getElementById("eventsList");
    container.replaceChildren();

    if (!events.length) {
        container.textContent = "No events available.";
        return;
    }

    events.forEach(event => {
        const column = document.createElement("div");
        column.className = "col-md-4";

        const card = document.createElement("div");
        card.className = "event-card";

        const title = document.createElement("h5");
        title.textContent = event.title;

        const description = document.createElement("p");
        description.textContent = event.description || "No description available.";

        const date = document.createElement("p");
        date.textContent = "Starts: " + new Date(event.start_time).toLocaleString();

        const price = document.createElement("p");
        price.textContent = "Ticket price: Rs. " + event.ticket_price;

        const capacity = document.createElement("p");
        capacity.textContent = "Capacity: " + event.capacity;

        const bookButton = document.createElement("button");
        bookButton.className = "btn btn-primary w-100";
        bookButton.textContent = "Book Tickets";
        bookButton.addEventListener("click", () => bookEvent(event.id));

        card.append(title, description, date, price, capacity, bookButton);
        column.appendChild(card);
        container.appendChild(column);
    });
}

// SEARCH EVENTS
function filterEvents() {
    const query = document.getElementById("eventSearch").value.toLowerCase();

    const filtered = eventsCache.filter(event =>
        event.title.toLowerCase().includes(query) ||
        (event.description || "").toLowerCase().includes(query)
    );

    displayEvents(filtered);
}

// BOOK EVENT
async function bookEvent(eventId) {
    if (!token) {
        showSection("authSection");
        showMessage("Please log in before booking.", "warning");
        return;
    }

    const quantity = Number(prompt("How many tickets do you need?"));

    if (!Number.isInteger(quantity) || quantity < 1 || quantity > 10) {
        showMessage("Please enter a quantity between 1 and 10.", "warning");
        return;
    }

    try {
        const result = await apiRequest("/bookings/", {
            method: "POST",
            body: JSON.stringify({
                event_id: eventId,
                quantity: quantity
            })
        });

        showMessage(
            `Booking successful! Payment reference: ${result.payment_reference}`
        );

        showSection("bookingsSection");
    } catch (error) {
        showMessage(error.message, "danger");
    }
}

// MY BOOKINGS
async function loadBookings() {
    try {
        const bookings = await apiRequest("/bookings/my-bookings");

        const container = document.getElementById("bookingsList");
        container.replaceChildren();

        if (!bookings.length) {
            container.textContent = "You have no bookings yet.";
            return;
        }

        bookings.forEach(booking => {
            const card = document.createElement("div");
            card.className = "content-card mb-3";

            const title = document.createElement("h5");
            title.textContent = "Booking #" + booking.id;

            const details = document.createElement("p");
            details.textContent =
                `Event ID: ${booking.event_id} | Tickets: ${booking.quantity} | Amount: Rs. ${booking.total_amount}`;

            const status = document.createElement("p");
            status.textContent =
                `Status: ${booking.status} | Payment: ${booking.payment_reference || "N/A"}`;

            card.append(title, details, status);
            container.appendChild(card);
        });
    } catch (error) {
        showMessage(error.message, "danger");
    }
}

// MY TICKETS
async function loadTickets() {
    try {
        const tickets = await apiRequest("/tickets/my-tickets");

        const container = document.getElementById("ticketsList");
        container.replaceChildren();

        if (!tickets.length) {
            container.textContent = "No tickets available.";
            return;
        }

        for (const ticket of tickets) {
            const column = document.createElement("div");
            column.className = "col-md-4";

            const card = document.createElement("div");
            card.className = "ticket-card";

            const title = document.createElement("h5");
            title.textContent = "Ticket #" + ticket.id;

            const event = document.createElement("p");
            event.textContent = "Event ID: " + ticket.event_id;

            const status = document.createElement("p");
            status.textContent = "Status: " + ticket.status;

            const qr = document.createElement("img");
            qr.alt = "Ticket QR code";
            qr.src = API + `/tickets/${ticket.id}/qr`;

            // QR image endpoint requires authentication.
            // Fetch it with the token and display it as a blob.
            try {
                const response = await fetch(qr.src, {
                    headers: { "Authorization": `Bearer ${token}` }
                });

                if (response.ok) {
                    const blob = await response.blob();
                    qr.src = URL.createObjectURL(blob);
                } else {
                    qr.alt = "Unable to load QR code";
                }
            } catch {
                qr.alt = "Unable to load QR code";
            }

            card.append(title, event, status, qr);
            column.appendChild(card);
            container.appendChild(column);
        }
    } catch (error) {
        showMessage(error.message, "danger");
    }
}

// MANUAL TICKET CHECK-IN
async function checkInTicket() {
    const qr_token = document.getElementById("qrToken").value.trim();
    const event_id = Number(document.getElementById("checkinEventId").value);

    if (!qr_token || !Number.isInteger(event_id) || event_id <= 0) {
        showCheckinMessage("Enter a valid QR token and event ID.", "danger");
        return;
    }

    await submitCheckin(qr_token, event_id);
}

async function submitCheckin(qr_token, event_id) {
    try {
        const result = await apiRequest("/tickets/check-in", {
            method: "POST",
            body: JSON.stringify({ qr_token, event_id })
        });

        showCheckinMessage(
            result.message || "Ticket checked in successfully!",
            "success"
        );

        document.getElementById("qrToken").value = "";
    } catch (error) {
        showCheckinMessage(error.message, "danger");
    }
}

function showCheckinMessage(message, type) {
    const element = document.getElementById("checkinMessage");
    element.textContent = message;
    element.className = `mt-3 text-${type}`;
}

// CAMERA QR SCANNER
function startScanner() {
    if (!token) {
        showCheckinMessage("Please log in as gate staff.", "danger");
        return;
    }

    if (typeof Html5Qrcode === "undefined") {
        showCheckinMessage("QR scanner library could not load.", "danger");
        return;
    }

    if (qrScanner) return;

    qrScanner = new Html5Qrcode("qr-reader");

    qrScanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 250, height: 250 } },
        decodedText => {
            let qrToken = decodedText;

            // Also accept a JSON QR payload if used later.
            try {
                const parsed = JSON.parse(decodedText);
                if (parsed.qr_token) qrToken = parsed.qr_token;
            } catch {}

            const eventId = Number(
                document.getElementById("checkinEventId").value
            );

            if (!Number.isInteger(eventId) || eventId <= 0) {
                showCheckinMessage(
                    "Enter the event ID before scanning.",
                    "warning"
                );
                return;
            }

            stopScanner();
            document.getElementById("qrToken").value = qrToken;
            submitCheckin(qrToken, eventId);
        },
        () => {}
    ).catch(error => {
        qrScanner = null;
        showCheckinMessage("Could not start camera: " + error, "danger");
    });
}

function stopScanner() {
    if (qrScanner) {
        const scanner = qrScanner;
        qrScanner = null;

        scanner.stop()
            .then(() => scanner.clear())
            .catch(() => {});
    }
}

// ADMIN STATISTICS
async function loadAdminStats() {
    try {
        const stats = await apiRequest("/admin/stats");

        const container = document.getElementById("statsList");
        container.replaceChildren();

        const cards = [
            ["Total Events", stats.total_events],
            ["Total Venues", stats.total_venues],
            ["Total Bookings", stats.total_bookings],
            ["Revenue", "Rs. " + stats.total_revenue],
            ["Check-ins", stats.total_checkins]
        ];

        cards.forEach(([label, value]) => {
            const column = document.createElement("div");
            column.className = "col-md-4";

            const card = document.createElement("div");
            card.className = "stat-card";

            const heading = document.createElement("h3");
            heading.textContent = value;

            const caption = document.createElement("p");
            caption.textContent = label;

            card.append(heading, caption);
            column.appendChild(card);
            container.appendChild(column);
        });
    } catch (error) {
        showMessage(error.message, "danger");
    }
}

// AGENT STATUS
async function loadAgentStatus() {
    try {
        const result = await apiRequest("/agents/status");

        const container = document.getElementById("agentStatus");
        container.replaceChildren();

        result.agents.forEach(agent => {
            const item = document.createElement("p");
            item.textContent = "✓ " + agent;
            container.appendChild(item);
        });
    } catch (error) {
        showMessage(error.message, "danger");
    }
}

// AGENT MESSAGE LOGS
async function loadAgentMessages() {
    try {
        const messages = await apiRequest("/agents/messages");

        const container = document.getElementById("agentMessages");
        container.replaceChildren();

        if (!messages.length) {
            container.textContent = "No agent messages recorded.";
            return;
        }

        messages.forEach(message => {
            const item = document.createElement("div");
            item.className = "border-bottom py-2";

            const details = document.createElement("p");
            details.textContent =
                `${message.sender} → ${message.receiver} | ${message.performative}`;

            const content = document.createElement("small");
            content.textContent = message.content || message.message_content || "";

            item.append(details, content);
            container.appendChild(item);
        });
    } catch (error) {
        showMessage(error.message, "danger");
    }
}

// INITIAL PAGE
if (token) {
    showSection("eventsSection");
} else {
    showSection("authSection");
}

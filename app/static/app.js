let token = localStorage.getItem("token");
let selectedTest = null;
let selectedCentre = null;

document.addEventListener("DOMContentLoaded", () => {
    loadCentres();

    if (token) {
        showLoggedIn();
        loadBookings();
    }
});


async function loadCentres() {
    const response = await fetch("/centres");
    const centres = await response.json();

    const container = document.getElementById("centres");
    container.innerHTML = "";

    for (const centre of centres) {
        const testsResponse = await fetch(`/centres/${centre.id}/tests`);
        const tests = await testsResponse.json();

        let testsHTML = "";

        tests.forEach(test => {
            testsHTML += `
                <div class="test">
                    <div>
                        <div class="test-name">${test.name}</div>
                        <div class="price">₹${test.price}</div>
                    </div>

                    <button class="primary-btn"
                        onclick='openBooking(${test.id}, "${test.name}", ${centre.id}, "${centre.name}")'>
                        Book
                    </button>
                </div>
            `;
        });

        container.innerHTML += `
            <div class="centre-card">
                <h3>${centre.name}</h3>
                <p class="location">${centre.location}</p>
                ${testsHTML}
            </div>
        `;
    }
}


function showLogin() {
    document.getElementById("authSection").classList.remove("hidden");
    document.getElementById("loginForm").classList.remove("hidden");
    document.getElementById("signupForm").classList.add("hidden");
}


function showSignup() {
    document.getElementById("authSection").classList.remove("hidden");
    document.getElementById("loginForm").classList.add("hidden");
    document.getElementById("signupForm").classList.remove("hidden");
}


async function signup() {
    const response = await fetch("/signup", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            name: document.getElementById("signupName").value,
            email: document.getElementById("signupEmail").value,
            password: document.getElementById("signupPassword").value
        })
    });

    const data = await response.json();

    document.getElementById("authMessage").textContent = data.message || data.error;

    if (response.ok) {
        showLogin();
    }
}


async function login() {
    const response = await fetch("/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            email: document.getElementById("loginEmail").value,
            password: document.getElementById("loginPassword").value
        })
    });

    const data = await response.json();

    if (!response.ok) {
        document.getElementById("authMessage").textContent = data.error;
        return;
    }

    token = data.access_token;
    localStorage.setItem("token", token);

    document.getElementById("authSection").classList.add("hidden");

    showLoggedIn();
    loadBookings();
}


function showLoggedIn() {
    document.getElementById("loginBtn").classList.add("hidden");
    document.getElementById("logoutBtn").classList.remove("hidden");
    document.getElementById("bookingsSection").classList.remove("hidden");
}


function logout() {
    token = null;
    localStorage.removeItem("token");

    document.getElementById("loginBtn").classList.remove("hidden");
    document.getElementById("logoutBtn").classList.add("hidden");
    document.getElementById("bookingsSection").classList.add("hidden");
}


function openBooking(testId, testName, centreId, centreName) {
    if (!token) {
        showLogin();
        document.getElementById("authMessage").textContent =
            "Please login before booking a test.";
        return;
    }

    selectedTest = testId;
    selectedCentre = centreId;

    document.getElementById("modalTestName").textContent = testName;
    document.getElementById("modalCentreName").textContent = centreName;

    document.getElementById("bookingModal").classList.remove("hidden");
}


function closeModal() {
    document.getElementById("bookingModal").classList.add("hidden");
}


async function createBooking() {
    const appointmentTime =
        document.getElementById("appointmentTime").value;

    if (!appointmentTime) {
        document.getElementById("bookingMessage").textContent =
            "Please select an appointment time.";
        return;
    }

    const response = await fetch("/bookings", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
            test_id: selectedTest,
            centre_id: selectedCentre,
            appointment_time: appointmentTime
        })
    });

    const data = await response.json();

    if (!response.ok) {
        document.getElementById("bookingMessage").textContent =
            data.error;
        return;
    }

    closeModal();
    loadBookings();
}


async function loadBookings() {
    if (!token) return;

    const response = await fetch("/bookings", {
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    if (!response.ok) return;

    const bookings = await response.json();
    const container = document.getElementById("bookings");

    container.innerHTML = "";

    if (bookings.length === 0) {
        container.innerHTML = `
            <div class="booking-card">
                <p>No bookings yet.</p>
            </div>
        `;
        return;
    }

    bookings.forEach(booking => {
    let action = "";

    if (booking.status === "PENDING") {
        action = `
            <button class="primary-btn"
                onclick="makePayment(${booking.id})">
                Pay ₹${booking.amount}
            </button>
        `;
    }

    container.innerHTML += `
        <div class="booking-card">
            <div class="booking-info">
                <strong>Booking #${booking.id}</strong>
                <p>Test ID: ${booking.test_id}</p>
                <p>Appointment: ${booking.appointment_time}</p>
                <p>Amount: ₹${booking.amount}</p>
            </div>

            <div>
                <span class="status">${booking.status}</span>
                ${action}
            </div>
        </div>
    `;
});
}
async function makePayment(bookingId) {
    const response = await fetch("/payments", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
            booking_id: bookingId,
            status: "SUCCESS"
        })
    });

    const data = await response.json();

    if (!response.ok) {
        alert(data.error);
        return;
    }

    alert("Payment successful!");
    loadBookings();
}
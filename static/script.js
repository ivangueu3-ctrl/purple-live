// ==============================================
// PURPLE LIVE — FULL SCRIPT
// ==============================================

// ===== GLOBAL VARIABLES =====
let currentCallId = null;
let callTimer = null;
let callSeconds = 0;
let isHostBusy = false;

// ===== SCREEN RECORDING & PROTECTION =====
function blockRecording() {
    // Prevent screenshot/recording detection
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            console.log('⚠️ Page hidden — recording may be active');
        }
    });
    // Disable right-click
    document.addEventListener('contextmenu', e => e.preventDefault());
    // Disable keyboard shortcuts
    document.addEventListener('keydown', e => {
        if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'p' || e.key === 'u' || e.key === 'S')) {
            e.preventDefault();
        }
        if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && e.key === 'I')) {
            e.preventDefault();
        }
    });
}
blockRecording();

// ===== PUBLIC CHAT =====
function sendPublicChat() {
    const input = document.getElementById('public-input');
    if (!input) return;
    const text = input.value.trim();
    if (!text) return;
    
    fetch('/send-public-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
    }).then(() => {
        input.value = '';
        refreshPublicChat();
    });
}

function refreshPublicChat() {
    fetch('/get-public-chat')
        .then(res => res.json())
        .then(data => {
            const area = document.getElementById('public-messages');
            if (!area) return;
            area.innerHTML = '';
            data.messages.forEach(m => {
                const div = document.createElement('div');
                div.className = 'chat-msg';
                div.innerHTML = `<strong>${m.sender}:</strong> ${m.message}`;
                area.appendChild(div);
            });
            area.scrollTop = area.scrollHeight;
        });
}
setInterval(refreshPublicChat, 2500);

// ===== PRIVATE CHAT =====
function sendPrivateMsg() {
    const input = document.getElementById('private-input');
    if (!input || !targetHostName) return;
    const text = input.value.trim();
    if (!text) return;
    
    fetch('/send-private-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ to_user: targetHostName, message: text })
    }).then(() => {
        input.value = '';
        refreshPrivateChat();
    });
}

function refreshPrivateChat() {
    if (!targetHostName) return;
    fetch(`/get-private-chat/${targetHostName}`)
        .then(res => res.json())
        .then(data => {
            const area = document.getElementById('private-messages');
            if (!area) return;
            area.innerHTML = '';
            data.messages.forEach(m => {
                const div = document.createElement('div');
                div.className = 'chat-msg';
                div.innerHTML = `<strong>${m.sender}:</strong> ${m.message}`;
                area.appendChild(div);
            });
            area.scrollTop = area.scrollHeight;
        });
}
setInterval(refreshPrivateChat, 3000);

// ===== GIFT SYSTEM =====
function sendGift(giftId, giftName, cost) {
    if (!targetHostName) {
        alert('🔍 First find and visit a host profile to send gifts!');
        return;
    }
    if (targetHostName === currentUser) {
        alert('❌ You cannot gift to yourself!');
        return;
    }
    
    fetch('/send-gift', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            gift_id: giftId,
            to_user: targetHostName
        })
    }).then(res => res.json())
    .then(data => {
        if (data.success) {
            updateCoinDisplay(data.new_coins);
            showGiftAnimation(data.gift);
        } else {
            alert(data.error || '❌ Failed to send gift');
        }
    });
}

function showGiftAnimation(gift) {
    const anim = document.createElement('div');
    anim.className = 'gift-animation';
    anim.innerHTML = `
        <span class="gift-emoji-large">${gift.emoji}</span>
        <span class="gift-name">${gift.name}</span>
    `;
    document.body.appendChild(anim);
    
    setTimeout(() => anim.classList.add('show'), 50);
    setTimeout(() => {
        anim.classList.remove('show');
        setTimeout(() => anim.remove(), 400);
    }, 2500);
}

function updateCoinDisplay(coins) {
    const el = document.getElementById('coin-count');
    if (el) el.textContent = coins;
}

// ===== DAILY TASKS =====
function claimTask(taskId) {
    fetch('/claim-task', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: taskId })
    }).then(res => res.json())
    .then(data => {
        if (data.success) {
            updateCoinDisplay(data.coins);
            alert('✅ Task claimed! Coins added!');
            location.reload();
        } else {
            alert(data.error || '❌ Cannot claim this task');
        }
    });
}

// ===== PK BATTLE =====
function startPK() {
    if (!isHost) {
        alert('⚠️ Only verified hosts can join PK battles!');
        return;
    }
    fetch('/start-pk', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                alert('⚔️ PK Battle started! Join to earn bonus coins!');
                location.reload();
            }
        });
}

// ===== HOST CALL RATE UPDATE =====
function updateRateDisplay(value) {
    const display = document.getElementById('rate-display');
    if (display) display.textContent = value;
}

function saveRate() {
    const slider = document.getElementById('rate-slider');
    if (!slider) return;
    
    fetch('/update-call-rates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ per_min: parseInt(slider.value) })
    }).then(res => res.json())
    .then(data => {
        if (data.success) {
            alert('✅ Call rate saved!');
        } else {
            alert(data.error || '❌ Rate not saved');
        }
    });
}

// ===== PRIVATE CALL — VIEWER SIDE =====
document.addEventListener('DOMContentLoaded', () => {
    const callBtn = document.getElementById('call-host-btn');
    if (callBtn) {
        callBtn.addEventListener('click', requestPrivateCall);
    }
    
    if (isHost) {
        checkIncomingCalls();
    }
});

function requestPrivateCall() {
    if (!targetHostId) {
        alert('❌ Host not found!');
        return;
    }
    
    const statusMsg = document.getElementById('call-status-msg');
    if (statusMsg) statusMsg.textContent = '📞 Requesting call...';
    
    fetch('/request-private-call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ host_id: targetHostId })
    }).then(res => res.json())
    .then(data => {
        if (data.success) {
            currentCallId = data.call_id;
            if (statusMsg) statusMsg.textContent = '✅ Call requested! Waiting host to accept...';
            monitorCallStatus();
        } else {
            if (data.error === 'host_busy') {
                if (statusMsg) statusMsg.textContent = '⚠️ Host is currently busy. Please try again later.';
            } else {
                if (statusMsg) statusMsg.textContent = '❌ ' + data.error;
            }
        }
    });
}

function monitorCallStatus() {
    if (!currentCallId) return;
    
    const checkInterval = setInterval(() => {
        fetch(`/check-call-status/${currentCallId}`)
            .then(res => res.json())
            .then(data => {
                if (!data.exists) {
                    clearInterval(checkInterval);
                    const statusMsg = document.getElementById('call-status-msg');
                    if (statusMsg) statusMsg.textContent = '❌ Call declined or ended';
                    return;
                }
                if (data.status === 'active') {
                    clearInterval(checkInterval);
                    startCallTimer();
                    const statusMsg = document.getElementById('call-status-msg');
                    if (statusMsg) statusMsg.textContent = '✅ Call connected! 📞';
                }
            });
    }, 1500);
}

function startCallTimer() {
    callSeconds = 0;
    callTimer = setInterval(() => {
        callSeconds++;
        const mins = Math.floor(callSeconds / 60);
        const secs = callSeconds % 60;
        console.log(`⏱️ Call time: ${mins}:${secs.toString().padStart(2, '0')}`);
    }, 1000);
}

function endCall() {
    if (callTimer) clearInterval(callTimer);
    if (currentCallId) {
        fetch('/end-private-call', { method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ call_id: currentCallId })
        });
    }
    currentCallId = null;
    callSeconds = 0;
    alert('📞 Call ended');
}

// ===== HOST — INCOMING CALL DETECTION =====
function checkIncomingCalls() {
    if (!isHost) return;
    
    setInterval(() => {
        fetch('/host-pending-calls')
            .then(res => res.json())
            .then(data => {
                const panel = document.getElementById('host-call-panel');
                if (!panel) return;
                
                if (data.calls.length > 0) {
                    panel.classList.remove('hidden');
                    const call = data.calls[0];
                    const nameEl = document.getElementById('caller-name');
                    if (nameEl) nameEl.textContent = `From: ${call.viewer}`;
                    
                    // Attach buttons
                    const acceptBtn = document.getElementById('accept-btn');
                    const declineBtn = document.getElementById('decline-btn');
                    
                    if (acceptBtn) {
                        acceptBtn.onclick = () => acceptCall(call.call_id);
                    }
                    if (declineBtn) {
                        declineBtn.onclick = () => declineCall(call.call_id);
                    }
                } else {
                    panel.classList.add('hidden');
                }
            });
    }, 2000);
}

function acceptCall(callId) {
    fetch('/accept-private-call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ call_id: callId })
    }).then(res => res.json())
    .then(data => {
        if (data.success) {
            alert('✅ Call connected! 📞');
            startCallTimer();
        }
    });
}

function declineCall(callId) {
    fetch('/decline-private-call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ call_id: callId })
    }).then(() => {
        console.log('Call declined');
    });
}

// ===== EXTRA: Add gift animation styles dynamically =====
const style = document.createElement('style');
style.textContent = `
.gift-animation {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) scale(0);
    z-index: 9999;
    text-align: center;
    pointer-events: none;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.gift-animation.show {
    transform: translate(-50%, -50%) scale(1);
}
.gift-emoji-large {
    font-size: 4rem;
    display: block;
    text-shadow: 0 0 20px rgba(255,215,0,0.8), 0 0 40px rgba(218,112,214,0.6);
    animation: sparkle 1s ease-in-out infinite alternate;
}
.gift-name {
    color: #FFD700;
    font-weight: bold;
    font-size: 1.3rem;
    margin-top: 10px;
    text-shadow: 0 0 10px rgba(0,0,0,0.8);
}
@keyframes sparkle {
    from { filter: brightness(1); }
    to { filter: brightness(1.4) drop-shadow(0 0 10px gold); }
}
`;
document.head.appendChild(style);
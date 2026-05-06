async function sendQuestion() {
    const input    = document.getElementById("userInput");
    const sendBtn  = document.getElementById("sendBtn");
    const question = input.value.trim();

    if (!question) return;

    addUserMessage(question);
    input.value = "";
    sendBtn.disabled    = true;
    sendBtn.textContent = "...";

    const loader = addLoadingMessage();

    try {
        // Get current user email from Firebase
        let userEmail = "";
        if (typeof firebase !== "undefined" && firebase.auth().currentUser) {
            userEmail = firebase.auth().currentUser.email;
        }

        const response = await fetch("/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                question: question,
                email: userEmail
            })
        });

        const data = await response.json();
        loader.remove();

        if (data.answer) {
            addBotMessage(data.answer, data.query_type);
        } else {
            addBotMessage("Error occurred. Please try again.", "error");
        }

    } catch (error) {
        loader.remove();
        addBotMessage("Connection error. Please try again.", "error");
    }

    sendBtn.disabled    = false;
    sendBtn.textContent = "Send ➤";
}


function addUserMessage(text) {
    const container = document.getElementById("chatContainer");
    const div       = document.createElement("div");
    div.className   = "user-message";
    div.textContent = "You: " + text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}


function addBotMessage(text, queryType) {
    const container = document.getElementById("chatContainer");
    const wrapper   = document.createElement("div");
    wrapper.className = "bot-wrapper";

    // Badge
    if (queryType && queryType !== "error") {
        const badge       = document.createElement("div");
        badge.className   = "query-badge";
        badge.textContent = getBadgeLabel(queryType);
        wrapper.appendChild(badge);
    }

    // Message box
    const div     = document.createElement("div");
    div.className = "bot-message";

    // Build formatted lines
    text.split("\n").forEach(function(line) {
        const p          = document.createElement("div");
        p.style.marginBottom = "4px";

        // ━━━ Divider
        if (line.includes("━━━")) {
            p.style.borderTop = "1px solid #0d4a3a";
            p.style.margin    = "10px 0";

        // ## or # Heading
       // ## or # Heading
        } else if (line.startsWith("##") || line.startsWith("#")) {
            p.textContent         = line.replace(/^#+\s*/, "");
            p.style.color         = "#f5c842";
            p.style.fontFamily    = "'Cinzel', serif";
            p.style.fontSize      = "18px";
            p.style.fontWeight    = "900";
            p.style.marginTop     = "14px";
            p.style.marginBottom  = "8px";
            p.style.borderBottom  = "2px solid rgba(245,200,66,0.3)";
            p.style.paddingBottom = "6px";
            p.style.letterSpacing = "1px";
            p.style.textTransform = "uppercase";

        // Bullet point
        } else if (line.startsWith("•") || line.startsWith("-")) {
            const cleanLine = line.replace(/^[•\-]\s*/, "");
            if (/[\u0600-\u06FF]/.test(cleanLine)) {
                p.textContent        = cleanLine;
                p.style.direction    = "rtl";
                p.style.textAlign    = "right";
                p.style.fontFamily   = "'Noto Nastaliq Urdu', serif";
                p.style.fontSize     = "15px";
                p.style.lineHeight   = "2.5";
                p.style.paddingRight = "12px";
                p.style.color        = "#f0e6d3";
                p.style.display      = "block";
                p.style.width        = "100%";
            } else {
                p.textContent       = "🔸 " + cleanLine;
                p.style.color       = "#f0e6d3";
                p.style.paddingLeft = "12px";
                p.style.fontSize    = "13.5px";
            }
            
        // Bismillah
        } else if (line.includes("Bismillah")) {
            p.textContent      = line;
            p.style.color      = "#f5c842";
            p.style.fontFamily = "'Cinzel', serif";
            p.style.fontSize   = "14px";
            p.style.fontWeight = "700";
            p.style.textAlign  = "center";
            p.style.margin     = "0 0 10px 0";

        // Emoji lines
        } else if (/^[📖📜🔹✅⚠️❓🎓🌍📝🕌🔗]/.test(line)) {
            p.style.color      = "#e8b84b";
            p.style.fontWeight = "700";
            p.style.fontSize   = "15px";
            p.style.marginTop  = "10px";

            // ⭐ Make Sunnah.com and Quran.com links clickable
            if (line.includes("sunnah.com") || line.includes("quran.com")) {
                const parts  = line.split("https://");
                const label  = document.createTextNode(parts[0]);
                p.appendChild(label);

                const link            = document.createElement("a");
                link.href             = "https://" + parts[1].trim();
                link.textContent      = "https://" + parts[1].trim();
                link.target           = "_blank";
                link.style.color      = "#f5c842";
                link.style.textDecoration = "underline";
                link.style.cursor     = "pointer";
                p.appendChild(link);
            } else {
                p.textContent = line;
            }

            if (/[\u0600-\u06FF]/.test(line)) {
                p.style.direction  = "rtl";
                p.style.textAlign  = "right";
                p.style.fontFamily = "'Noto Nastaliq Urdu', serif";
                p.style.fontSize   = "15px";
                p.style.lineHeight = "2.5";
            }

        // Summary / Note labels
       } else if (
            line.includes("✅ SUMMARY") ||
            line.includes("✅ خلاصہ") ||
            line.includes("⚠️ NOTE") ||
            line.includes("⚠️ نوٹ")
        ) {
            p.textContent      = line.replace(/^\.*/, "").trim();
            p.style.color      = "#f5c842";
            p.style.fontWeight = "700";
            p.style.fontSize   = "14px";
            p.style.marginTop  = "8px";

            // Remove dot if present
            p.textContent      = line.replace(/^\.*/, "").trim();
            p.style.color      = "#f5c842";
            p.style.fontWeight = "700";
            p.style.fontSize   = "14px";
            p.style.marginTop  = "8px";
            // If Urdu text
            if (/[\u0600-\u06FF]/.test(line)) {
                p.style.direction  = "rtl";
                p.style.textAlign  = "right";
                p.style.fontFamily = "'Noto Nastaliq Urdu', serif";
                p.style.lineHeight = "2.5";
            }

        // Normal text
        } else {
            // Sunnah.com and Quran.com link in normal text
           if (line.includes("sunnah.com") || line.includes("quran.com")) {
                line = line.replace(/__/g, "").replace(/\*/g, "").trim();
                const parts  = line.split("https://");
                const label  = document.createTextNode(parts[0]);
                p.appendChild(label);
                
                const link            = document.createElement("a");
                link.href             = "https://" + parts[1].trim();
                link.textContent      = "🔗 " + "https://" + parts[1].trim();
                link.target           = "_blank";
                link.style.color      = "#f5c842";
                link.style.textDecoration = "underline";
                link.style.cursor     = "pointer";
                link.style.display    = "block";
                link.style.marginTop  = "4px";
                p.appendChild(link);

            // Urdu/Arabic text
            } else if (/[\u0600-\u06FF]/.test(line)) {
                p.textContent        = line;
                p.style.direction    = "rtl";
                p.style.textAlign    = "right";
                p.style.fontFamily   = "'Noto Nastaliq Urdu', serif";
                p.style.fontSize     = "15px";
                p.style.lineHeight   = "2.5";
                p.style.color        = "#e8d5b8";

            // Normal English text
            } else {
                p.textContent    = line;
                p.style.color    = "#e8d5b8";
                p.style.fontSize = "13.5px";
            }
        }

        div.appendChild(p);
    });

    wrapper.appendChild(div);
    container.appendChild(wrapper);
    container.scrollTop = container.scrollHeight;
}


function addLoadingMessage() {
    const container = document.getElementById("chatContainer");
    const div       = document.createElement("div");
    div.className   = "loading-message";
    div.textContent = "🤔 We are working on your Query...";
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
}


function getBadgeLabel(queryType) {
    const labels = {
        "tafsir"      : "📖 Tafsir",
        "urdu_tafsir" : "📖 Urdu Tafsir",
        "hadith"      : "📜 Hadith",
        "tarjuma"     : "🌍 Tarjuma",
        "notes"       : "📝 Study Notes",
        "islamic_qa"  : "❓ Islamic Q&A",
        "general"     : "🎓 Islamic Studies",
        "not_islamic" : "⚠️ Out of Scope"
    };
    return labels[queryType] || "🕌 Islamic Mentor";
}


function handleKeyPress(event) {
    if (event.key === "Enter") sendQuestion();
}
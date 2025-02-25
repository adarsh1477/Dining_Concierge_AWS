var checkout = {};

$(document).ready(function () {
    var $messages = $(".messages-content"),
        d,
        h,
        m,
        i = 0;

    $(window).on("load", function () {
        $messages.mCustomScrollbar();
        insertResponseMessage("Hi there, I'm your personal Concierge. How can I help?");
    });

    function updateScrollbar() {
        $messages
            .mCustomScrollbar("update")
            .mCustomScrollbar("scrollTo", "bottom", {
                scrollInertia: 10,
                timeout: 0,
            });
    }

    function setDate() {
        d = new Date();
        if (m != d.getMinutes()) {
            m = d.getMinutes();
            $('<div class="timestamp">' + d.getHours() + ":" + m + "</div>").appendTo(
                $(".message:last")
            );
        }
    }

    function callChatbotApi(message) {
        console.log("📡 Sending message to API:", message);

        return fetch("https://ie8xv4u366.execute-api.us-east-1.amazonaws.com/prod/chatbot", {
            method: "POST", 
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: message }) 
        })
        .then(response => {
            console.log("🔄 Raw API Response:", response);
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json(); 
        })
        .then(data => {
            console.log("✅ Parsed API Response:", data);

            // If 'body' is a string, parse it again
            if (typeof data.body === "string") {
                try {
                    data.body = JSON.parse(data.body);
                } catch (error) {
                    console.error("❌ Failed to parse API response body:", error);
                }
            }

            return data;
        })
        .catch(error => {
            console.error("❌ API Error:", error);
            return { message: "Error connecting to chatbot. Please try again." };
        });
    }

    function insertMessage() {
        var msg = $(".message-input").val().trim();
        if (msg === "") {
            return false;
        }

        $('<div class="message message-personal">' + msg + "</div>")
            .appendTo($(".mCSB_container"))
            .addClass("new");

        setDate();
        $(".message-input").val(null);
        updateScrollbar();

        callChatbotApi(msg).then((data) => {
            console.log("🟢 Received API Data in insertMessage:", data);

            let chatbotResponse = data.body?.message || data.message || "Oops, something went wrong.";

            insertResponseMessage(chatbotResponse);
        });
    }

    $(".message-submit").click(function () {
        insertMessage();
    });

    $(window).on("keydown", function (e) {
        if (e.which == 13) {
            insertMessage();
            return false;
        }
    });

    function insertResponseMessage(content) {
        $(`
            <div class="message loading new">
                <figure class="avatar"><img src="https://media.tenor.com/images/4c347ea7198af12fd0a66790515f958f/tenor.gif" /></figure>
                <span></span>
            </div>
        `).appendTo($(".mCSB_container"));
        updateScrollbar();

        setTimeout(function () {
            $(".message.loading").remove();
            $(`
                <div class="message new">
                    <figure class="avatar"><img src="https://media.tenor.com/images/4c347ea7198af12fd0a66790515f958f/tenor.gif" /></figure>
                    ${content}
                </div>
            `).appendTo($(".mCSB_container")).addClass("new");
            setDate();
            updateScrollbar();
            i++;
        }, 500);
    }
});

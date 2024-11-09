// Simulate sending a message and receiving a response from the assistant
function press(e) {
  if (e.keyCode === 13 && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function sendMessage() {
  const userInput = document.getElementById("userInput");
  const chatDisplay = document.getElementById("chatDisplay");
  const userMessage = userInput.value.trim();

  if (userMessage === "") return;

  // Display the user's message
  const userMessageElement = document.createElement("div");
  userMessageElement.classList.add("message", "user-message");
  userMessageElement.textContent = userMessage;
  chatDisplay.appendChild(userMessageElement);
  userInput.value = ""; // Clear input

  // Simulate sending the question to the assistant and getting a response
  fetchAssistantResponse(userMessage);
}

// Function to simulate fetching a response from the assistant
async function fetchAssistantResponse(question) {
  const chatDisplay = document.getElementById("chatDisplay");
  const response = await fetch("http://127.0.0.1:8000/onomi", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
    },
    body: JSON.stringify({
      question: question,
      id_employee: "1001",
      compania: "1",
      database: "123",
      thread_id: "",
    }),
  });

  const data = await response.json();
  let assistantResponse = "";
  if (typeof data.response === "object") {
    assistantResponse = data.response["assistant"];
  } else {
    assistantResponse = data.response || data.Error;
  }

  // Display the assistant's response
  const assistantMessageElement = document.createElement("div");
  assistantMessageElement.classList.add("message", "assistant-message");
  assistantMessageElement.innerText = assistantResponse;
  chatDisplay.appendChild(assistantMessageElement);

  // Scroll to the bottom of the chat display
  chatDisplay.scrollTop = chatDisplay.scrollHeight;
}

$('#btn-nav').on("change", function (){
  if ($("#btn-nav").is(":checked")){
    $(".chat-container").css('margin-left','14%');
  }else{
    $(".chat-container").css('margin-left','');
  }
});
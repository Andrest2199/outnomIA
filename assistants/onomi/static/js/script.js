document.getElementById('btn-nav').checked = false;

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
  const thread_id = document.getElementById("threadId").value;

  if (userMessage === "") return;

  // Display the user's message
  const userMessageElement = document.createElement("div");
  userMessageElement.classList.add("message", "user-message");
  userMessageElement.innerText = userMessage;
  chatDisplay.appendChild(userMessageElement);
  userInput.value = "";
  // Create and show spinner
  const spinnerElement = createSpinner();
  chatDisplay.appendChild(spinnerElement);
  $("#spinner").show();
  // Scroll to the bottom of the chat display
  chatDisplay.scrollTop = chatDisplay.scrollHeight;
  // Send the question to the assistant and getting a response
  setTimeout(() => fetchAssistantResponse(userMessage,thread_id), 500);
}

// Function to simulate fetching a response from the assistant
async function fetchAssistantResponse(question,thread_id="") {
  const chatDisplay = document.getElementById("chatDisplay");
  const response = await fetch("http://3.82.204.90:80/onomi", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
    },
    body: JSON.stringify({
      question: question,
      id_employee: "095393",
      compania: "1",
      database: "FROM FRONT 123",
      thread_id: thread_id,
    }),
  });

  const data = await response.json();
  let assistantResponse = "";
  if (typeof data.response === "object") {
    assistantResponse = data.response["assistant"];
    const threadElement = document.getElementById("threadId");
    if (threadElement.value == "" || threadElement.value == null )
      threadElement.value = data.thread_id;
  } else {
    assistantResponse = data.response || data.Error;
    const threadElement = document.getElementById("threadId");
    if (threadElement.value == "" || threadElement.value == null )
      threadElement.value = data.thread_id || "";
  }
  // Display the assistant's response
  const assistantMessageElement = document.createElement("div");
  assistantMessageElement.classList.add("message", "assistant-message");
  assistantMessageElement.innerText = assistantResponse;
  chatDisplay.appendChild(assistantMessageElement);
  // Add spinner to the end of chat
  const spinnerElement = createSpinner();
  chatDisplay.appendChild(spinnerElement);
  // Scroll to the bottom of the chat display
  chatDisplay.scrollTop = chatDisplay.scrollHeight;
}

async function loadMessages(thread_id) {
  $('#spinnerBody').css("display","flex");
  let optionsMenu = document.querySelectorAll(`a[onclick]`);
  optionsMenu.forEach(element => {
      element.parentElement.style.background = '';
  });
  $(`#${thread_id}`).parent().css("background","rgba(255,0,0,0.5)");
  try {
      const response = await fetch(`http://3.82.204.90:80/retrieve_messages?thread_id=${thread_id}`, {
          method: "GET",
          headers: {
              "Content-Type": "application/json"
          }
      });
      
      const data = await response.json();
      if (data.message === "Success") {
          displayMessages(data.response,thread_id);
      } else {
          console.error("Error fetching messages:", data.Error);
      }
  } catch (error) {
      console.error("Request failed:", error);
  }
}

function displayMessages(messages,thread_id) {
  const chatDisplay = document.getElementById("chatDisplay");
  chatDisplay.innerHTML = '';
  // Obtén los índices en orden inverso y recorre los mensajes de atrás hacia adelante
  Object.keys(messages)
    .reverse()
    .forEach(index => {
      const message = messages[index];
      const role = Object.keys(message)[0];
      const content = message[role];
      
      const messageElement = document.createElement("div");
      messageElement.classList.add("message", `${role}-message`);
      messageElement.innerText = content;
      
      chatDisplay.appendChild(messageElement);
  });
  // Add spinner to the end of ch
  const spinnerElement = createSpinner();
  chatDisplay.appendChild(spinnerElement);
  // Add thread id to the chat
  const threadElement = document.getElementById("threadId");
  threadElement.value = thread_id;
  // Hacer scroll hacia abajo para ver el mensaje
  chatDisplay.scrollTop = chatDisplay.scrollHeight;
  // Ocultar spinnerBody
  $('#spinnerBody').css("display","none");
}

function createSpinner() {
  let spinnerElement = document.getElementById("spinner");
  
  if (spinnerElement) {
    $("#spinner").remove();
  }

  spinnerElement = document.createElement("div");
  spinnerElement.id = "spinner";
  spinnerElement.classList.add("message", "assistant-message");
  spinnerElement.hidden = true;

  const spinnerInner = document.createElement("div");
  spinnerInner.classList.add("spinner");
  spinnerElement.appendChild(spinnerInner);

  return spinnerElement;
}

function newThread(){
  let optionsMenu = document.querySelectorAll(`a[onclick]`);
  optionsMenu.forEach(element => {
      element.parentElement.style.background = '';
  });
  $('#newThread').parent().css("background","rgba(255,0,0,0.5)");
  const chatDisplay = document.getElementById("chatDisplay");
  chatDisplay.innerHTML = '';
  const threadElement = document.getElementById("threadId");
  threadElement.value = "";
}

$('#btn-nav').on("change", function (){
  if ($("#btn-nav").is(":checked")){
    $(".chat-container").css('margin-left','14%');
  }else{
    $(".chat-container").css('margin-left','');
  }
});

// static/js/users/register.js

document.addEventListener("DOMContentLoaded", () => {
  const usernameInput = document.getElementById(username_field_id);
  if (!usernameInput) return;

  // Create feedback element right after the input
  const feedback = document.createElement("div");
  feedback.classList.add("invalid-feedback"); // default
  usernameInput.parentNode.appendChild(feedback);

  let debounceTimer;

  const checkUsername = async (username) => {
    try {
      const response = await fetch(
        `/users/check-username/?username=${encodeURIComponent(username)}`
      );
      const data = await response.json();

      if (data.available) {
        usernameInput.classList.remove("is-invalid");
        usernameInput.classList.add("is-valid");
        feedback.textContent = data.message;
        feedback.classList.remove("invalid-feedback");
        feedback.classList.add("valid-feedback");
      } else {
        usernameInput.classList.remove("is-valid");
        usernameInput.classList.add("is-invalid");
        feedback.textContent = data.message;
        feedback.classList.remove("valid-feedback");
        feedback.classList.add("invalid-feedback");
      }
    } catch (err) {
      usernameInput.classList.remove("is-valid");
      usernameInput.classList.add("is-invalid");
      feedback.textContent = "Could not validate username. Try again.";
      feedback.classList.remove("valid-feedback");
      feedback.classList.add("invalid-feedback");
    }
  };

  usernameInput.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    const username = usernameInput.value.trim();

    if (!username) {
      usernameInput.classList.remove("is-valid", "is-invalid");
      feedback.textContent = "";
      return;
    }

    debounceTimer = setTimeout(() => {
      checkUsername(username);
    }, 400);
  });
});

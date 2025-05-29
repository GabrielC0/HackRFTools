document.addEventListener("DOMContentLoaded", () => {
  // State management
  const state = {
    selectedChannel: "",
    loopMode: false,
    isConnected: true,
    commandHistory: [],
    monetaryValue: 0.5,
    lastCommand: "",
  };

  // DOM Elements
  const channelSelect = document.getElementById("channelSelect");
  const channelInfo = document.getElementById("channelInfo");
  const selectedChannelDisplay = document.getElementById(
    "selectedChannelDisplay"
  );
  const buttonGrid = document.getElementById("buttonGrid");
  const noChannelMessage = document.getElementById("noChannelMessage");
  const loopMode = document.getElementById("loopMode");
  const toast = document.getElementById("toast");
  const toastMessage = document.getElementById("toastMessage");
  const analyticsModal = document.getElementById("analyticsModal");
  const settingsModal = document.getElementById("settingsModal");
  const shutdownModal = document.getElementById("shutdownModal");
  const totalCommands = document.getElementById("totalCommands");
  const totalEarnings = document.getElementById("totalEarnings");
  const monetaryValueInput = document.getElementById("monetaryValue");

  // Initialize channels
  const channels = Array.from({ length: 13 }, (_, i) => (i + 1).toString());
  channels.forEach((channel) => {
    const option = document.createElement("option");
    option.value = channel;
    option.textContent = channel.padStart(2, "0");
    channelSelect.appendChild(option);
  });

  // Initialize buttons
  const buttons = ["A", "B", "C", "D", "E", "F", "G", "H"];
  buttons.forEach((button) => {
    const btn = document.createElement("button");
    btn.className = "control-button";
    btn.textContent = button;
    btn.onclick = () => handleButtonClick(button);
    buttonGrid.appendChild(btn);
  });

  // Channel selection handler
  channelSelect.addEventListener("change", (e) => {
    state.selectedChannel = e.target.value;
    if (state.selectedChannel) {
      channelInfo.style.display = "block";
      buttonGrid.style.display = "grid";
      noChannelMessage.style.display = "none";
      selectedChannelDisplay.textContent = `CH_${state.selectedChannel.padStart(
        2,
        "0"
      )}`;
    } else {
      channelInfo.style.display = "none";
      buttonGrid.style.display = "none";
      noChannelMessage.style.display = "block";
    }
  });

  // Loop mode handler
  loopMode.addEventListener("change", (e) => {
    state.loopMode = e.target.checked;
    document.getElementById("loopIndicator").style.display = state.loopMode
      ? "block"
      : "none";
  });

  // Button click handler
  async function handleButtonClick(button) {
    const command = `Canal ${state.selectedChannel} - Bouton ${button}`;
    const newCommand = {
      timestamp: new Date(),
      command,
      value: state.monetaryValue,
    };

    state.commandHistory.push(newCommand);
    state.lastCommand = command;

    console.log(`Envoi commande: ${command}`);

    if (state.loopMode) {
      setTimeout(() => {
        console.log(`Envoi commande (Loop 1): ${command}`);
      }, 0);

      setTimeout(() => {
        const loopCommand = {
          timestamp: new Date(),
          command: `${command} (Loop)`,
          value: state.monetaryValue,
        };
        state.commandHistory.push(loopCommand);
        console.log(`Envoi commande (Loop 2): ${command}`);
        updateAnalytics();
      }, 1000);
    }

    showToast();
    updateAnalytics();
  }

  // Toast notification
  function showToast() {
    toastMessage.textContent =
      state.lastCommand + (state.loopMode ? " [Loop Enabled]" : "");
    toast.style.display = "block";
    setTimeout(() => {
      toast.style.display = "none";
    }, 3000);
  }

  // Analytics
  function updateAnalytics() {
    totalCommands.textContent = state.commandHistory.length
      .toString()
      .padStart(6, "0");
    const earnings = state.commandHistory
      .reduce((total, cmd) => total + cmd.value, 0)
      .toFixed(2);
    totalEarnings.textContent = `${earnings} EUR`;
  }

  // Modal handlers
  document.getElementById("analyticsButton").onclick = () =>
    (analyticsModal.style.display = "block");
  document.getElementById("settingsButton").onclick = () =>
    (settingsModal.style.display = "block");

  // Shutdown handler
  document.getElementById("shutdownButton").onclick = () => {
    settingsModal.style.display = "none";
    shutdownModal.style.display = "block";
    console.log("Arrêt du Raspberry Pi...");
    setTimeout(() => {
      shutdownModal.style.display = "none";
    }, 4000);
  };

  // Monetary value handler
  monetaryValueInput.addEventListener("change", (e) => {
    state.monetaryValue = Number.parseFloat(e.target.value) || 0;
  });

  // Close modals when clicking outside
  window.onclick = (event) => {
    if (event.target.classList.contains("modal")) {
      event.target.style.display = "none";
    }
  };
});

const { app, BrowserWindow } = require("electron");
const path = require("path");

const isDev = process.env.NODE_ENV === "development";

function createWindow() {
  // Créer la fenêtre du navigateur
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true,
    },
  });

  // Charger l'URL appropriée
  const startUrl = isDev
      ? "http://localhost:3000"
      : `file://${path.join(__dirname, "react-app/build/index.html")}`;

  mainWindow.loadURL(startUrl);

  // Ouvrir les DevTools en mode développement
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  // Gérer la fermeture de la fenêtre
  mainWindow.on('closed', function () {
    mainWindow = null;
  });
}

// Quand l'application est prête
app.whenReady().then(createWindow);

// Gérer l'activation de l'application (macOS)
app.on("activate", function () {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

// Quitter quand toutes les fenêtres sont fermées
app.on("window-all-closed", function () {
  if (process.platform !== "darwin") app.quit();
});
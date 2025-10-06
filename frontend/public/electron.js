const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");

let win;

function createWindow() {
  win = new BrowserWindow({
    width: 350,
    height: 400,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"), 
    },
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    resizable: false,
    movable: true,
  });

  win.loadURL("http://localhost:3000");
}

ipcMain.on("resize-window", (event, width, height) => {
  if (win) {
    const bounds = win.getBounds();
    win.setBounds({
      x: bounds.x,
      y: bounds.y,
      width,
      height,
    });
  }
});

app.whenReady().then(createWindow);
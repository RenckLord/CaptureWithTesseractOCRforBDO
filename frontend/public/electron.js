const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
  const win = new BrowserWindow({
    width: 350,       // Ancho 
    height: 250,      // Alto 
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
    transparent: true, 
    frame: false,      
    alwaysOnTop: true, 
    resizable: false,
    movable: true,
    skipTaskbar: true, 
  });
  
  //win.setIgnoreMouseEvents(true);

  // Carga la aplicación de React
const startUrl = 'http://localhost:3000';
  win.loadURL(startUrl);
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
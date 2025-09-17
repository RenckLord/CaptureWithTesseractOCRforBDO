// frontend/public/electron.js
const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
  // Configuración de la ventana del overlay
  const win = new BrowserWindow({
    width: 350,       // Ancho del overlay
    height: 150,      // Alto del overlay
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
    transparent: true, // Habilita la transparencia
    frame: false,      // Oculta la barra de título y bordes
    alwaysOnTop: true, // Mantiene la ventana siempre visible
    resizable: false,
    movable: true,
    skipTaskbar: true, // No la muestra en la barra de tareas de Windows
  });
  
  // Hace que los clics "atraviesen" la ventana, para que puedas seguir jugando
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
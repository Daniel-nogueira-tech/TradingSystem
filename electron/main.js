const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('node:path');

function createWindow() {
    const indexPath = path.join(__dirname, '..', 'dist', 'index.html');


    const iconPath = process.platform === 'darwin'
    ? path.resolve(__dirname, '..', 'dist', 'favicon.icns')
    : path.resolve(__dirname, '..', 'dist', 'favicon.ico');

    const win = new BrowserWindow({
        width: 1920,
        height: 1080,
        icon:iconPath, // Favicon from dist
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
        },
    });
   // load de desenvolvimento
    win.loadURL('http://localhost:5173')

    // Load the production build
   /* win.loadFile(indexPath).catch((err) => {
        console.error('Failed to load index.html:', err);
    });*/
}


app.whenReady().then(() => {
    ipcMain.handle('ping', () => 'pong');
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});
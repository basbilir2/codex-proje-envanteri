const {app,BrowserWindow,shell,dialog}=require('electron');
const path=require('node:path');
const fs=require('node:fs');

app.setName('Elmas Apartmanı');
const appDataRoot=app.getPath('appData'),dataPath=path.join(appDataRoot,'Elmas Apartmanı'),legacyDataPath=path.join(appDataRoot,'elmas-apartmani-masaustu');
if(!fs.existsSync(dataPath)&&fs.existsSync(legacyDataPath))fs.cpSync(legacyDataPath,dataPath,{recursive:true});
app.setPath('userData',dataPath);

if(!app.requestSingleInstanceLock())app.quit();
let mainWindow,desktopServer;

async function createWindow(){
 const {startDesktopServer}=await import('./server.mjs');
 const initial=app.isPackaged?path.join(process.resourcesPath,'initial-data.json'):path.join(__dirname,'initial-data.json');
 const syncConfig={webAppUrl:'https://script.google.com/macros/s/AKfycbzjPFOPUV6yWInedQrkE_j4W7MG7NWPC8QAnXjd6j3PezP6bOLn9v_KLvdgqHi1BGU9Qg/exec',secret:process.env.ELMAS_SYNC_SECRET||'PRIVATE_VALUE_004'};
 desktopServer=await startDesktopServer({dataDir:app.getPath('userData'),initialData:initial,syncConfig});
 mainWindow=new BrowserWindow({width:1440,height:920,minWidth:980,minHeight:680,show:false,backgroundColor:'#f5f7f3',autoHideMenuBar:true,webPreferences:{contextIsolation:true,nodeIntegration:false,sandbox:true}});
 mainWindow.webContents.setWindowOpenHandler(({url})=>{if(/^https?:/.test(url))shell.openExternal(url);return {action:'deny'};});
 mainWindow.webContents.on('will-navigate',(event,url)=>{if(!url.startsWith(desktopServer.url)){event.preventDefault();if(/^https?:/.test(url))shell.openExternal(url);}});
 await mainWindow.loadURL(desktopServer.url);
 fs.writeFileSync(path.join(dataPath,'baslatma-durumu.json'),JSON.stringify({ok:true,at:new Date().toISOString(),url:desktopServer.url}));
 mainWindow.show();
}
app.whenReady().then(createWindow).catch(error=>{console.error(error&&error.stack||error);try{fs.writeFileSync(path.join(dataPath,'baslatma-durumu.json'),JSON.stringify({ok:false,at:new Date().toISOString(),error:String(error&&error.stack||error)}));}catch{}dialog.showErrorBox('Elmas Apartmanı',error.message);app.quit();});
app.on('second-instance',()=>{if(mainWindow){if(mainWindow.isMinimized())mainWindow.restore();mainWindow.focus();}});
app.on('window-all-closed',()=>{if(process.platform!=='darwin')app.quit();});
app.on('before-quit',()=>{desktopServer?.close();});

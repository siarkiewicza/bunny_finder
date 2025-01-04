const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('path')
const fs = require('fs').promises
const fetch = require('node-fetch')
const FormData = require('form-data')
const isDev = process.env.NODE_ENV === "development"

// Constants for batch processing
const BATCH_SIZE = 20  // Reduced batch size for better memory management
const SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png']
const API_URL = 'http://127.0.0.1:5001/detect-batch'

async function createWindow() {
    const win = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    })

    if (isDev) {
        win.loadURL('http://localhost:3001')
        win.webContents.openDevTools()
    } else {
        win.loadFile(path.join(__dirname, '../dist/index.html'))
    }

    return win
}

async function getAllImageFiles(dirPath) {
    const files = []
    
    async function scanDir(currentPath) {
        try {
            const entries = await fs.readdir(currentPath, { withFileTypes: true })
            
            for (const entry of entries) {
                const fullPath = path.join(currentPath, entry.name)
                
                if (entry.isDirectory()) {
                    await scanDir(fullPath)
                } else if (entry.isFile()) {
                    const ext = path.extname(entry.name).toLowerCase()
                    if (SUPPORTED_FORMATS.includes(ext)) {
                        console.log(`Found image: ${fullPath}`)
                        files.push(fullPath)
                    }
                }
            }
        } catch (error) {
            console.error(`Error scanning directory ${currentPath}:`, error)
        }
    }
    
    await scanDir(dirPath)
    console.log(`Total images found: ${files.length}`)
    return files
}

async function processBatch(win, files, startIdx, outputPath) {
    const endIdx = Math.min(startIdx + BATCH_SIZE, files.length)
    const batch = files.slice(startIdx, endIdx)
    let bunniesFound = 0
    
    try {
        console.log(`Processing batch: ${startIdx} to ${endIdx} of ${files.length}`)
        console.log('API URL:', API_URL)
        console.log('Batch size:', batch.length)
        
        // Create form data with batch of images
        const formData = new FormData()
        for (const file of batch) {
            const fileData = await fs.readFile(file)
            formData.append('images', fileData, path.basename(file))
            console.log(`Added to batch: ${file}`)
        }

        console.log('Sending batch to server...')
        const response = await fetch(API_URL, {
            method: 'POST',
            body: formData,
            headers: {
                'Accept': 'application/json'
            }
        }).catch(error => {
            console.error('Fetch error details:', {
                message: error.message,
                type: error.type,
                code: error.code,
                stack: error.stack
            });
            throw error;
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Server error response:', errorText);
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
        }

        const results = await response.json()
        console.log('Server response:', results)
        
        // Process results and copy bunny images
        if (results.success) {
            for (let i = 0; i < results.results.length; i++) {
                const result = results.results[i]
                if (result.has_bunny) {
                    const sourceFile = batch[i]
                    const fileName = path.basename(sourceFile)
                    const outputFilePath = path.join(outputPath, fileName)
                    await fs.copyFile(sourceFile, outputFilePath)
                    bunniesFound++
                    console.log(`Copied bunny image: ${fileName} (confidence: ${result.detections[0]?.confidence})`)
                } else {
                    console.log(`No bunny detected in: ${path.basename(batch[i])}`)
                }
            }
        }

        // Send progress update
        win.webContents.send('scan-progress', {
            processed: endIdx,
            total: files.length,
            bunniesFound: bunniesFound
        })

        // Process next batch if there are more files
        if (endIdx < files.length) {
            await new Promise(resolve => setTimeout(resolve, 100))
            const nextBatchBunnies = await processBatch(win, files, endIdx, outputPath)
            bunniesFound += nextBatchBunnies
        }

    } catch (error) {
        console.error('Error processing batch:', error)
        win.webContents.send('scan-error', {
            message: `Error processing batch: ${error.message}`
        })
    }

    return bunniesFound
}

app.whenReady().then(async () => {
    const mainWindow = await createWindow()

    ipcMain.handle('process-folder', async (event, { inputPath, outputPath, sensitivity }) => {
        try {
            console.log(`Starting folder processing:`)
            console.log(`Input: ${inputPath}`)
            console.log(`Output: ${outputPath}`)
            console.log(`Sensitivity: ${sensitivity}`)

            // Get all image files recursively
            const files = await getAllImageFiles(inputPath)
            
            if (files.length === 0) {
                console.log('No image files found')
                return {
                    success: false,
                    error: 'No image files found in the selected folder'
                }
            }

            // Initialize progress
            mainWindow.webContents.send('scan-progress', {
                processed: 0,
                total: files.length,
                bunniesFound: 0
            })

            // Process files in batches
            console.log(`Starting batch processing of ${files.length} files`)
            const bunniesFound = await processBatch(mainWindow, files, 0, outputPath)
            console.log(`Processing complete. Found ${bunniesFound} bunnies`)

            return {
                success: true,
                bunniesFound: bunniesFound,
                totalProcessed: files.length
            }

        } catch (error) {
            console.error('Error processing folder:', error)
            return {
                success: false,
                error: error.message
            }
        }
    })
})

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit()
    }
})

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow()
    }
})
import React, { useState } from 'react'
import './styles.css'
import bunnyImage from './images/bunny-shot-crop.jpg'
const { ipcRenderer } = window.require('electron')

if (process.env.NODE_ENV === 'development') {
  const { install } = require('electron-react-devtools');
  install();
}

function App() {
    const [isDragging, setIsDragging] = useState(false)
    const [inputPath, setInputPath] = useState('')
    const [outputPath, setOutputPath] = useState('')
    const [sensitivity, setSensitivity] = useState('medium')
    const [isScanning, setIsScanning] = useState(false)
    const [scanProgress, setScanProgress] = useState({
        processed: 0,
        total: 0,
        bunniesFound: 0,
        percentage: 0
    })
    const [statusMessage, setStatusMessage] = useState('')

    const handleDragOver = (e) => {
        e.preventDefault()
        setIsDragging(true)
    }

    const handleDragLeave = () => {
        setIsDragging(false)
    }

    const handleDrop = (e) => {
        e.preventDefault()
        setIsDragging(false)

        const items = e.dataTransfer.items
        if (items) {
            for (let i = 0; i < items.length; i++) {
                const item = items[i]
                if (item.kind === 'file') {
                    const entry = item.webkitGetAsEntry()
                    if (entry.isDirectory) {
                        setInputPath(e.dataTransfer.files[i].path)
                        break
                    }
                }
            }
        }
    }

    const handleDestinationDrop = (e) => {
        e.preventDefault()
        const items = e.dataTransfer.items
        if (items) {
            for (let i = 0; i < items.length; i++) {
                const item = items[i]
                if (item.kind === 'file') {
                    const entry = item.webkitGetAsEntry()
                    if (entry.isDirectory) {
                        setOutputPath(e.dataTransfer.files[i].path)
                        break
                    }
                }
            }
        }
    }

    const handleReset = () => {
        setInputPath('')
        setOutputPath('')
        setScanProgress({
            processed: 0,
            total: 0,
            bunniesFound: 0,
            percentage: 0
        })
        setStatusMessage('')
    }

    const handleStartScan = async () => {
        if (!inputPath || !outputPath) {
            setStatusMessage('Please select both input and output folders')
            return
        }

        setIsScanning(true)
        setStatusMessage('Starting scan...')
        setScanProgress({
            processed: 0,
            total: 0,
            bunniesFound: 0,
            percentage: 0
        })

        try {
            const result = await ipcRenderer.invoke('process-folder', {
                inputPath,
                outputPath,
                sensitivity
            })

            if (result.success) {
                setStatusMessage(`Scan complete! Found ${result.bunniesFound} bunny images`)
            } else {
                setStatusMessage('Error during scan: ' + result.error)
            }
        } catch (error) {
            console.error('Scanning error:', error)
            setStatusMessage('Error during scan')
        } finally {
            setIsScanning(false)
        }
    }

    // Listen for progress updates
    React.useEffect(() => {
        const handleProgress = (event, data) => {
            const percentage = (data.processed / data.total) * 100
            setScanProgress({
                processed: data.processed,
                total: data.total,
                bunniesFound: data.bunniesFound,
                percentage: percentage
            })
        }

        ipcRenderer.on('scan-progress', handleProgress)
        return () => ipcRenderer.removeListener('scan-progress', handleProgress)
    }, [])

    return (
        <div className="container">
            <div className="content">
                <div className="left-column">
                    <div className="header">
                        <div className="small-header">BUNNY PHOTO FINDER</div>
                        <div className="subheader">SEARCH your files for bunny pictures</div>
                        <h1 className="large-title">BUNNIES</h1>
                    </div>
                    
                    <div className="drop-zone"
                        onDrop={handleDrop}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                    >
                        <div className="drop-text">
                            Drop your photos folder here<br />
                            or manually type the<br />
                            address below
                        </div>
                    </div>

                    <div className="folder-input">
                        {inputPath || 'Folder location'}
                    </div>

                    <div className="button-group">
                        <button
                            className="start-button"
                            onClick={handleStartScan}
                            disabled={!inputPath || !outputPath || isScanning}
                        >
                            START
                        </button>

                        <button 
                            className="reset-button"
                            onClick={handleReset}
                            disabled={isScanning}
                        >
                            Reset
                        </button>
                    </div>

                    <div 
                        className="drop-zone"
                        onDrop={handleDestinationDrop}
                        onDragOver={(e) => e.preventDefault()}
                    >
                        <div className="drop-text">
                            Drop your results folder here<br />
                            or manually type the<br />
                            address below
                        </div>
                    </div>

                    <div className="folder-input">
                        {outputPath || 'Results folder'}
                    </div>

                    <div className="settings-section">
    <div className="settings-text">Detection Accuracy</div>
    <select 
        className="settings-dropdown"
        value={sensitivity}
        onChange={(e) => setSensitivity(e.target.value)}
    >
        <option value="high">Strict (90% confidence)</option>
        <option value="medium">Normal (50% confidence)</option>
        <option value="low">Relaxed (30% confidence)</option>
    </select>
</div>

                    <div className="progress-section">
                        {(isScanning || scanProgress.total > 0) && (
                            <div className="progress-stats">
                                <div>Scanned: {scanProgress.processed}/{scanProgress.total}</div>
                                <div>Bunnies: {scanProgress.bunniesFound}</div>
                            </div>
                        )}
                        {isScanning && (
                            <div className="progress-bar">
                                <div 
                                    className="progress-fill"
                                    style={{ width: `${scanProgress.percentage}%` }}
                                />
                            </div>
                        )}
                        {statusMessage && (
                            <div className="status-message">
                                {statusMessage}
                            </div>
                        )}
                    </div>
                </div>

                <div className="right-column">
                    <img 
                        src={bunnyImage} 
                        alt="Bunny placeholder" 
                        className="photo-placeholder"
                    />
                </div>
            </div>
        </div>
    )
}

export default App
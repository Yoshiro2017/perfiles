// ==========================================
// SHOW CONTENT ONLY WHEN JAVASCRIPT IS ACTIVE
// ==========================================
document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('mainContent').style.display = 'block';
});

// ==========================================
// TYPEWRITER STATE
// ==========================================
let paperContent = '';
let lastTypeTime = Date.now();
let typeCount = 0;
let typeStart = null;
let isJammed = false;
const MAX_WPM = 40;

// ==========================================
// MODERN KEYBOARD STATE
// ==========================================
let screenContent = '';
let charCount = 0;
let startTime = null;
let timerInterval = null;

// ==========================================
// ELEMENT REFERENCES
// ==========================================
const paperText = document.getElementById('paperText');
const jamOverlay = document.getElementById('jamOverlay');
const speedWarning = document.getElementById('speedWarning');
const twWpm = document.getElementById('twWpm');

const screenText = document.getElementById('screenText');
const wpmDisplay = document.getElementById('wpm');
const charsDisplay = document.getElementById('chars');
const timeDisplay = document.getElementById('time');

// ==========================================
// CALCULATE WPM
// ==========================================
function calculateWPM(count, startTimeMs) {
  if (!startTimeMs || count === 0) return 0;
  const minutes = (Date.now() - startTimeMs) / 60000;
  return Math.round((count / 5) / minutes); // 5 chars = 1 word standard
}

// ==========================================
// UPDATE DISPLAYS
// ==========================================
function updatePaperDisplay() {
  paperText.textContent = paperContent;
}

function updateScreenDisplay() {
  screenText.textContent = screenContent || 'Start typing... ⌨️';
  charsDisplay.textContent = charCount;
  
  if (startTime && charCount > 0) {
    const wpm = calculateWPM(charCount, startTime);
    wpmDisplay.textContent = wpm;
  }
}

function updateTimeDisplay() {
  if (!startTime) {
    timeDisplay.textContent = '0:00';
    return;
  }
  const elapsed = Math.floor((Date.now() - startTime) / 1000);
  const mins = Math.floor(elapsed / 60);
  const secs = String(elapsed % 60).padStart(2, '0');
  timeDisplay.textContent = `${mins}:${secs}`;
}

// ==========================================
// TYPEWRITER SPEED CHECK — JAM IF TOO FAST!
// ==========================================
function checkTypewriterSpeed() {
  const now = Date.now();
  const timeDiff = now - lastTypeTime;
  
  // Start timing on first keystroke
  if (typeStart === null) typeStart = now;
  
  typeCount++;
  lastTypeTime = now;
  
  const currentWPM = calculateWPM(typeCount, typeStart);
  twWpm.textContent = currentWPM;
  
  // Show warning if getting close
  if (currentWPM > MAX_WPM - 5) {
    speedWarning.style.display = 'block';
  } else {
    speedWarning.style.display = 'none';
  }
  
  // JAM if over limit OR typing too rapidly (keystrokes too close together)
  if (currentWPM > MAX_WPM || timeDiff < 80) {
    jamTypewriter();
  }
}

function jamTypewriter() {
  isJammed = true;
  jamOverlay.classList.add('show');
  if (timerInterval) clearInterval(timerInterval);
}

function resetTypewriter() {
  isJammed = false;
  paperContent = '';
  typeCount = 0;
  typeStart = null;
  jamOverlay.classList.remove('show');
  speedWarning.style.display = 'none';
  twWpm.textContent = '0';
  updatePaperDisplay();
}

// ==========================================
// KEYBOARD INPUT HANDLERS
// ==========================================
function handleKeyPress(keyElement) {
  const char = keyElement.dataset.char;
  const action = keyElement.dataset.action;
  
  // Visual feedback
  keyElement.classList.add('active');
  setTimeout(() => keyElement.classList.remove('active'), 100);
  
  // Skip if jammed
  if (isJammed) return;
  
  // Start timer on first input
  if (!startTime) {
    startTime = Date.now();
    timerInterval = setInterval(updateTimeDisplay, 1000);
  }
  
  // Handle actions vs characters
  if (action) {
    handleAction(action);
  } else if (char) {
    handleCharacter(char);
  }
}

function handleCharacter(char) {
  // Typewriter
  paperContent += char;
  updatePaperDisplay();
  checkTypewriterSpeed();
  
  // Modern keyboard
  screenContent += char;
  charCount++;
  updateScreenDisplay();
}

function handleAction(action) {
  if (action === 'backspace') {
    // Typewriter — backspace works but feels "clunky"
    paperContent = paperContent.slice(0, -1);
    updatePaperDisplay();
    
    // Modern keyboard
    screenContent = screenContent.slice(0, -1);
    charCount = Math.max(0, charCount - 1);
    updateScreenDisplay();
    
  } else if (action === 'enter') {
    // Typewriter — carriage return
    paperContent += '\n';
    updatePaperDisplay();
    checkTypewriterSpeed();
    
    // Modern keyboard
    screenContent += '\n';
    updateScreenDisplay();
  }
}

// ==========================================
// PHYSICAL KEYBOARD SUPPORT
// ==========================================
document.addEventListener('keydown', e => {
  if (isJammed) return;
  
  // Start timer
  if (!startTime) {
    startTime = Date.now();
    timerInterval = setInterval(updateTimeDisplay, 1000);
  }
  
  if (e.key === 'Backspace') {
    e.preventDefault();
    handleAction('backspace');
  }
  else if (e.key === 'Enter') {
    e.preventDefault();
    handleAction('enter');
  }
  else if (e.key.length === 1 && !e.ctrlKey && !e.altKey && !e.metaKey) {
    handleCharacter(e.key);
  }
});

// ==========================================
// SETUP ALL ON-SCREEN KEYS
// ==========================================
document.querySelectorAll('.key').forEach(key => {
  key.addEventListener('mousedown', () => key.classList.add('active'));
  key.addEventListener('mouseup', () => key.classList.remove('active'));
  key.addEventListener('mouseleave', () => key.classList.remove('active'));
  
  key.addEventListener('touchstart', e => {
    e.preventDefault();
    key.classList.add('active');
  });
  key.addEventListener('touchend', () => key.classList.remove('active'));
  
  key.addEventListener('click', () => handleKeyPress(key));
});

// ==========================================
// INITIALIZE
// ==========================================
console.log('⌨️ QWERTY Demo Loaded!');
console.log('🖨️ Typewriter: Max 40 WPM — Go faster and it jams!');
console.log('🖥️ Modern: No speed limit — tracks WPM, characters, and time');

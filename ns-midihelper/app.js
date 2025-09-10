document.addEventListener('DOMContentLoaded', () => {
    const letterInput = document.getElementById('letter-input');
    const numberInput = document.getElementById('number-input');

    const programOutput = document.getElementById('program-value');
    const mspOutput = document.getElementById('msp-value');
    const lspOutput = document.getElementById('lsp-value');
    const variablesSection = document.getElementById('midi-variables');

    const errorMessage = document.getElementById('error-message');

    let jsonData = [];

    fetch('assets/programs.json')
        .then(response => response.json())
        .then(data => { jsonData = data; })
        .catch(err => console.error('Failed to load JSON:', err));

    let currentLetter = '';
    let currentNumber = '';

    function resetNumber() {
        currentNumber = '';
        numberInput.value = '';
        programOutput.value = '';
        mspOutput.value = '';
        lspOutput.value = '';
        variablesSection.classList.remove('active');
    }

    function searchProgram() {
        const programId = `${currentLetter}:${currentNumber}`;
        const match = jsonData.find(item => String(item["Program ID"]) === programId);
        if (match) {
            programOutput.value = match.Program ?? '';
            mspOutput.value = match.MSP ?? '';
            lspOutput.value = match.LSB ?? '';
        } else {
            programOutput.value = 'Not found';
            mspOutput.value = 'Not found';
            lspOutput.value = 'Not found';
        }
        variablesSection.classList.add('active');
    }

    // Valid bank letters A–P
    const validBanks = new Set(['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']);

    // Valid numbers: 11-15, 21-25, 31-35, 41-45, 51-55
    const validNumbers = new Set([
        '11','12','13','14','15',
        '21','22','23','24','25',
        '31','32','33','34','35',
        '41','42','43','44','45',
        '51','52','53','54','55'
    ]);

    document.addEventListener('keydown', (e) => {
        if (e.key.length !== 1) return;

        if (/^[a-zA-Z]$/.test(e.key)) {
            const inputLetter = e.key.toUpperCase();

            if (!validBanks.has(inputLetter)) {
                showError(`Bank ${inputLetter} does not exist. Please try again.`);
                return;
            } else {
                clearError();
            }

            // New letter → reset number and set letter
            currentLetter = inputLetter;
            letterInput.value = currentLetter;
            resetNumber();
        } else if (/^[0-9]$/.test(e.key)) {
            clearError();

            // Handle number input
            if (currentNumber.length >= 2) {
                resetNumber(); // already 2 digits → start fresh
            }

            currentNumber += e.key;
            numberInput.value = currentNumber;

            // Only search if we have 2 digits
            if (currentNumber.length === 2) {
                if (validNumbers.has(currentNumber)) {
                    searchProgram();
                } else {
                    showError(`Program ${currentLetter}${currentNumber} does not exist. Please try again.`);
                    resetNumber(); // clear invalid number
                }
            }
        }
    });
    // Error handling functions
    function showError(msg) {
        errorMessage.textContent = msg;
        errorMessage.classList.add('active');
    }

    function clearError() {
        errorMessage.textContent = '';
        errorMessage.classList.remove('active');
    }

    // Mobile / manual input support
    letterInput.addEventListener('input', () => {
        const val = letterInput.value.trim().toUpperCase();
        if (!val) return;
        if (val !== currentLetter) {
            currentLetter = val;
            resetNumber();
        }
    });

    numberInput.addEventListener('input', () => {
        let val = numberInput.value.replace(/\D/g, '').slice(-2); // max 2 digits
        if (val.length === 2) {
            currentNumber = val;
            searchProgram();
        } else {
            currentNumber = val;
        }
        numberInput.value = currentNumber;
    });

    setTimeout(() => {
        document.body.classList.remove('hidden');
    }, 500);
});
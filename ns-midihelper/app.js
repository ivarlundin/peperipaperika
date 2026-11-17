document.addEventListener('DOMContentLoaded', () => {
    const letterInput = document.getElementById('letter-input');
    const numberInput = document.getElementById('number-input');

    const programOutput = document.getElementById('program-value');
    const mspOutput = document.getElementById('msp-value');
    const lspOutput = document.getElementById('lsp-value');
    const variablesSection = document.getElementById('midi-variables');

    const errorMessage = document.getElementById('error-message');
    const modelButtons = document.querySelectorAll('.stage-model-btn');

    const STORAGE_KEY = 'ns-midihelper-stage-model';

    /**
     * Nord Stage 4 program banks A–H only (512 programs, 8×8 pages per bank).
     * Source: Nord Stage 4 User Manual v1.6X, “Programs” + “Program Change operations”
     * (MSB 0, LSB 0–3, PC 0–127 for Program row). Matches KeyboardBuddy nordStage4.ts.
     */
    const STAGE4_BANK_LETTERS = 'ABCDEFGH';

    /** Nord Stage 3 program banks A–P (see assets/programs.json). */
    const STAGE3_BANK_LETTERS = 'ABCDEFGHIJKLMNOP';

    /** @returns {number|null} program index 0–63 within bank */
    function stage4SlotToProgramInBank(slot) {
        const page = Math.floor(slot / 10);
        const button = slot % 10;
        if (page < 1 || page > 8 || button < 1 || button > 8) return null;
        return (page - 1) * 8 + (button - 1);
    }

    function stage4LocationToMidi(bank, slot) {
        const bankIndex = STAGE4_BANK_LETTERS.indexOf(bank.toUpperCase());
        if (bankIndex < 0) return null;
        const programInBank = stage4SlotToProgramInBank(Number(slot));
        if (programInBank === null) return null;
        // LSB/PC packing ported from KeyboardBuddy; provisional pending hardware test.
        return {
            bankMsb: 0,
            bankLsb: Math.floor(bankIndex / 2),
            program: (bankIndex % 2) * 64 + programInBank,
        };
    }

    let jsonData = [];
    let stageModel = '4';

    fetch('assets/programs.json')
        .then(response => response.json())
        .then(data => { jsonData = data; })
        .catch(err => console.error('Failed to load JSON:', err));

    let currentLetter = '';
    let currentNumber = '';

    const STAGE3_BANKS = new Set(STAGE3_BANK_LETTERS.split(''));
    const STAGE4_BANKS = new Set(STAGE4_BANK_LETTERS.split(''));

    function bankRangeLabel() {
        return stageModel === '4' ? 'A–H' : 'A–P';
    }

    function bankErrorMessage(letter) {
        const bank = letter.toUpperCase();
        if (stageModel === '4') {
            if (STAGE3_BANKS.has(bank) && !STAGE4_BANKS.has(bank)) {
                return (
                    `Bank ${bank} is not on Nord Stage 4 (program banks A–H only). ` +
                    'Switch to Stage 3 for banks I–P.'
                );
            }
            return `Bank ${bank} is not valid for Nord Stage 4 (use ${bankRangeLabel()}).`;
        }
        return `Bank ${bank} is not valid for Nord Stage 3 (use ${bankRangeLabel()}).`;
    }

    function slotErrorMessage(letter, number) {
        const loc = `${letter}${number}`;
        if (stageModel === '4') {
            return (
                `Program ${loc} is not valid for Nord Stage 4 ` +
                '(use panel slots 11–18, 21–28, … 81–88).'
            );
        }
        return (
            `Program ${loc} is not valid for Nord Stage 3 ` +
            '(use panel slots 11–15, 21–25, … 51–55).'
        );
    }

    const STAGE3_NUMBERS = new Set([
        '11','12','13','14','15',
        '21','22','23','24','25',
        '31','32','33','34','35',
        '41','42','43','44','45',
        '51','52','53','54','55'
    ]);

    const STAGE4_NUMBERS = new Set(
        Array.from({ length: 8 }, (_, page) =>
            Array.from({ length: 8 }, (_, button) =>
                String((page + 1) * 10 + (button + 1))
            )
        ).flat()
    );

    function validBanks() {
        return stageModel === '4' ? STAGE4_BANKS : STAGE3_BANKS;
    }

    function validNumbers() {
        return stageModel === '4' ? STAGE4_NUMBERS : STAGE3_NUMBERS;
    }

    function setModelOutputs(msb, lsb, programWire) {
        mspOutput.value = msb;
        lspOutput.value = lsb;
        // Match programs.json convention (1-based Program field for display).
        programOutput.value = programWire + 1;
    }

    function updateModelToggleUi() {
        modelButtons.forEach((btn) => {
            const selected = btn.dataset.model === stageModel;
            btn.classList.toggle('is-selected', selected);
            btn.setAttribute('aria-pressed', selected ? 'true' : 'false');
        });
    }

    function loadModelFromStorage() {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored === '3' || stored === '4') stageModel = stored;
        } catch (_) {
            /* ignore */
        }
        updateModelToggleUi();
    }

    function setStageModel(model) {
        if (model !== '3' && model !== '4') return;
        if (model === stageModel) return;
        stageModel = model;
        try {
            localStorage.setItem(STORAGE_KEY, stageModel);
        } catch (_) {
            /* ignore */
        }
        updateModelToggleUi();
        currentLetter = '';
        currentNumber = '';
        letterInput.value = '';
        resetNumber();
        clearError();
    }

    modelButtons.forEach((btn) => {
        btn.addEventListener('click', () => setStageModel(btn.dataset.model));
    });

    loadModelFromStorage();

    function resetNumber() {
        currentNumber = '';
        numberInput.value = '';
        programOutput.value = '';
        mspOutput.value = '';
        lspOutput.value = '';
        variablesSection.classList.remove('active');
    }

    function searchProgram() {
        if (stageModel === '4') {
            const midi = stage4LocationToMidi(currentLetter, currentNumber);
            if (midi) {
                setModelOutputs(midi.bankMsb, midi.bankLsb, midi.program);
            } else {
                programOutput.value = 'Not found';
                mspOutput.value = 'Not found';
                lspOutput.value = 'Not found';
            }
        } else {
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
        }
        variablesSection.classList.add('active');
    }

    document.addEventListener('keydown', (e) => {
        if (e.key.length !== 1) return;

        if (/^[a-zA-Z]$/.test(e.key)) {
            const inputLetter = e.key.toUpperCase();

            if (!validBanks().has(inputLetter)) {
                showError(bankErrorMessage(inputLetter));
                return;
            } else {
                clearError();
            }

            currentLetter = inputLetter;
            letterInput.value = currentLetter;
            resetNumber();
        } else if (/^[0-9]$/.test(e.key)) {
            clearError();

            if (currentNumber.length >= 2) {
                resetNumber();
            }

            currentNumber += e.key;
            numberInput.value = currentNumber;

            if (currentNumber.length === 2) {
                if (validNumbers().has(currentNumber)) {
                    searchProgram();
                } else {
                    showError(slotErrorMessage(currentLetter, currentNumber));
                    resetNumber();
                }
            }
        }
    });

    function showError(msg) {
        errorMessage.textContent = msg;
        errorMessage.classList.add('active');
    }

    function clearError() {
        errorMessage.textContent = '';
        errorMessage.classList.remove('active');
    }

    letterInput.addEventListener('input', () => {
        const val = letterInput.value.trim().toUpperCase().slice(0, 1);
        letterInput.value = val;
        if (!val) {
            currentLetter = '';
            resetNumber();
            clearError();
            return;
        }
        if (!validBanks().has(val)) {
            showError(bankErrorMessage(val));
            letterInput.value = currentLetter;
            return;
        }
        if (val !== currentLetter) {
            currentLetter = val;
            resetNumber();
            clearError();
        }
    });

    numberInput.addEventListener('input', () => {
        let val = numberInput.value.replace(/\D/g, '').slice(-2);
        if (val.length === 2) {
            currentNumber = val;
            if (validNumbers().has(currentNumber) && validBanks().has(currentLetter)) {
                searchProgram();
            }
        } else {
            currentNumber = val;
        }
        numberInput.value = currentNumber;
    });

    setTimeout(() => {
        document.body.classList.remove('hidden');
    }, 500);
});
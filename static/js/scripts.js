document.addEventListener('DOMContentLoaded', function() {
    var phraseForm = document.getElementById('phrase-form');
    var phraseInput = document.getElementById('phrase-input');
    var submitButton = document.getElementById('submit-btn');
    var messageDiv = document.getElementById('message');

    phraseForm.addEventListener('submit', function(event) {
        event.preventDefault();
        var phrase = phraseInput.value.trim().toLowerCase();

        if (phrase === '') {
            return; // Nie robimy nic, jeśli pole jest puste
        }

        fetch('/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ phrase: phrase })
        })
        .then(function(response) {
            if (response.ok) {
                phraseInput.classList.remove('error');
                messageDiv.textContent = 'Phrase submitted successfully!';
                messageDiv.classList.remove('error-msg');
                messageDiv.classList.add('success-msg');
                phraseInput.value = ''; // Czyszczenie pola po udanym zgłoszeniu
            } else {
                messageDiv.textContent = 'You have already submitted a phrase.';
                messageDiv.classList.remove('success-msg');
                messageDiv.classList.add('error-msg');
                phraseInput.classList.add('error');
            }
        })
        .catch(function(error) {
            console.error('Error:', error);
        });
    });
});

import os

# Define a dictionary of available scripts

scripts = {
    '1': 'overcast.py',  # scanner
    '2': 'cloudburst.py',  # service stopper
    '3': 'coldfront.py',  # delete backups
    '4': 'test.py',  # test samples
    '5': 'deluge.py'  # flood
}

# Display menu options
print('Select a script to execute:')
for key, value in scripts.items():
    print(f'{key}: {value}')

# Get user input
user_input = input('Enter the script number: ')

# Check if the user input is valid
if user_input in scripts:
    # Execute the selected script
    os.system(f'python {scripts[user_input]}')
else:
    print('Invalid input. Please try again.')

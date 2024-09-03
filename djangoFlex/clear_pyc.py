import os

def clear_pyc_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))
                print(f'Removed: {os.path.join(root, file)}')

# Clear .pyc files in the current project directory
clear_pyc_files('.')

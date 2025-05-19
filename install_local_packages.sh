#!/bin/bash
echo "Installing packages in development mode..."
uv pip install -e .

# Check if installation was successful
if [ $? -eq 0 ]; then
    echo "Installation completed successfully!"
else
    echo "Installation failed!"
    exit 1
fi
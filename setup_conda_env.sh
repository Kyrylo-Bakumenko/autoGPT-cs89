#!/bin/bash

# Backup current environment (optional)
conda env export > environment_backup.yml

# Get environment name
read -p "Enter name for the conda environment (default: autoGPT): " env_name
env_name=${env_name:-autoGPT}

# Check if environment exists and remove if needed
if conda env list | grep -q "^$env_name "; then
    read -p "Environment $env_name already exists. Remove it? (y/n): " remove_env
    if [[ $remove_env == "y" ]]; then
        conda env remove --name $env_name
    else
        echo "Aborting setup. Please choose a different environment name."
        exit 1
    fi
fi

# Create fresh environment with Python
conda create -y --name $env_name python=3.10

# Activate the environment
eval "$(conda shell.bash hook)"
conda activate $env_name

# Install packages from requirements.txt
pip install -r requirements.txt

echo "✅ Conda environment '$env_name' has been successfully created and activated."
echo "✅ Required packages have been installed."
echo ""
echo "📝 Usage:"
echo "- To activate: conda activate $env_name"
echo "- To deactivate: conda deactivate"
echo ""
echo "🔑 Remember to set your OpenAI API key in the .env file or as an environment variable:"
echo "export OPENAI_API_KEY='your-api-key-here'"

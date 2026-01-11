# Java Runtime Setup for OpenAPI Generator

## Overview
The OpenAPI Generator requires a Java Runtime Environment (JRE) or Java Development Kit (JDK) to function. This document provides setup instructions for different operating systems.

## Requirements
- Java 8 or higher (Java 17 recommended for optimal performance)
- OpenAPI Generator CLI (already installed via npm)

## Installation Instructions

### Windows
1. Download OpenJDK from https://adoptium.net/
2. Select Windows, choose your architecture (x64 for most systems)
3. Download the JDK installer (not just JRE)
4. Run the installer with default settings
5. Verify installation by opening Command Prompt and running:
   ```cmd
   java -version
   ```

### macOS
```bash
# Using Homebrew (recommended)
brew install openjdk@17

# Set JAVA_HOME (add to ~/.zshrc or ~/.bash_profile)
export JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home
export PATH="$JAVA_HOME/bin:$PATH"
```

### Ubuntu/Debian
```bash
# Update package index
sudo apt update

# Install OpenJDK 17
sudo apt install openjdk-17-jdk

# Verify installation
java -version
```

### CentOS/RHEL/Fedora
```bash
# For CentOS/RHEL
sudo yum install java-17-openjdk-devel

# For Fedora
sudo dnf install java-17-openjdk-devel
```

## Verification
After installation, verify both Java and OpenAPI Generator are working:

```bash
# Check Java version (should show openjdk version)
java -version

# Check OpenAPI Generator CLI
npm list -g @openapitools/openapi-generator-cli

# Test OpenAPI Generator (optional)
openapi-generator-cli version
```

## Environment Variables (Optional)
Some systems may require setting JAVA_HOME:

### Windows
```cmd
set JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-17.0.x.x-hotspot
```

### macOS/Linux
```bash
export JAVA_HOME=/path/to/your/java/installation
```

## Notes for This Project
- The OpenAPI Generator CLI has been installed globally via npm
- SDK generation will be performed in the `sdks/` directory
- Multiple language SDKs will be generated: Python, JavaScript/TypeScript, Java
- The Java runtime is essential for the OpenAPI Generator to function

## Troubleshooting
1. **'java' command not found**: Ensure Java is installed and in your PATH
2. **JAVA_HOME not set**: Some applications require this environment variable
3. **Version conflicts**: Multiple Java versions can cause issues - ensure the correct version is active
4. **Permission errors**: On macOS/Linux, you may need to set executable permissions

## Automated Setup Script (macOS/Linux)
```bash
#!/bin/bash
# Setup script for Java runtime

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*)    MACHINE=Cygwin;;
    MINGW*)     MACHINE=MinGw;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

if [ "$MACHINE" = "Mac" ]; then
    # macOS setup with Homebrew
    if ! command -v brew &> /dev/null; then
        echo "Please install Homebrew first: https://brew.sh/"
        exit 1
    fi

    brew install openjdk@17
    echo 'export JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home' >> ~/.zshrc
    echo 'export PATH="$JAVA_HOME/bin:$PATH"' >> ~/.zshrc
    export JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home
    export PATH="$JAVA_HOME/bin:$PATH"
elif [ "$MACHINE" = "Linux" ]; then
    # Linux setup
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install openjdk-17-jdk -y
    elif command -v yum &> /dev/null; then
        sudo yum install java-17-openjdk-devel -y
    elif command -v dnf &> /dev/null; then
        sudo dnf install java-17-openjdk-devel -y
    else
        echo "Unsupported Linux distribution. Please install Java manually."
        exit 1
    fi
fi

# Verify installation
echo "Java version:"
java -version

echo "OpenAPI Generator CLI:"
npm list -g @openapitools/openapi-generator-cli
```
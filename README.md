# Flask Application

This project is a Flask web application that integrates with CAS for authentication and Redis for session management and data storage. It also uses WebSocket for real-time updates.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Build](#build)
- [Features](#features)
- [Contributing](#contributing)
- [License](#license)

## Installation

1. Clone the repository:

```sh
git clone https://github.com/dan-zong-hao/dcz-backend.git
cd repository
```

2. Create and activate a Conda environment using the environment.yml file:

```sh
conda env create -f environment.yml
conda activate myenv
```

3. Configure your environment variables. Replace the placeholders in the code (e.g., app_login_url, cas_url, Redis configuration) with your actual configuration.

## Usage

1. Start your [dcz-frontend](https://github.com/dan-zong-hao/dcz-frontend.git)

2. Start the dcz-backend

```sh
python app.py
```

# AdVocate: AI-Powered Ad Generator

AdVocate is an AI-powered platform that automates the creation of marketing research and advertisements. It uses specialized AI agents to streamline market analysis, strategy development, and content generation.

## Key Features

-   **Automated Market Research:** Conducts in-depth market research and generates insightful reports.
-   **AI-Driven Marketing Strategies:** Develops comprehensive marketing strategies tailored to your brand.
-   **Ad Content Generation:** Automatically creates engaging ad content and image prompts.

## Core Components

-   **Research Agent:** Automates market research, analyzes data, and generates reports.
-   **Marketing Agent:** Analyzes brand voice, creates audience profiles, and develops marketing strategies.
-   **Ad Generator:** Creates ad content, generates image prompts, and processes campaigns.

## Setup Instructions

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/JNK234/AdVocate---AI-Ad-Generator.git
    cd AdVocate---AI-Ad-Generator
    ```

2.  **Configure the environment:**

    ```bash
    cp .env.template .env
    ```

    Edit the `.env` file with your Azure OpenAI API credentials and other necessary configurations.

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**

    ```bash
    streamlit run app.py
    ```

## Requirements

-   Python 3.8+
-   Azure OpenAI API access
-   Streamlit
-   LangChain

## Project Structure

```
├── ad_generation_app.py     # Main application file
├── app.py                    # Streamlit web interface
├── campaign_generator.py     # Campaign generation logic
├── campaign_results.json     # Stores campaign results
├── enhanced_app.py           # Enhanced application features
├── main.py                   # Main execution script
├── models/                   # AI models and data storage
│   └── vectorstore/          # Vector storage configurations
├── notebooks/                # Jupyter notebooks for experimentation
├── Outputs/                  # Campaign output directory
├── README.md                 # This file
├── requirements.txt          # Project dependencies
├── run_campaign_flow.py      # Campaign execution flow
└── src/                      # Source code directory
    ├── agents/               # AI agent implementations
    ├── config/               # Configuration settings
    └── core/                 # Core functionalities
```

import requests
from bs4 import BeautifulSoup
from transformers import pipeline
from jinja2 import Template
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Step 1: Web Scraping
def scrape_website(url):
    """Scrape text content from the provided company website URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an error for HTTP issues
        soup = BeautifulSoup(response.text, 'html.parser')
        # Filter relevant content (headings and paragraphs)
        content = soup.find_all(['h1', 'h2', 'p'])
        return " ".join([item.text.strip() for item in content if item.text.strip()])
    except requests.RequestException as e:
        logging.error(f"Error fetching website content: {e}")
        return ""

# Step 2: Content Summarization
def summarize_content(content, summarizer, max_length=100, min_length=30):
    """Summarize the extracted website content using an NLP pipeline."""
    try:
        # Chunk content to prevent token overflow
        chunks = [content[i:i + 512] for i in range(0, len(content), 512)]
        summaries = [summarizer(chunk, max_length=max_length, min_length=min_length, truncation=True)[0]['summary_text'] for chunk in chunks]
        return summaries
    except Exception as e:
        logging.error(f"Error during summarization: {e}")
        return ["Summarization failed."]

# Step 3: Generate Summary
def generate_summary(template_path, company_overview, key_services, recent_updates):
    """Generate a structured summary using a Jinja2 template."""
    if not os.path.exists(template_path):
        logging.warning("Template file not found. Using default template.")
        template_content = """
        ## Company Overview
        {{ company_overview }}

        ## Key Services
        {{ key_services }}

        ## Recent Updates
        {{ recent_updates }}
        """
        template = Template(template_content)
    else:
        with open(template_path, 'r') as file:
            template = Template(file.read())
    
    return template.render(
        company_overview=company_overview,
        key_services=key_services,
        recent_updates=recent_updates
    )

# Main Execution
if __name__ == "__main__":
    url = "https://example.com"  # Replace with an actual company URL
    template_path = "template.txt"  # Path to the Jinja2 template file

    # Initialize the summarizer once
    logging.info("Initializing summarization model...")
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

    try:
        # Step 1: Scrape Website
        logging.info("Scraping website...")
        content = scrape_website(url)
        if not content:
            raise ValueError("No content extracted from the website.")

        # Step 2: Summarize Content
        logging.info("Summarizing content...")
        summaries = summarize_content(content, summarizer)

        # Step 3: Generate Output
        logging.info("Generating summary...")
        company_summary = generate_summary(
            template_path,
            company_overview=summaries[0] if len(summaries) > 0 else "N/A",
            key_services=summaries[1] if len(summaries) > 1 else "N/A",
            recent_updates=summaries[2] if len(summaries) > 2 else "N/A"
        )

        # Save the output to a file
        output_path = "output_summary.txt"
        with open(output_path, "w") as output_file:
            output_file.write(company_summary)

        logging.info(f"Workflow complete! Summary saved to {output_path}")
    except Exception as e:
        logging.error(f"Error during execution: {e}")

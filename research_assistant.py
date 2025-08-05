import os
import requests
import re
import xml.etree.ElementTree as ET
import openai
from dotenv import load_dotenv

# --- NEW: Load environment variables from .env file ---
load_dotenv()

# Check if the API key is loaded
if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY not found. Make sure it's set in your .env file.")
    exit()

# --- The rest of the code is the same ---

def summarize_with_openai(abstract):
    """
    Summarizes the given abstract using the OpenAI Chat API.
    """
    print("   -> Sending abstract to AI for summarization...")
    try:
        # The client automatically uses the key loaded into the environment
        client = openai.OpenAI() 
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a highly skilled research assistant. Your task is to summarize academic abstracts into a structured format."
                },
                {
                    "role": "user",
                    "content": f"""Please summarize the following abstract. Present the output in markdown with these exact headings:

- **Key Problem:**
- **Methodology:**
- **Key Findings:**
- **Conclusion:**

Abstract:
{abstract}
"""
                }
            ]
        )
        summary = response.choices[0].message.content
        return summary.strip()

    except Exception as e:
        print(f"   -> Error during summarization: {e}")
        return "Error: Could not generate summary."


def sanitize_filename(name):
    """Removes characters that are invalid for filenames."""
    return re.sub(r'[\\/*?:"<>|]', "", name)

def run_research_assistant(topic, max_papers=5):
    """
    Main function to run the personal research assistant.
    """
    print(f"\nStarting research for topic: '{topic}'")

    base_url = 'http://export.arxiv.org/api/query?'
    search_query = f'search_query=all:{topic.replace(" ", "+")}&start=0&max_results={max_papers}'
    
    try:
        response = requests.get(base_url + search_query)
        response.raise_for_status()
        print("Successfully connected to ArXiv API.")
        
        folder_name = sanitize_filename(topic)
        os.makedirs(folder_name, exist_ok=True)
        print(f"Created/found folder: '{folder_name}'")

        root = ET.fromstring(response.content)
        atom_namespace = '{http://www.w3.org/2005/Atom}'
        
        entries = root.findall(f'{atom_namespace}entry')
        if not entries:
            print("\nNo papers found for this topic on ArXiv.")
            return

        for entry in entries:
            title = entry.find(f'{atom_namespace}title').text.strip().replace('\n', ' ')
            abstract = entry.find(f'{atom_namespace}summary').text.strip().replace('\n', ' ')
            
            print(f"Processing: {title[:60]}...")
            
            ai_summary = summarize_with_openai(abstract)
            
            file_name = f"{sanitize_filename(title)}.md"
            file_path = os.path.join(folder_name, file_name)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n")
                f.write(f"## AI-Generated Summary\n\n")
                f.write(ai_summary)
            
            print(f"   -> Saved summary to '{file_path}'")

    except Exception as e:
        print(f"An error occurred: {e}")
        return
    
    print("\nResearch complete! Your AI-powered summaries are ready.")


if __name__ == "__main__":
    print("Welcome to the Personal Research Assistant!")
    topic_input = input("Please enter the research topic you want to search for: ")

    if topic_input.strip():
        run_research_assistant(topic_input)
    else:
        print("No topic entered. Exiting program.")
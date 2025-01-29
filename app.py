import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai
import pandas as pd
import csv
import io

# OpenAI API Key (Ensure you have set it in Streamlit Secrets or an .env file)
openai.api_key = st.secrets["openai_api_key"] if "openai_api_key" in st.secrets else "your-openai-key-here"

# Function to extract key elements from a webpage
def extract_content(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        meta_title = soup.find('title').text if soup.find('title') else ''
        meta_description = (
            soup.find('meta', attrs={'name': 'description'})['content']
            if soup.find('meta', attrs={'name': 'description'}) else ''
        )
        headers = [h.text.strip() for h in soup.find_all(['h1', 'h2', 'h3'])]
        text_content = " ".join([p.text.strip() for p in soup.find_all('p')])

        return {
            "url": url,
            "meta_title": meta_title,
            "meta_description": meta_description,
            "headers": headers,
            "text": text_content
        }
    except Exception as e:
        return {"url": url, "error": str(e)}

# Function to generate structured content recommendations
def generate_content_outline(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert in content marketing and SEO."},
            {"role": "user", "content": f"Analyze the provided text and recommend a well-structured content outline, including:\n"
                                        "- Title\n"
                                        "- SEO-optimized Meta Title & Description\n"
                                        "- Key Headings (H1, H2, H3) based on competitive analysis\n"
                                        "- Suggested sections\n"
                                        "- Recommended content length\n"
                                        "- Important keywords to target\n"
                                        "Here is the extracted competitor content:\n\n{text}"}
        ]
    )
    return response['choices'][0]['message']['content']

# Streamlit UI
st.title("Competitor Content Analysis & Structured Outline Generator")

st.write("Analyze competitor URLs and generate structured content recommendations.")

# Input for competitor URLs
urls = st.text_area("Paste Competitor URLs (one per line)", height=150).splitlines()

if st.button("Analyze"):
    results = []
    
    with st.spinner("Analyzing competitor websites..."):
        for url in urls:
            extracted_data = extract_content(url)
            if "error" in extracted_data:
                st.error(f"Failed to analyze {url}: {extracted_data['error']}")
                continue
            
            structured_outline = generate_content_outline(extracted_data["text"])
            extracted_data["structured_outline"] = structured_outline
            results.append(extracted_data)

    if results:
        st.success("Analysis complete! See results below.")
        
        for result in results:
            st.subheader(f"Analysis for {result['url']}")
            st.write(f"**Meta Title:** {result['meta_title']}")
            st.write(f"**Meta Description:** {result['meta_description']}")
            st.write(f"**Extracted Headings:** {', '.join(result['headers'])}")
            st.write("### Recommended Content Outline:")
            st.write(result["structured_outline"])

        # Export to CSV
        if st.button("Export Content Outline as CSV"):
            output = io.StringIO()
            csv_writer = csv.writer(output)
            csv_writer.writerow(["URL", "Meta Title", "Meta Description", "Headers", "Structured Content Outline"])
            
            for result in results:
                csv_writer.writerow([
                    result["url"],
                    result["meta_title"],
                    result["meta_description"],
                    ", ".join(result["headers"]),
                    result["structured_outline"]
                ])
            
            output.seek(0)
            st.download_button("Download CSV", output.getvalue(), "competitor_analysis.csv", "text/csv")

        # Export to TXT
        if st.button("Export Content Outline as TXT"):
            output_txt = io.StringIO()
            for result in results:
                output_txt.write(f"### {result['url']}\n")
                output_txt.write(f"Meta Title: {result['meta_title']}\n")
                output_txt.write(f"Meta Description: {result['meta_description']}\n")
                output_txt.write(f"Extracted Headings: {', '.join(result['headers'])}\n")
                output_txt.write("### Structured Content Outline:\n")
                output_txt.write(f"{result['structured_outline']}\n\n")
            
            output_txt.seek(0)
            st.download_button("Download TXT", output_txt.getvalue(), "content_outline.txt", "text/plain")

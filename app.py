import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai
import pandas as pd
import csv
import io

# Ensure OpenAI API Key is accessible
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
else:
    st.error("❌ OpenAI API Key is missing in Streamlit Secrets! Please add it.")
    st.stop()

# Check if OpenAI API Key is valid
@st.cache_data
def verify_openai_key():
    try:
        openai.Engine.list()
        return True
    except openai.error.AuthenticationError:
        return False

if not verify_openai_key():
    st.error("❌ Invalid or expired OpenAI API Key! Please check your Streamlit Secrets.")
    st.stop()

# Function to extract key elements from a webpage (caching enabled)
@st.cache_data
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

# Function to batch process OpenAI API calls for faster analysis
def generate_bulk_content_outlines(text_list):
    messages = [
        {"role": "system", "content": "You are an expert in content marketing and SEO."},
    ]
    for text in text_list:
        messages.append(
            {"role": "user", "content": f"Analyze the following competitor content and generate a structured content outline:\n{text}"}
        )

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return [choice["message"]["content"] for choice in response['choices']]

# Streamlit UI
st.title("Competitor Content Analysis & Structured Outline Generator")

st.write("Analyze competitor URLs and generate structured content recommendations.")

# Input for competitor URLs
urls = st.text_area("Paste Competitor URLs (one per line)", height=150).splitlines()

if st.button("Analyze"):
    results = []
    
    with st.spinner("Analyzing competitor websites..."):
        extracted_texts = []
        url_data = []

        for url in urls:
            extracted_data = extract_content(url)
            if "error" in extracted_data:
                st.error(f"Failed to analyze {url}: {extracted_data['error']}")
                continue
            
            extracted_texts.append(extracted_data["text"])
            url_data.append(extracted_data)

        # Send all extracted texts to OpenAI in a single batch request
        structured_outlines = generate_bulk_content_outlines(extracted_texts)
        
        for idx, structured_outline in enumerate(structured_outlines):
            url_data[idx]["structured_outline"] = structured_outline
            results.append(url_data[idx])

    if results:
        st.success("Analysis complete! See results below.")
        
        for result in results:
            with st.expander(f"🔍 Analysis for {result['url']}"):
                st.write(f"**Meta Title:** {result['meta_title']}")
                st.write(f"**Meta Description:** {result['meta_description']}")
                st.write(f"**Extracted Headings:** {', '.join(result['headers'])}")
                st.write("### 📌 Recommended Content Outline:")
                st.write(result["structured_outline"])

        # Export to CSV
        if st.button("📥 Export Content Outline as CSV"):
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
        if st.button("📥 Export Content Outline as TXT"):
            output_txt = io.StringIO()
            for result in results:
                output_txt.write(f"### {result['url']}\n")
                output_txt.write(f"Meta Title: {result['meta_title']}\n")
                output_txt.write(f"Meta Description: {result['meta_description']}\n")
                output_txt.write(f"Extracted Headings: {', '.join(result['headers'])}\n")
                output_txt.write("### 📌 Structured Content Outline:\n")
                output_txt.write(f"{result['structured_outline']}\n\n")
            
            output_txt.seek(0)
            st.download_button("Download TXT", output_txt.getvalue(), "content_outline.txt", "text/plain")

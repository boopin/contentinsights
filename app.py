import streamlit as st
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords
from collections import Counter
import pandas as pd
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Program details
PROGRAM_NAME = "ContentInsightX"
TAGLINE = "Unlock Competitor Insights with AI-Powered Content Analysis"
VERSION = "v1.0.0"

# Set page title and icon for the browser tab
st.set_page_config(
    page_title=PROGRAM_NAME,
    page_icon="🔍",  # You can use an emoji or a URL to an icon
    layout="wide"
)

# Download NLTK data
nltk.download('punkt')
nltk.download('stopwords')

# Function to generate insights using OpenAI API
def generate_insights(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that analyzes text and generates insights."},
            {"role": "user", "content": f"Analyze this text and generate a structured content outline:\n\n{text}"}
        ]
    )
    return response['choices'][0]['message']['content']

# Streamlit app
st.title(f"{PROGRAM_NAME} {VERSION}")
st.markdown(f"**{TAGLINE}**")
st.write("---")

# Input URLs
st.write("### Enter Competitor URLs")
urls = st.text_area("Paste URLs (one per line)", height=100).splitlines()

if st.button("Analyze"):
    results = []
    for url in urls:
        try:
            # Fetch HTML
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract meta tags and headers
            meta_title = soup.find('title').text if soup.find('title') else ''
            meta_description = soup.find('meta', attrs={'name': 'description'})['content'] if soup.find('meta', attrs={'name': 'description'}) else ''
            headers = [h.text for h in soup.find_all(['h1', 'h2', 'h3'])]

            # Extract text content
            text = ' '.join([p.text for p in soup.find_all('p')])

            # Tokenize and clean text
            words = nltk.word_tokenize(text)
            words = [word.lower() for word in words if word.isalnum() and word.lower() not in stopwords.words('english')]
            word_freq = Counter(words)

            # Save results
            results.append({
                'url': url,
                'meta_title': meta_title,
                'meta_description': meta_description,
                'headers': headers,
                'word_freq': word_freq,
                'text': text
            })
        except Exception as e:
            st.error(f"Error analyzing {url}: {e}")

    # Display insights
    st.write("## Insights")
    for result in results:
        st.write(f"### {result['url']}")
        st.write(f"**Meta Title:** {result['meta_title']}")
        st.write(f"**Meta Description:** {result['meta_description']}")
        st.write(f"**Headers:** {', '.join(result['headers'])}")
        st.write(f"**Top 10 Words:** {result['word_freq'].most_common(10)}")

    # Visualize word frequencies
    st.write("## Word Frequency Visualization")
    all_words = []
    for result in results:
        all_words.extend(result['word_freq'].elements())
    overall_word_freq = Counter(all_words)
    top_words = pd.DataFrame(overall_word_freq.most_common(10), columns=['Word', 'Frequency'])
    st.bar_chart(top_words.set_index('Word'))

    # Generate structured outline using OpenAI API
    st.write("## Structured Content Outline")
    for result in results:
        insights = generate_insights(result['text'])
        st.write(f"### Outline for {result['url']}")
        st.write(insights)

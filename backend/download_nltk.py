import nltk
import textblob.download_corpora
import sys
import os

# Get the directory where this script is located (the project root)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Define the download directory as a folder named 'nltk_data' in the root
DOWNLOAD_DIR = os.path.join(BASE_DIR, 'nltk_data')

# Create the directory if it doesn't exist
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

print(f"--- NLTK data will be downloaded to: {DOWNLOAD_DIR} ---")
nltk.data.path.append(DOWNLOAD_DIR)

# --- Download TextBlob ---
print("--- Starting TextBlob Downloader ---")
try:
    textblob.download_corpora.main()
    print("--- TextBlob Download Complete ---")
except Exception as e:
    print(f"!!! ERROR downloading TextBlob: {e}")

# --- Download NLTK Packages ---
print("--- Starting NLTK Downloader ---")
nltk_packages = [
    'punkt_tab',
    'stopwords',
    'punkt',
    'averaged_perceptron_tagger',
    'wordnet',
    'omw-1.4'
]

for pkg in nltk_packages:
    try:
        print(f"Downloading NLTK package: {pkg}...")
        nltk.download(pkg, download_dir=DOWNLOAD_DIR)
        print(f"Successfully downloaded {pkg}")
    except Exception as e:
        print(f"!!! ERROR downloading {pkg}: {e}")
        if pkg == 'punkt_tab':
             print("!!! CRITICAL FAILURE: Could not download punkt_tab.")
             pass

print("--- All downloads complete ---")
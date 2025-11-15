import nltk
import textblob.download_corpora
import sys
import os

# Set the download directory explicitly to the one Render uses
download_dir = '/opt/render/nltk_data'
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# Add this path to NLTK's search list
nltk.data.path.append(download_dir)

print(f"--- Setting NLTK data path to: {download_dir} ---")

# Download TextBlob
print("--- Starting TextBlob Downloader ---")
try:
    textblob.download_corpora.main()
    print("--- TextBlob Download Complete ---")
except Exception as e:
    print(f"!!! ERROR downloading TextBlob: {e}")

# Download NLTK packages
print("--- Starting NLTK Downloader ---")
nltk_packages = [
    'punkt_tab',  # The one that is failing
    'stopwords',
    'punkt',
    'averaged_perceptron_tagger',
    'wordnet',
    'omw-1.4'
]

for pkg in nltk_packages:
    try:
        print(f"Downloading NLTK package: {pkg}...")
        # Download to the specific directory
        nltk.download(pkg, download_dir=download_dir)
        print(f"Successfully downloaded {pkg} to {download_dir}")
    except Exception as e:
        print(f"!!! ERROR downloading {pkg}: {e}")
        if pkg == 'punkt_tab':
             print("!!! CRITICAL FAILURE: Could not download punkt_tab.")
             pass

print("--- NLTK Download Complete ---")
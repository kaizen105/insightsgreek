import nltk
import textblob.download_corpora
import sys

# Download TextBlob
print("--- Starting TextBlob Downloader ---")
textblob.download_corpora.main()
print("--- TextBlob Download Complete ---")


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
        nltk.download(pkg)
        print(f"Successfully downloaded {pkg}")
    except Exception as e:
        print(f"!!! ERROR downloading {pkg}: {e}")
        # We can optionally exit if a critical package fails
        if pkg == 'punkt_tab':
             sys.exit(f"Failed to download critical package: {pkg}")

print("--- NLTK Download Complete ---")
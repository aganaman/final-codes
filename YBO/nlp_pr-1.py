import spacy
import pandas as pd
from collections import Counter
from multiprocessing import Pool

# Load spaCy model and set up stop words
nlp = spacy.load("en_core_web_sm")
stop_words = nlp.Defaults.stop_words

# Load Excel files into pandas dataframes
df_testcases = pd.read_excel("C:/Users/namanaga/Downloads/rpl-s nlp test 6/All_TCs.xlsx")
df_changes = pd.read_csv("C:/Users/namanaga/Downloads/rpl-s nlp test 6/change_wise_recommendation.csv")

print(df_testcases)
print(df_changes)

# Define function to preprocess text
def preprocess(text):
    print("Preprocess function called--",text)
    # Remove leading/trailing white space
    text = text.strip()

    # Convert to lowercase
    text = text.lower()

    # Replace newlines with spaces
    text = text.replace("\n", " ")

    # Remove punctuation and stop words
    doc = nlp(text)
    tokens = [token.lemma_ for token in doc if not token.is_punct and token.lemma_ not in stop_words]

    # Remove digits and words with fewer than 3 characters
    #tokens = [token for token in tokens if not token.isdigit() and len(token) >= 3]

    # Count the frequency of each token
    token_counts = Counter(tokens)

    # Return the most common tokens as a space-separated string
    return " ".join([token for token, count in token_counts.most_common(5)])

import math

# Define batch size
batch_size = 100
titles=[]
# Get number of batches needed
num_batches = math.ceil(len(df_testcases) / batch_size)

# Preprocess test case titles using multiprocessing
with Pool(5) as pool:
    for i in range(num_batches):
        # Get titles for current batch
        start_idx = i * batch_size
        end_idx = min(start_idx + batch_size, len(df_testcases))
        try:
            testcase_titles = df_testcases["title"][start_idx:end_idx].tolist()
            print("------------------batch num {0}----------------------------------".format(i))
            print(testcase_titles)

            # Process titles in current batch
            testcase_titles = pool.map(preprocess, testcase_titles)
            for result in pool.map(preprocess, testcase_titles):
                titles.append(result)
            
            # Print results for current batch
            print(f"Processed batch {i+1}/{num_batches}")
            print("--------------------------testcase_titles--------------------------")
            print(titles)
        
        except Exception as e:
            print(f"Error occurred: {e}")
            testcase_titles = df_testcases["title"][start_idx:end_idx].tolist()
    pool.close()
    pool.join()

# Preprocess change descriptions
change_descriptions = df_changes["Change Details"].apply(preprocess)
print("--------------change_descriptions----------------")
print(change_descriptions)

# Define threshold similarity score
threshold = 0.8

# Create a new column in the changes dataframe to store the similarity score
df_changes["similarity_score"] = 0

# Use spaCy's nlp.pipe method to process all preprocessed test case titles at once
testcase_docs = list(nlp.pipe(testcase_titles))

# Define function to calculate similarity score using spaCy
def calculate_similarity(change):
    doc2 = nlp(change)
    similarity_scores = [doc1.similarity(doc2) for doc1 in testcase_docs]
    max_similarity = max(similarity_scores)
    matching_title = df_testcases.loc[similarity_scores.index(max_similarity), "title"]
    return max_similarity, matching_title

# Calculate similarity scores for each change using multiprocessing
with Pool() as pool:
    similarity_scores = pool.map(calculate_similarity, change_descriptions)

# Loop through each similarity score and print matching test cases if above threshold
recommendations = []
for i, (max_similarity, matching_title) in enumerate(similarity_scores):
    if max_similarity > threshold:
        matching_id = df_testcases[df_testcases["title"]==matching_title]["id"].values[0]
        print(f"Matching test case for change {i}: {matching_title} (ID: {matching_id}, similarity score: {max_similarity})")
        recommendations.append(df_testcases[df_testcases["title"]==matching_title]["id"].values[0])

print(set(recommendations))
